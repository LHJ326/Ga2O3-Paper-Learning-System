"""Write reproducible Summary Knowledge validation artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .quality import SummaryQualityReport


class QualityReportWriter:
    @staticmethod
    def _write(path: Path, text: str) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
        temporary.replace(path)

    def write(
        self, report: SummaryQualityReport, *, knowledge_path: str | Path
    ) -> dict[str, Path]:
        output = Path(knowledge_path)
        output.mkdir(parents=True, exist_ok=True)
        payload = report.as_dict()
        quality_payload = {
            "paper_id": report.paper_id,
            "structure_score": report.structure.score,
            "evidence_score": report.evidence.coverage,
            "parameter_check": payload["parameter_check"],
            "overall_status": report.overall_status,
            "review_required": report.review_required,
            "missing_sections": list(report.structure.missing_sections),
            "claim_counts": {
                "total": report.evidence.total_claims,
                "supported": report.evidence.supported_claims,
                "unsupported": report.evidence.unsupported_claims,
            },
        }
        quality_path = output / "quality_report.yaml"
        log_path = output / "validation_log.json"
        self._write(
            quality_path,
            yaml.safe_dump(quality_payload, allow_unicode=True, sort_keys=False),
        )
        self._write(
            log_path,
            json.dumps(
                {
                    "validation_schema_version": "1.0",
                    **payload,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        return {"quality_report": quality_path, "validation_log": log_path}
