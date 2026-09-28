import json
from pathlib import Path

import pytest

from src.parser.table_recovery import (
    BoundingBox,
    CoordinateTransform,
    FallbackStatus,
    PaddleOCRCLIProvider,
    PyMuPDFCropRenderer,
    SourceAnchor,
    TableFailureDetector,
    TableFallbackCoordinator,
    TableFallbackCandidate,
    TableOCRCache,
    TableRecoverySpec,
    TableRegionLocator,
    TriggerReason,
    load_ocr_tokens,
    load_runtime_recovery_specs,
    sha256_file,
)
from src.benchmark.table_recovery_evaluator import evaluate_table_recovery


ROOT = Path(__file__).resolve().parents[1]
B02_MIDDLE = ROOT / "data" / "parsed" / "B02" / "mineru" / "raw" / "middle_json" / "B02.json"
B02_RUNTIME = ROOT / "data" / "parsed" / "B02" / "light_ocr" / "runtime_raw"


def block(kind, index, bbox, text=""):
    return {
        "type": kind,
        "index": index,
        "bbox": bbox,
        "content": [{"type": "text", "content": text}] if text else [],
    }


def payload(*blocks):
    return {
        "schema": "docvortex.middle",
        "schema_version": "2.0",
        "pages": [{"page_idx": 0, "blocks": list(blocks)}],
    }


def candidate(*, image=False, anchor_bbox=(0.1, 0.2, 0.2, 0.22)):
    anchor = SourceAnchor(0, "paragraph_title", "TABLE 2", BoundingBox(*anchor_bbox))
    title = SourceAnchor(1, "paragraph_title", "RESULTS", BoundingBox(0.1, 0.23, 0.4, 0.25))
    suspected = SourceAnchor(2, "image", "", BoundingBox(0.1, 0.26, 0.8, 0.6)) if image else None
    return TableFallbackCandidate(
        page=1,
        designator="TABLE 2",
        status=FallbackStatus.CANDIDATE,
        reason=(TriggerReason.TABLE_MISCLASSIFIED_AS_IMAGE if image else TriggerReason.TABLE_BODY_MISSING),
        confidence=0.9,
        anchor=anchor,
        title=title,
        suspected_image=suspected,
    )


def test_existing_valid_table_does_not_trigger_fallback():
    document = payload(
        block("paragraph_title", 0, [0.1, 0.1, 0.2, 0.12], "TABLE I"),
        block("table", 1, [0.1, 0.13, 0.8, 0.5], "A | B"),
    )
    assert TableFailureDetector().detect(document) == []


@pytest.mark.parametrize("anchor", ["TABLE I", "Table II", "TABLE 2", "Table 3."])
def test_common_table_designators_trigger_without_table(anchor):
    detected = TableFailureDetector().detect(
        payload(block("paragraph_title", 0, [0.1, 0.1, 0.2, 0.12], anchor))
    )
    assert len(detected) == 1
    assert detected[0].reason is TriggerReason.TABLE_BODY_MISSING


def test_suspected_uncaptioned_image_triggers_misclassified_reason():
    detected = TableFailureDetector().detect(payload(
        block("paragraph_title", 0, [0.1, 0.1, 0.2, 0.12], "TABLE IV"),
        block("paragraph_title", 1, [0.1, 0.13, 0.5, 0.15], "MEASUREMENTS"),
        block("image", 2, [0.08, 0.16, 0.85, 0.55]),
    ))
    assert detected[0].reason is TriggerReason.TABLE_MISCLASSIFIED_AS_IMAGE
    assert detected[0].suspected_image is not None


def test_scientific_figure_image_is_not_misclassified_as_table_body():
    detected = TableFailureDetector().detect(payload(
        block("paragraph_title", 0, [0.1, 0.1, 0.2, 0.12], "TABLE IV"),
        block("image", 1, [0.08, 0.16, 0.85, 0.55], "Fig. 4. Waveform"),
    ))
    assert detected[0].reason is TriggerReason.TABLE_BODY_MISSING


def test_no_table_evidence_produces_no_candidate():
    assert TableFailureDetector().detect(
        payload(block("text", 0, [0.1, 0.1, 0.8, 0.2], "ordinary paragraph"))
    ) == []


def test_image_region_uses_image_union_and_keeps_table_body():
    region = TableRegionLocator().locate(
        candidate(image=True), page_width=600, page_height=800
    )
    assert region.localization_method == "nearby_uncaptioned_image_union"
    assert region.table_pdf_bbox == BoundingBox(60, 208, 480, 480)
    assert region.pdf_bbox.x0 < region.table_pdf_bbox.x0
    assert region.pdf_bbox.y0 < region.table_pdf_bbox.y0


def test_no_image_region_uses_column_and_structural_boundary():
    blocks = [block("paragraph_title", 8, [0.1, 0.7, 0.3, 0.72], "NEXT SECTION")]
    region = TableRegionLocator().locate(
        candidate(image=False), page_width=600, page_height=800, page_blocks=blocks
    )
    assert region.localization_method == "conservative_left_column"
    assert region.table_pdf_bbox.x1 == pytest.approx(306)
    assert region.table_pdf_bbox.y1 == pytest.approx(552)


def test_region_crop_is_clamped_inside_page():
    item = candidate(image=False, anchor_bbox=(0.9, 0.96, 0.99, 0.99))
    region = TableRegionLocator(margin_ratio=0.1).locate(
        item, page_width=600, page_height=800
    )
    assert 0 <= region.pdf_bbox.x0 <= region.pdf_bbox.x1 <= 600
    assert 0 <= region.pdf_bbox.y0 <= region.pdf_bbox.y1 <= 800


def test_pixel_to_pdf_coordinate_transform_and_round_trip():
    transform = CoordinateTransform(BoundingBox(100, 200, 300, 500), 4.0, 3.0, 800, 900)
    pixels = BoundingBox(40, 60, 440, 360)
    pdf = transform.pixel_to_pdf(pixels)
    assert pdf == BoundingBox(110, 220, 210, 320)
    round_trip = transform.pdf_to_pixel(pdf)
    assert round_trip.to_list() == pytest.approx(pixels.to_list(), abs=1e-9)


def test_crop_renderer_records_actual_scale_and_bounds(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "source.pdf"
    document = pymupdf.open()
    document.new_page(width=200, height=300)
    document.save(pdf)
    document.close()
    region = TableRegionLocator().locate(
        candidate(image=True), page_width=200, page_height=300
    )
    crop = PyMuPDFCropRenderer(dpi=144).render(pdf, region, tmp_path / "crop.png")
    assert crop.image_path.is_file()
    assert crop.transform.pixel_width > 0
    assert crop.transform.scale_x == pytest.approx(2.0, rel=0.02)
    assert crop.sha256 == sha256_file(crop.image_path)


def test_provider_command_generation_uses_external_worker(tmp_path):
    executable = tmp_path / "python.exe"
    worker = tmp_path / "worker.py"
    executable.write_bytes(b"")
    worker.write_text("", encoding="utf-8")
    provider = PaddleOCRCLIProvider(executable=executable, worker_script=worker)
    command = provider.build_command(Path("crop.png"), Path("ocr.json"))
    assert command[0] == str(executable)
    assert command[1] == str(worker)
    assert "--input" in command and "--output" in command


def test_provider_unavailable_is_nonfatal(tmp_path):
    provider = PaddleOCRCLIProvider(
        executable=tmp_path / "missing.exe", worker_script=tmp_path / "missing.py"
    )
    result = provider.run(None, tmp_path / "ocr.json")  # type: ignore[arg-type]
    assert result.status is FallbackStatus.FALLBACK_UNAVAILABLE
    assert "unavailable" in result.stderr_summary.lower()


def test_provider_subprocess_failure_is_reported(monkeypatch, tmp_path):
    executable = tmp_path / "python.exe"
    worker = tmp_path / "worker.py"
    executable.write_bytes(b"")
    worker.write_text("", encoding="utf-8")
    provider = PaddleOCRCLIProvider(executable=executable, worker_script=worker)

    class Completed:
        returncode = 7
        stdout = ""
        stderr = "model initialization failed"

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Completed())
    fake_crop = type("Crop", (), {"image_path": tmp_path / "crop.png"})()
    result = provider.run(fake_crop, tmp_path / "ocr.json")
    assert result.status is FallbackStatus.FAILED
    assert result.exit_code == 7
    assert "initialization" in result.stderr_summary
    assert result.log_path is not None and result.log_path.is_file()


def test_cache_key_is_deterministic_and_path_independent():
    kwargs = dict(
        pdf_sha256="ABCD", page=4, bbox=BoundingBox(1, 2, 3, 4), dpi=288,
        backend_identity={"backend": "test", "version": "1"},
    )
    assert TableOCRCache.key(**kwargs) == TableOCRCache.key(**kwargs)


def test_cache_manifest_validates_raw_artifact_sha(tmp_path):
    cache = TableOCRCache(tmp_path)
    directory = cache.directory("key")
    directory.mkdir()
    artifact = directory / "ocr.json"
    artifact.write_text('{"rec_texts": []}', encoding="utf-8")
    cache.save("key", {"ocr_artifact": "ocr.json", "ocr_json_sha256": sha256_file(artifact)})
    assert cache.load("key")["_artifact_path"] == artifact
    artifact.write_text("changed", encoding="utf-8")
    assert cache.load("key") is None


def test_runtime_token_retains_crop_and_pdf_bbox(tmp_path):
    artifact = tmp_path / "ocr.json"
    artifact.write_text(json.dumps({
        "rec_texts": ["A"], "rec_scores": [0.9], "rec_boxes": [[20, 30, 60, 90]]
    }), encoding="utf-8")
    spec = TableRecoverySpec(
        table_id="1", page=2, raw_artifact=artifact, sha256=sha256_file(artifact),
        table_region=BoundingBox(0, 0, 100, 100), coordinate_space="crop_pixels",
        header_rows=1, producer={"name": "test"},
        runtime_evidence={"coordinate_transform": {
            "crop_pdf_bbox": [100, 200, 200, 300], "scale_x": 2, "scale_y": 3,
        }},
    )
    item = load_ocr_tokens(spec)[0]
    assert item.bbox == BoundingBox(20, 30, 60, 90)
    assert item.pdf_bbox == BoundingBox(110, 210, 130, 230)


def test_b02_fixture_detection_finds_two_runtime_candidates():
    detected = TableFailureDetector().detect(json.loads(B02_MIDDLE.read_text(encoding="utf-8")))
    assert len(detected) == 2
    assert {item.reason for item in detected} == {
        TriggerReason.TABLE_BODY_MISSING,
        TriggerReason.TABLE_MISCLASSIFIED_AS_IMAGE,
    }
    assert {item.page for item in detected} == {8, 11}


def test_core_runtime_module_does_not_import_paddleocr():
    source = (ROOT / "src" / "parser" / "table_recovery" / "runtime.py").read_text(encoding="utf-8")
    assert "import paddleocr" not in source.casefold()


def test_runtime_manifests_reconstruct_without_external_ocr():
    paper_id, specs = load_runtime_recovery_specs(B02_RUNTIME)
    assert paper_id == "B02"
    assert [(spec.table_id, spec.page) for spec in specs] == [("II", 11), ("I", 8)]
    tokens = load_ocr_tokens(specs[0])
    assert tokens and tokens[0].pdf_bbox is not None


def test_runtime_layer_c_preserves_layer_a_and_b():
    baseline_path = ROOT / "data" / "benchmark" / "B02" / "B02_BENCHMARK_RESULT.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    result = evaluate_table_recovery(
        ROOT / "data" / "benchmark" / "B02" / "B02_GROUND_TRUTH.yaml",
        baseline_path,
        ROOT / "data" / "parsed" / "B02" / "light_ocr" / "B02_LIGHT_OCR_MANIFEST.yaml",
        runtime_manifest_dir=B02_RUNTIME,
    )
    assert result["layer_a"]["metrics"] == baseline["metrics"]
    assert result["layer_b"] == baseline["layer_b"]
    assert result["layer_c"]["artifact_source"] == "runtime_cache"
    assert result["layer_c"]["tables"]["tp"] == 2


def test_cache_hit_skips_ocr_provider_call():
    class NoCallProvider:
        cache_identity = {
            "backend": "ordinary_paddleocr_external",
            "provider_version": "1",
            "language": "en",
            "device": "gpu:0",
            "orientation_classification": False,
            "document_unwarping": False,
            "textline_orientation": False,
        }

        def run(self, crop, output_path):
            raise AssertionError("cache hit must skip OCR")

    result = TableFallbackCoordinator(
        provider=NoCallProvider(), cache=TableOCRCache(B02_RUNTIME)
    ).run(
        paper_id="B02",
        pdf_path=ROOT / "data" / "benchmark" / "B02" / "B02.pdf",
        middle_json_path=B02_MIDDLE,
    )
    assert len(result.records) == 2
    assert all(record.cache_hit for record in result.records)
