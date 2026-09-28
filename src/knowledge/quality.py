"""Deterministic quality checks for evidence-linked scientific summaries."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SUMMARY_STRUCTURE = {
    "Research Objective": ("research objective",),
    "Material/System": ("material/system", "material system", "materials and system"),
    "Device Structure": ("device structure", "device architecture"),
    "Mechanism": ("mechanism", "working mechanism"),
    "Performance": ("performance", "experimental results", "device performance"),
    "Innovation": ("innovation", "core innovations"),
    "Limitation": ("limitation", "limitations", "reported limitations"),
}
_EVIDENCE_ID = re.compile(r"\bE\d+\b")
_NUMBER = (
    r"\d+(?:\.\d+)?(?:\s*(?:×|x)\s*10\s*(?:\^|\*\*)?\s*[+-]?\d+"
    r"|[eE][+-]?\d+|(?:\^|\*\*)\s*[+-]?\d+)?"
)


class QualityInputError(ValueError):
    """Raised when required summary-validation input cannot be loaded."""


@dataclass(frozen=True)
class StructureCheck:
    required_sections: tuple[str, ...]
    present_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    score: float


@dataclass(frozen=True)
class EvidenceCheck:
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    coverage: float
    unsupported_details: tuple[dict[str, Any], ...]
    prompt_records: int
    response_records: int


@dataclass(frozen=True)
class ParameterWarning:
    parameter: str
    value: float
    unit: str
    message: str
    source_text: str


@dataclass(frozen=True)
class ParameterCheck:
    status: str
    warnings: tuple[ParameterWarning, ...]


@dataclass(frozen=True)
class SummaryQualityReport:
    paper_id: str
    structure: StructureCheck
    evidence: EvidenceCheck
    parameter_check: ParameterCheck
    overall_status: str
    review_required: bool

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["structure_score"] = self.structure.score
        payload["evidence_score"] = self.evidence.coverage
        return payload


def check_summary_structure(summary: str) -> StructureCheck:
    headings = {
        line[3:].strip().casefold()
        for line in summary.splitlines()
        if line.startswith("## ")
    }
    present = tuple(
        canonical
        for canonical, aliases in SUMMARY_STRUCTURE.items()
        if any(alias.casefold() in headings for alias in aliases)
    )
    missing = tuple(name for name in SUMMARY_STRUCTURE if name not in present)
    score = round(100.0 * len(present) / len(SUMMARY_STRUCTURE), 2)
    return StructureCheck(tuple(SUMMARY_STRUCTURE), present, missing, score)


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise QualityInputError(f"validation input does not exist: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix == ".jsonl":
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
            records = payload["records"]
        elif isinstance(payload, dict):
            records = [payload]
        else:
            raise QualityInputError(f"JSON validation input must contain records: {path}")
    if not all(isinstance(record, dict) for record in records):
        raise QualityInputError(f"validation records must be objects: {path}")
    return records


def _resolve_record_file(knowledge_path: Path, stem: str) -> Path:
    for suffix in (".json", ".jsonl"):
        candidate = knowledge_path / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate
    raise QualityInputError(f"missing {stem}.json or {stem}.jsonl in {knowledge_path}")


def _evidence_index(prompt_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in prompt_records:
        evidence = record.get("evidence")
        if not isinstance(evidence, list):
            prompt = record.get("prompt")
            if not isinstance(prompt, str) or "Extraction task:\n" not in prompt:
                continue
            try:
                task = json.loads(prompt.split("Extraction task:\n", 1)[1])
            except json.JSONDecodeError:
                continue
            evidence = task.get("evidence", [])
        for item in evidence:
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str):
                index[item["evidence_id"]] = item
    return index


def check_evidence_coverage(
    summary: str,
    prompt_records: list[dict[str, Any]],
    response_records: list[dict[str, Any]],
) -> EvidenceCheck:
    evidence = _evidence_index(prompt_records)
    claims = [
        line[2:].strip()
        for line in summary.splitlines()
        if line.startswith("- ") and "Not explicitly identified" not in line
    ]
    supported = 0
    unsupported: list[dict[str, Any]] = []
    for position, claim in enumerate(claims, start=1):
        evidence_ids = tuple(dict.fromkeys(_EVIDENCE_ID.findall(claim)))
        unresolved: list[str] = []
        for evidence_id in evidence_ids:
            item = evidence.get(evidence_id)
            if item is None:
                unresolved.append(evidence_id)
                continue
            page = item.get("page")
            source_reference = item.get("source_reference")
            source_element = item.get("element_id") or item.get("element_type")
            if (
                not isinstance(page, int)
                or isinstance(page, bool)
                or page < 1
                or not isinstance(source_reference, (str, dict))
                or not source_reference
                or not isinstance(source_element, str)
                or not source_element
            ):
                unresolved.append(evidence_id)
        if evidence_ids and not unresolved:
            supported += 1
        else:
            unsupported.append({
                "claim_index": position,
                "claim": claim,
                "evidence_ids": list(evidence_ids),
                "unresolved_evidence_ids": unresolved,
            })
    total = len(claims)
    coverage = round(100.0 * supported / total, 2) if total else 0.0
    return EvidenceCheck(
        total_claims=total,
        supported_claims=supported,
        unsupported_claims=total - supported,
        coverage=coverage,
        unsupported_details=tuple(unsupported),
        prompt_records=len(prompt_records),
        response_records=len(response_records),
    )


def _parse_number(raw: str) -> float:
    compact = re.sub(r"\s+", "", raw).replace("×", "x")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)[xX]10(?:\^|\*\*)?([+-]?\d+)", compact)
    if match:
        return float(match.group(1)) * 10 ** int(match.group(2))
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:\^|\*\*)([+-]?\d+)", compact)
    if match:
        return float(match.group(1)) ** int(match.group(2))
    return float(compact)


def check_parameter_ranges(summary: str) -> ParameterCheck:
    rules = (
        ("wavelength", re.compile(rf"(?P<value>{_NUMBER})\s*nm\b", re.I), "nm", 100, 5000),
        ("responsivity", re.compile(
            rf"responsivit(?:y|ies)[^.\n]{{0,100}}?(?P<value>{_NUMBER})\s*A\s*/\s*W", re.I
        ), "A/W", 0, 1e8),
        ("detectivity", re.compile(
            rf"detectivit(?:y|ies)[^.\n]{{0,100}}?(?P<value>{_NUMBER})\s*(?:Jones|cm\s*Hz\^?1/2\s*W-?1)", re.I
        ), "Jones", 0, 1e20),
        ("on/off ratio", re.compile(
            rf"(?:on\s*/\s*off|on-off|switching)\s+ratio[^.\n]{{0,80}}?(?P<value>{_NUMBER})", re.I
        ), "ratio", 1, 1e15),
    )
    warnings: list[ParameterWarning] = []
    for parameter, pattern, unit, minimum, maximum in rules:
        for match in pattern.finditer(summary):
            value = _parse_number(match.group("value"))
            if value < minimum or value > maximum:
                warnings.append(ParameterWarning(
                    parameter=parameter,
                    value=value,
                    unit=unit,
                    message=f"value is outside broad scientific plausibility range [{minimum}, {maximum}]",
                    source_text=match.group(0),
                ))

    time_pattern = re.compile(
        rf"(?:response|rise|fall|decay)\s+time[^.\n]{{0,80}}?"
        rf"(?P<value>{_NUMBER})\s*(?P<unit>ns|μs|µs|us|ms|s)\b",
        re.I,
    )
    factors = {"ns": 1e-9, "μs": 1e-6, "µs": 1e-6, "us": 1e-6, "ms": 1e-3, "s": 1.0}
    for match in time_pattern.finditer(summary):
        raw_unit = match.group("unit").casefold()
        value = _parse_number(match.group("value"))
        seconds = value * factors[raw_unit]
        if seconds <= 0 or seconds > 1e6:
            warnings.append(ParameterWarning(
                parameter="response time",
                value=value,
                unit=match.group("unit"),
                message="value is outside broad scientific plausibility range (0, 1000000 s]",
                source_text=match.group(0),
            ))
    return ParameterCheck("warning" if warnings else "pass", tuple(warnings))


class SummaryQualityAnalyzer:
    def analyze(self, *, paper_id: str, knowledge_path: str | Path) -> SummaryQualityReport:
        path = Path(knowledge_path)
        summary_file = path / "summary.md"
        if not summary_file.is_file():
            raise QualityInputError(f"summary does not exist: {summary_file}")
        summary = summary_file.read_text(encoding="utf-8")
        prompts = _load_records(_resolve_record_file(path, "summary_extraction_prompts"))
        responses = _load_records(_resolve_record_file(path, "summary_extraction_responses"))
        structure = check_summary_structure(summary)
        evidence = check_evidence_coverage(summary, prompts, responses)
        parameters = check_parameter_ranges(summary)
        review_required = (
            bool(structure.missing_sections)
            or evidence.coverage < 100.0
            or bool(parameters.warnings)
        )
        return SummaryQualityReport(
            paper_id=paper_id,
            structure=structure,
            evidence=evidence,
            parameter_check=parameters,
            overall_status="review_required" if review_required else "pass",
            review_required=review_required,
        )
