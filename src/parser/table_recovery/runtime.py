"""Localized OCR runtime for table fallback without in-process OCR imports."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, Sequence

from .detection import (
    FallbackStatus,
    SourceAnchor,
    TableFallbackCandidate,
    TableFailureDetector,
    block_bbox,
)
from .models import BoundingBox, TableRecoverySpec, load_ocr_tokens
from .spatial_reconstructor import SpatialTableReconstructor


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


@dataclass(frozen=True)
class LocalizedTableRegion:
    page: int
    pdf_bbox: BoundingBox
    table_pdf_bbox: BoundingBox
    source_anchors: tuple[SourceAnchor, ...]
    confidence: float
    localization_method: str
    reason: str


class TableRegionLocator:
    """Map normalized MinerU evidence to bounded PDF-space crops."""

    def __init__(self, *, margin_ratio: float = 0.02) -> None:
        self.margin_ratio = margin_ratio

    @staticmethod
    def _to_pdf(box: BoundingBox, width: float, height: float) -> BoundingBox:
        return BoundingBox(box.x0 * width, box.y0 * height, box.x1 * width, box.y1 * height)

    @staticmethod
    def _clamp(box: BoundingBox, width: float, height: float) -> BoundingBox:
        return BoundingBox(
            max(0.0, min(width, box.x0)),
            max(0.0, min(height, box.y0)),
            max(0.0, min(width, box.x1)),
            max(0.0, min(height, box.y1)),
        )

    def locate(
        self,
        candidate: TableFallbackCandidate,
        *,
        page_width: float,
        page_height: float,
        page_blocks: Sequence[dict[str, Any]] = (),
    ) -> LocalizedTableRegion:
        anchors = tuple(
            item for item in (candidate.anchor, candidate.title, candidate.suspected_image)
            if item is not None
        )
        margin_x = page_width * self.margin_ratio
        margin_y = page_height * self.margin_ratio
        if candidate.suspected_image is not None:
            image_pdf = self._to_pdf(candidate.suspected_image.bbox, page_width, page_height)
            evidence_pdf = [self._to_pdf(item.bbox, page_width, page_height) for item in anchors]
            union = BoundingBox.union(evidence_pdf)
            assert union is not None
            crop = BoundingBox(
                union.x0 - margin_x,
                union.y0 - margin_y,
                union.x1 + margin_x,
                union.y1 + margin_y,
            )
            method = "nearby_uncaptioned_image_union"
            table_box = image_pdf
        else:
            anchor = candidate.anchor.bbox
            title = candidate.title.bbox if candidate.title else anchor
            center_x = (anchor.center_x + title.center_x) / 2
            if center_x < 0.42:
                x0, x1 = 0.04, 0.51
                column_method = "left_column"
            elif center_x > 0.58:
                x0, x1 = 0.49, 0.96
                column_method = "right_column"
            else:
                x0, x1 = 0.04, 0.96
                column_method = "full_width"
            table_top = title.y1 + 0.006
            boundary = self._next_structural_boundary(
                page_blocks, table_top=table_top, x0=x0, x1=x1
            )
            table_bottom = boundary if boundary is not None else min(0.98, table_top + 0.36)
            if table_bottom - table_top < 0.12:
                table_bottom = min(0.98, table_top + 0.22)
            table_box = self._to_pdf(
                BoundingBox(x0, table_top, x1, table_bottom), page_width, page_height
            )
            anchor_pdf = self._to_pdf(anchor, page_width, page_height)
            crop = BoundingBox(
                table_box.x0 - margin_x,
                min(anchor_pdf.y0, table_box.y0) - margin_y,
                table_box.x1 + margin_x,
                table_box.y1 + margin_y,
            )
            method = f"conservative_{column_method}"
        crop = self._clamp(crop, page_width, page_height)
        table_box = self._clamp(table_box, page_width, page_height)
        return LocalizedTableRegion(
            page=candidate.page,
            pdf_bbox=crop,
            table_pdf_bbox=table_box,
            source_anchors=anchors,
            confidence=candidate.confidence,
            localization_method=method,
            reason=candidate.reason.value,
        )

    @staticmethod
    def _next_structural_boundary(
        blocks: Sequence[dict[str, Any]], *, table_top: float, x0: float, x1: float
    ) -> float | None:
        boundaries: list[float] = []
        for block in blocks:
            if block.get("type") not in {"paragraph_title", "doc_title"}:
                continue
            bbox = block_bbox(block)
            if bbox is None or bbox.y0 <= table_top + 0.08:
                continue
            if x0 <= bbox.center_x <= x1:
                boundaries.append(bbox.y0 - 0.01)
        return min(boundaries) if boundaries else None


@dataclass(frozen=True)
class CoordinateTransform:
    crop_pdf_bbox: BoundingBox
    scale_x: float
    scale_y: float
    pixel_width: int
    pixel_height: int

    def pixel_to_pdf(self, box: BoundingBox) -> BoundingBox:
        return BoundingBox(
            self.crop_pdf_bbox.x0 + box.x0 / self.scale_x,
            self.crop_pdf_bbox.y0 + box.y0 / self.scale_y,
            self.crop_pdf_bbox.x0 + box.x1 / self.scale_x,
            self.crop_pdf_bbox.y0 + box.y1 / self.scale_y,
        )

    def pdf_to_pixel(self, box: BoundingBox) -> BoundingBox:
        return BoundingBox(
            (box.x0 - self.crop_pdf_bbox.x0) * self.scale_x,
            (box.y0 - self.crop_pdf_bbox.y0) * self.scale_y,
            (box.x1 - self.crop_pdf_bbox.x0) * self.scale_x,
            (box.y1 - self.crop_pdf_bbox.y0) * self.scale_y,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "crop_pdf_bbox": self.crop_pdf_bbox.to_list(),
            "scale_x": self.scale_x,
            "scale_y": self.scale_y,
            "pixel_width": self.pixel_width,
            "pixel_height": self.pixel_height,
        }


@dataclass(frozen=True)
class RenderedCrop:
    image_path: Path
    page: int
    dpi: int
    transform: CoordinateTransform
    sha256: str


class PyMuPDFCropRenderer:
    def __init__(self, *, dpi: int = 288) -> None:
        self.dpi = int(dpi)

    def render(self, pdf_path: Path, region: LocalizedTableRegion, output_path: Path) -> RenderedCrop:
        import pymupdf

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(pdf_path) as document:
            page = document[region.page - 1]
            clip = pymupdf.Rect(*region.pdf_bbox.to_list())
            requested_scale = self.dpi / 72.0
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(requested_scale, requested_scale),
                clip=clip,
                alpha=False,
            )
            pixmap.save(output_path)
        transform = CoordinateTransform(
            crop_pdf_bbox=region.pdf_bbox,
            scale_x=pixmap.width / region.pdf_bbox.width,
            scale_y=pixmap.height / region.pdf_bbox.height,
            pixel_width=pixmap.width,
            pixel_height=pixmap.height,
        )
        return RenderedCrop(
            image_path=output_path,
            page=region.page,
            dpi=self.dpi,
            transform=transform,
            sha256=sha256_file(output_path),
        )


@dataclass(frozen=True)
class OCRProviderResult:
    status: FallbackStatus
    raw_artifact: Path | None
    backend_metadata: dict[str, Any]
    command_metadata: dict[str, Any]
    exit_code: int | None = None
    stderr_summary: str | None = None
    elapsed_seconds: float | None = None
    log_path: Path | None = None


class TableOCRProvider(Protocol):
    @property
    def cache_identity(self) -> dict[str, Any]: ...

    def run(self, crop: RenderedCrop, output_path: Path) -> OCRProviderResult: ...


class PaddleOCRCLIProvider:
    """Invoke ordinary PaddleOCR in an external Python environment."""

    def __init__(
        self,
        *,
        executable: str | Path | None = None,
        worker_script: str | Path | None = None,
        device: str = "gpu:0",
        language: str = "en",
        timeout_seconds: int = 300,
    ) -> None:
        configured = executable or os.environ.get("TABLE_OCR_EXECUTABLE")
        self.configured_executable = Path(configured) if configured else None
        self.executable = self._resolve_executable(self.configured_executable)
        self.worker_script = Path(worker_script) if worker_script else (
            Path(__file__).resolve().parents[3] / "scripts" / "paddleocr_table_worker.py"
        )
        self.device = device
        self.language = language
        self.timeout_seconds = int(timeout_seconds)

    @staticmethod
    def _resolve_executable(path: Path | None) -> Path | None:
        if path is None:
            return None
        if path.name.casefold() in {"paddleocr.exe", "paddleocr"}:
            python = path.with_name("python.exe" if os.name == "nt" else "python")
            if python.is_file():
                return python
        return path

    @property
    def cache_identity(self) -> dict[str, Any]:
        return {
            "backend": "ordinary_paddleocr_external",
            "provider_version": "1",
            "language": self.language,
            "device": self.device,
            "orientation_classification": False,
            "document_unwarping": False,
            "textline_orientation": False,
        }

    def build_command(self, image_path: Path, output_path: Path) -> list[str]:
        executable = self.executable or self.configured_executable or Path("python")
        return [
            str(executable), str(self.worker_script),
            "--input", str(image_path), "--output", str(output_path),
            "--device", self.device, "--language", self.language,
        ]

    def run(self, crop: RenderedCrop, output_path: Path) -> OCRProviderResult:
        if self.executable is None or not self.executable.is_file() or not self.worker_script.is_file():
            return OCRProviderResult(
                status=FallbackStatus.FALLBACK_UNAVAILABLE,
                raw_artifact=None,
                backend_metadata=self.cache_identity,
                command_metadata={"available": False},
                stderr_summary="External OCR executable or worker script is unavailable",
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = self.build_command(crop.image_path, output_path)
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            log_path = output_path.with_suffix(".stderr.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(str(error), encoding="utf-8")
            return OCRProviderResult(
                status=FallbackStatus.FAILED,
                raw_artifact=None,
                backend_metadata=self.cache_identity,
                command_metadata={"executable": self.executable.name, "worker": self.worker_script.name},
                stderr_summary=str(error)[:1000],
                elapsed_seconds=time.perf_counter() - started,
                log_path=log_path,
            )
        success = completed.returncode == 0 and output_path.is_file()
        log_path = None
        if not success:
            log_path = output_path.with_suffix(".stderr.log")
            log_path.write_text(completed.stderr or completed.stdout, encoding="utf-8")
        backend_metadata = dict(self.cache_identity)
        if success and completed.stdout:
            try:
                worker_metadata = json.loads(completed.stdout.strip().splitlines()[-1])
                if worker_metadata.get("paddleocr_version"):
                    backend_metadata["backend_version"] = str(
                        worker_metadata["paddleocr_version"]
                    )
            except (json.JSONDecodeError, AttributeError):
                pass
        return OCRProviderResult(
            status=FallbackStatus.RECOVERED if success else FallbackStatus.FAILED,
            raw_artifact=output_path if success else None,
            backend_metadata=backend_metadata,
            command_metadata={
                "executable": self.executable.name,
                "worker": self.worker_script.name,
                "arguments": ["--device", self.device, "--language", self.language],
            },
            exit_code=completed.returncode,
            stderr_summary=completed.stderr[-1000:] if completed.stderr else None,
            elapsed_seconds=time.perf_counter() - started,
            log_path=log_path,
        )


class TableOCRCache:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @staticmethod
    def key(
        *, pdf_sha256: str, page: int, bbox: BoundingBox, dpi: int,
        backend_identity: dict[str, Any]
    ) -> str:
        payload = {
            "pdf_sha256": pdf_sha256.upper(),
            "page": int(page),
            "bbox": [round(value, 4) for value in bbox.to_list()],
            "dpi": int(dpi),
            "backend": backend_identity,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]

    def directory(self, cache_key: str) -> Path:
        return self.root / cache_key

    def load(self, cache_key: str) -> dict[str, Any] | None:
        manifest_path = self.directory(cache_key) / "manifest.json"
        if not manifest_path.is_file():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            artifact = manifest_path.parent / manifest["ocr_artifact"]
            if not artifact.is_file() or sha256_file(artifact) != manifest["ocr_json_sha256"]:
                return None
            manifest["_artifact_path"] = artifact
            return manifest
        except (KeyError, OSError, ValueError, json.JSONDecodeError):
            return None

    def save(self, cache_key: str, manifest: dict[str, Any]) -> Path:
        directory = self.directory(cache_key)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        return path


@dataclass
class FallbackRunRecord:
    candidate: TableFallbackCandidate
    region: LocalizedTableRegion
    status: FallbackStatus
    cache_hit: bool
    raw_artifact: Path | None = None
    manifest_path: Path | None = None
    table: Any | None = None
    error: str | None = None
    log_path: Path | None = None


@dataclass
class FallbackRunResult:
    records: list[FallbackRunRecord] = field(default_factory=list)

    @property
    def tables(self) -> list[Any]:
        return [record.table for record in self.records if record.table is not None]


class TableFallbackCoordinator:
    """Coordinate detection, local crops, cached OCR and deterministic reconstruction."""

    def __init__(
        self,
        *,
        provider: TableOCRProvider,
        cache: TableOCRCache,
        renderer: PyMuPDFCropRenderer | None = None,
        detector: TableFailureDetector | None = None,
        locator: TableRegionLocator | None = None,
        reconstructor: SpatialTableReconstructor | None = None,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.renderer = renderer or PyMuPDFCropRenderer()
        self.detector = detector or TableFailureDetector()
        self.locator = locator or TableRegionLocator()
        self.reconstructor = reconstructor or SpatialTableReconstructor()

    def run(self, *, paper_id: str, pdf_path: str | Path, middle_json_path: str | Path) -> FallbackRunResult:
        import pymupdf

        pdf_path = Path(pdf_path)
        middle_json_path = Path(middle_json_path)
        payload = json.loads(middle_json_path.read_text(encoding="utf-8"))
        candidates = self.detector.detect(payload)
        pdf_sha = sha256_file(pdf_path)
        result = FallbackRunResult()
        with pymupdf.open(pdf_path) as document:
            for candidate in candidates:
                page = document[candidate.page - 1]
                blocks = payload["pages"][candidate.page - 1].get("blocks", [])
                region = self.locator.locate(
                    candidate,
                    page_width=page.rect.width,
                    page_height=page.rect.height,
                    page_blocks=blocks,
                )
                cache_key = self.cache.key(
                    pdf_sha256=pdf_sha,
                    page=candidate.page,
                    bbox=region.pdf_bbox,
                    dpi=self.renderer.dpi,
                    backend_identity=self.provider.cache_identity,
                )
                cached = self.cache.load(cache_key)
                if cached is not None:
                    record = self._reconstruct_from_manifest(
                        paper_id, candidate, region, cached, True
                    )
                    result.records.append(record)
                    continue
                directory = self.cache.directory(cache_key)
                crop = self.renderer.render(pdf_path, region, directory / "crop.png")
                provider_result = self.provider.run(crop, directory / "ocr.json")
                if provider_result.status is not FallbackStatus.RECOVERED:
                    result.records.append(FallbackRunRecord(
                        candidate=candidate, region=region, status=provider_result.status,
                        cache_hit=False, error=provider_result.stderr_summary,
                        log_path=provider_result.log_path,
                    ))
                    continue
                assert provider_result.raw_artifact is not None
                table_region = crop.transform.pdf_to_pixel(region.table_pdf_bbox)
                runtime_evidence = {
                    "source_pdf": pdf_path.as_posix(),
                    "source_pdf_sha256": pdf_sha,
                    "middle_json": middle_json_path.as_posix(),
                    "crop_artifact": crop.image_path.as_posix(),
                    "crop_image_sha256": crop.sha256,
                    "coordinate_transform": crop.transform.to_mapping(),
                    "localization_method": region.localization_method,
                    "trigger_reason": region.reason,
                    "source_anchors": [asdict(anchor) | {"bbox": anchor.bbox.to_list()} for anchor in region.source_anchors],
                }
                manifest = {
                    "cache_key": cache_key,
                    "paper_id": paper_id,
                    "table_id": candidate.designator.split(maxsplit=1)[-1].rstrip(".:").upper(),
                    "source_pdf": pdf_path.as_posix(),
                    "source_pdf_sha256": pdf_sha,
                    "page": candidate.page,
                    "crop_pdf_bbox": region.pdf_bbox.to_list(),
                    "table_pdf_bbox": region.table_pdf_bbox.to_list(),
                    "table_region_crop_pixels": table_region.to_list(),
                    "dpi": crop.dpi,
                    "coordinate_transform": crop.transform.to_mapping(),
                    "crop_image": crop.image_path.name,
                    "crop_image_sha256": crop.sha256,
                    "ocr_backend": provider_result.backend_metadata,
                    "runtime_command": provider_result.command_metadata,
                    "ocr_artifact": provider_result.raw_artifact.name,
                    "ocr_json_sha256": sha256_file(provider_result.raw_artifact),
                    "elapsed_seconds": provider_result.elapsed_seconds,
                    "created_utc_epoch": int(time.time()),
                    "runtime_evidence": runtime_evidence,
                }
                manifest_path = self.cache.save(cache_key, manifest)
                manifest["_artifact_path"] = provider_result.raw_artifact
                record = self._reconstruct_from_manifest(
                    paper_id, candidate, region, manifest, False
                )
                record.manifest_path = manifest_path
                result.records.append(record)
        return result

    def _reconstruct_from_manifest(
        self,
        paper_id: str,
        candidate: TableFallbackCandidate,
        region: LocalizedTableRegion,
        manifest: dict[str, Any],
        cache_hit: bool,
    ) -> FallbackRunRecord:
        artifact = Path(manifest["_artifact_path"])
        spec = TableRecoverySpec(
            table_id=candidate.designator.split(maxsplit=1)[-1].rstrip(".:").upper(),
            page=candidate.page,
            raw_artifact=artifact,
            sha256=manifest["ocr_json_sha256"],
            table_region=BoundingBox.from_sequence(manifest["table_region_crop_pixels"]),
            coordinate_space="crop_pixels",
            header_rows=1,
            producer=dict(manifest["ocr_backend"]),
            runtime_evidence=dict(manifest.get("runtime_evidence", {})),
        )
        try:
            table = self.reconstructor.reconstruct(load_ocr_tokens(spec), spec)
        except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
            return FallbackRunRecord(
                candidate=candidate, region=region, status=FallbackStatus.FAILED,
                cache_hit=cache_hit, raw_artifact=artifact, error=str(error),
            )
        return FallbackRunRecord(
            candidate=candidate, region=region, status=FallbackStatus.RECOVERED,
            cache_hit=cache_hit, raw_artifact=artifact, table=table,
            manifest_path=artifact.parent / "manifest.json",
        )


def load_runtime_recovery_specs(root: str | Path) -> tuple[str, list[TableRecoverySpec]]:
    """Load reconstruction specs from runtime-cache manifests."""
    manifests = sorted(Path(root).glob("*/manifest.json"))
    if not manifests:
        raise ValueError(f"No runtime OCR manifests found in {root}")
    paper_ids: set[str] = set()
    specs: list[TableRecoverySpec] = []
    for path in manifests:
        payload = json.loads(path.read_text(encoding="utf-8"))
        paper_ids.add(str(payload["paper_id"]))
        specs.append(TableRecoverySpec(
            table_id=str(payload["table_id"]),
            page=int(payload["page"]),
            raw_artifact=path.parent / payload["ocr_artifact"],
            sha256=str(payload["ocr_json_sha256"]),
            table_region=BoundingBox.from_sequence(payload["table_region_crop_pixels"]),
            coordinate_space="crop_pixels",
            header_rows=1,
            producer=dict(payload["ocr_backend"]),
            runtime_evidence=dict(payload.get("runtime_evidence", {})),
        ))
    if len(paper_ids) != 1:
        raise ValueError("Runtime OCR cache contains multiple paper IDs")
    return paper_ids.pop(), specs
