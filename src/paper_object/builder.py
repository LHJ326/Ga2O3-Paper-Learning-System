"""Assemble existing P001 artifacts into one lossless Paper Object."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any
import yaml
from .schema import PROJECT_ROOT, PaperObjectSchema, load_paper_object_schema
from .validator import PaperObjectValidator

class PaperObjectBuildError(ValueError):
    pass

class PaperObjectBuilder:
    KNOWLEDGE_FILES = {
        "summary": "summary.md", "parameters": "device_parameters.yaml",
        "performance": "performance.yaml", "mechanism": "mechanism.yaml",
    }

    def __init__(self, *, project_root: str | Path = PROJECT_ROOT,
                 schema: PaperObjectSchema | None = None) -> None:
        self.project_root = Path(project_root)
        self.schema = schema or load_paper_object_schema()

    def build(self, paper_id: str) -> dict[str, Any]:
        paper = self.project_root / "data" / "papers" / paper_id
        knowledge_dir = paper / "knowledge"
        if not paper.is_dir():
            raise FileNotFoundError(f"Paper Object directory does not exist: {paper}")
        paths = {name: knowledge_dir / filename for name, filename in self.KNOWLEDGE_FILES.items()}
        missing = [path for path in paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"required knowledge artifact is missing: {missing[0]}")
        metadata = self._load_optional_yaml(self.project_root / "data" / "metadata" / f"{paper_id}.yaml")
        summary = paths["summary"].read_text(encoding="utf-8")
        parameters = self._load_yaml(paths["parameters"])
        performance = self._load_yaml(paths["performance"])
        mechanism = self._load_yaml(paths["mechanism"])
        knowledge = {"summary": summary, "parameters": parameters,
                     "performance": performance, "mechanism": mechanism}

        evidence: dict[str, dict[str, Any]] = {}
        for artifact in (parameters, performance, mechanism):
            for record in artifact.get("evidence_index", []):
                self._merge_evidence(evidence, self._normalize_evidence(record))
        summary_refs = set(re.findall(r"\bE\d{5}\b", summary))
        for record in self._summary_evidence(knowledge_dir):
            if record["evidence_id"] in summary_refs:
                self._merge_evidence(evidence, record)

        references = PaperObjectValidator.collect_references(knowledge)
        resolved = references & set(evidence)
        coverage = len(resolved) / len(references) if references else 1.0
        warnings, review_required = self._validation(knowledge_dir, mechanism)
        payload = {
            "schema_version": self.schema.schema_version,
            "object_type": self.schema.object_type,
            "paper_identity": {
                "paper_id": paper_id,
                "title": metadata.get("title"),
                "authors": metadata.get("authors"),
                "year": metadata.get("year"),
                "journal": metadata.get("journal"),
                "doi": metadata.get("doi", metadata.get("DOI")),
            },
            "source": {
                "pdf_path": metadata.get("source_pdf"),
                "parsed_path": self._relative_if_exists(
                    self.project_root / "data" / "parsed" / paper_id / "mineru" / "raw"
                ),
                "evidence_index": [evidence[key] for key in sorted(evidence)],
            },
            "knowledge": knowledge,
            "validation": {
                "evidence_coverage": round(coverage, 6),
                "warnings": warnings,
                "review_status": "review_required" if review_required or warnings else "passed",
            },
        }
        PaperObjectValidator(self.schema).validate(payload).raise_if_invalid()
        return payload

    def _summary_evidence(self, knowledge_dir: Path) -> list[dict[str, Any]]:
        path = knowledge_dir / "summary_extraction_prompts.jsonl"
        if not path.is_file():
            raise FileNotFoundError(f"Summary Evidence provenance does not exist: {path}")
        records: dict[str, dict[str, Any]] = {}
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip(): continue
            outer = json.loads(line)
            prompt = outer.get("prompt")
            if not isinstance(prompt, str) or "Extraction task:\n" not in prompt:
                raise PaperObjectBuildError(f"invalid Summary prompt provenance at line {line_number}")
            task = json.loads(prompt.split("Extraction task:\n", 1)[1])
            for item in task.get("evidence", []):
                record = self._normalize_evidence(item)
                self._merge_evidence(records, record)
        return list(records.values())

    @staticmethod
    def _normalize_evidence(record: Any) -> dict[str, Any]:
        if not isinstance(record, dict):
            raise PaperObjectBuildError("Evidence record must be a mapping")
        return {
            "evidence_id": record.get("evidence_id"),
            "page": record.get("page"),
            "element_id": record.get("element_id"),
            "element_type": record.get("element_type"),
            "source_reference": record.get("source_reference"),
            "quote": record.get("quote", record.get("content", "")),
        }

    @staticmethod
    def _merge_evidence(index: dict[str, dict[str, Any]], record: dict[str, Any]) -> None:
        evidence_id = record.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise PaperObjectBuildError("Evidence ID must be non-empty")
        previous = index.get(evidence_id)
        if previous is not None and previous != record:
            raise PaperObjectBuildError(f"conflicting Evidence records for {evidence_id}")
        index[evidence_id] = record

    def _validation(self, knowledge_dir: Path, mechanism: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
        warnings: list[dict[str, Any]] = []
        review_required = False
        quality = self._load_optional_yaml(knowledge_dir / "quality_report.yaml")
        if quality.get("review_required"):
            review_required = True
        missing_sections = quality.get("missing_sections")
        if isinstance(missing_sections, list) and missing_sections:
            warnings.append({"source": "summary_quality", "issue": "missing summary sections",
                             "fields": missing_sections})
        for name in ("device", "performance", "mechanism"):
            report = self._load_optional_yaml(knowledge_dir / f"{name}_extraction_run.yaml")
            if report.get("review_required") or report.get("status") == "review_required":
                review_required = True
            for warning in report.get("warnings", []) if isinstance(report.get("warnings", []), list) else []:
                warnings.append({"source": f"{name}_extraction", **warning})
        for field, value in mechanism.get("mechanisms", {}).items():
            entries = value if isinstance(value, list) else [value]
            for entry in entries:
                if isinstance(entry, dict) and entry.get("review_status") == "review_required":
                    warnings.append({"source": "mechanism", "field": field,
                                     "evidence_id": entry.get("evidence_id"),
                                     "issue": "mechanism observation requires review"})
        return warnings, review_required

    def _relative_if_exists(self, path: Path) -> str | None:
        return path.relative_to(self.project_root).as_posix() if path.exists() else None

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PaperObjectBuildError(f"YAML artifact must be a mapping: {path}")
        return payload

    @classmethod
    def _load_optional_yaml(cls, path: Path) -> dict[str, Any]:
        return cls._load_yaml(path) if path.is_file() else {}
