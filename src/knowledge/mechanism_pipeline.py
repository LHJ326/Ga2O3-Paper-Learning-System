"""Auditable P001 mechanism extraction orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.schema import Document

from .mechanism_extractor import MechanismExtractor, PreparedMechanismExtraction
from .mechanism_schema import MechanismDraft, MechanismSchema
from .mechanism_validator import MechanismValidator
from .mechanism_writer import MechanismWriter
from .prompt_builder import PromptEvidence


@dataclass(frozen=True)
class MechanismPipelineResult:
    mechanism_path: Path
    prompts_path: Path
    responses_path: Path
    run_manifest_path: Path
    api_calls: int
    selected_evidence_count: int
    chunk_count: int
    input_chars: int
    output_chars: int
    extracted_field_count: int
    null_field_count: int


class MechanismExtractionPipeline:
    def __init__(self, *, extractor: MechanismExtractor, validator: MechanismValidator,
                 writer: MechanismWriter) -> None:
        self.extractor = extractor
        self.validator = validator
        self.writer = writer

    def run(
        self, *, document: Document, schema: MechanismSchema,
        output_dir: str | Path, prepared: PreparedMechanismExtraction | None = None,
    ) -> MechanismPipelineResult:
        prepared = prepared or self.extractor.prepare(document=document, schema=schema)
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        prompts_path = output / "mechanism_extraction_prompts.jsonl"
        responses_path = output / "mechanism_extraction_responses.jsonl"
        manifest_path = output / "mechanism_extraction_run.yaml"
        self._write_jsonl(prompts_path, [
            {"call_index": index, "evidence_ids": [e.evidence_id for e in chunk.evidence],
             "prompt": prompt}
            for index, (chunk, prompt) in enumerate(zip(prepared.chunks, prepared.prompts), 1)
        ])
        response_records: list[dict[str, Any]] = []
        try:
            def persist(records: list[dict[str, Any]]) -> None:
                response_records[:] = records
                self._write_jsonl(responses_path, records)

            result = self.extractor.extract(
                schema=schema, prepared=prepared, response_callback=persist
            )
            selected = {item.evidence_id: item for item in prepared.selected_evidence}
            referenced = self._references(result.mechanisms)
            draft = MechanismDraft(
                schema.schema_version, "P001", schema.domain_id, result.mechanisms,
                [self._evidence_record(selected[eid]) for eid in referenced if eid in selected],
            )
            self.validator.validate(draft).raise_if_invalid()
            mechanism_path = self.writer.write(draft)
            extracted = sum(value is not None for value in draft.mechanisms.values())
            review = any(
                entry.get("review_status") == "review_required"
                for value in draft.mechanisms.values()
                for entry in (value if isinstance(value, list) else [value])
                if isinstance(entry, dict)
            )
            manifest = {
                "paper_id": "P001", "task": "mechanism_only",
                "status": "review_required" if review else "success",
                "api_calls": len(prepared.prompts),
                "selected_evidence_count": len(prepared.selected_evidence),
                "chunk_count": len(prepared.chunks),
                "max_prompt_chars": prepared.max_prompt_chars,
                "input_chars": prepared.total_prompt_chars,
                "estimated_input_tokens": prepared.estimated_input_tokens,
                "estimated_input_cost_usd_off_peak": prepared.estimated_input_cost_usd[0],
                "estimated_input_cost_usd_peak": prepared.estimated_input_cost_usd[1],
                "output_chars": result.output_chars,
                "extracted_field_count": extracted,
                "null_field_count": len(draft.mechanisms) - extracted,
                "evidence_coverage": 1.0,
                "review_required": review,
            }
            self._write_yaml(manifest_path, manifest)
        except Exception as error:
            self._write_jsonl(responses_path, response_records)
            self._write_yaml(manifest_path, {
                "paper_id": "P001", "task": "mechanism_only", "status": "failed",
                "api_calls": len(response_records),
                "selected_evidence_count": len(prepared.selected_evidence),
                "chunk_count": len(prepared.chunks),
                "input_chars": prepared.total_prompt_chars,
                "error_type": type(error).__name__,
            })
            raise
        return MechanismPipelineResult(
            mechanism_path, prompts_path, responses_path, manifest_path,
            manifest["api_calls"], manifest["selected_evidence_count"],
            manifest["chunk_count"], manifest["input_chars"], manifest["output_chars"],
            manifest["extracted_field_count"], manifest["null_field_count"],
        )

    @staticmethod
    def _references(mechanisms: dict[str, Any]) -> list[str]:
        refs: list[str] = []
        for value in mechanisms.values():
            for item in value if isinstance(value, list) else [value]:
                if isinstance(item, dict):
                    evidence_id = item.get("evidence_id")
                    if isinstance(evidence_id, str) and evidence_id not in refs:
                        refs.append(evidence_id)
        return refs

    @staticmethod
    def _evidence_record(item: PromptEvidence) -> dict[str, Any]:
        return {"evidence_id": item.evidence_id, "page": item.page,
                "element_id": item.element_id, "element_type": item.element_type,
                "source_reference": item.source_reference, "quote": item.content}

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in records)
            + ("\n" if records else ""), encoding="utf-8"
        )
        temporary.replace(path)

    @staticmethod
    def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        temporary.replace(path)
