"""Task-specific prompt selection and evidence chunking."""

from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass, replace
from enum import Enum

from .prompt_builder import PromptEvidence


class ExtractionTask(str, Enum):
    SUMMARY = "summary"
    PARAMETER = "parameter"
    MECHANISM = "mechanism"


@dataclass(frozen=True)
class PromptStrategy:
    task: ExtractionTask
    prompt_file: str
    element_types: frozenset[str]
    response_shape: dict[str, object]
    keywords: tuple[str, ...] = ()
    always_include_types: frozenset[str] = frozenset()

    def accepts(self, item: PromptEvidence) -> bool:
        if item.element_type not in self.element_types:
            return False
        if not self.keywords or item.element_type in self.always_include_types:
            return True
        content = item.content.casefold()
        return any(keyword in content for keyword in self.keywords)


@dataclass(frozen=True)
class EvidenceChunk:
    task: ExtractionTask
    section_id: str
    element_type: str
    index: int
    evidence: tuple[PromptEvidence, ...]


class PromptStrategyRegistry:
    def __init__(self) -> None:
        common = frozenset({"Section", "TextBlock", "Figure", "Table", "Equation"})
        self._strategies = {
            ExtractionTask.SUMMARY: PromptStrategy(
                task=ExtractionTask.SUMMARY,
                prompt_file="summary_prompt.md",
                element_types=common,
                response_shape={
                    "research_problem": [],
                    "methodology": [],
                    "results": [],
                    "innovation": [],
                    "limitations": [],
                    "summary": "string",
                    "key_points": ["string"],
                },
            ),
            ExtractionTask.PARAMETER: PromptStrategy(
                task=ExtractionTask.PARAMETER,
                prompt_file="parameter_prompt.md",
                element_types=frozenset({"Section", "TextBlock", "Figure", "Table"}),
                response_shape={"fields": {}},
                keywords=(
                    "responsiv", "detectiv", "quantum efficiency", "eqe", "dark current",
                    "photocurrent", "rise time", "fall time", "decay time", "wavelength",
                    "bias", "voltage", "a/w", "jones", "doping", "dopant", "substrate",
                    "electrode", "contact", "anneal", "deposition", "fabrication",
                    "device structure", "crystal phase", "ga2o3", "β-ga", "α-ga",
                ),
                always_include_types=frozenset({"Figure", "Table"}),
            ),
            ExtractionTask.MECHANISM: PromptStrategy(
                task=ExtractionTask.MECHANISM,
                prompt_file="mechanism_prompt.md",
                element_types=frozenset({"Section", "TextBlock", "Figure", "Equation"}),
                response_shape={"mechanism": []},
                keywords=(
                    "mechanism", "trap", "defect", "carrier", "transport", "junction",
                    "barrier", "gain", "recombination", "oxygen vacancy", "adsorption",
                    "desorption", "band", "depletion", "tunnel", "photoconduct",
                    "attributed", "explained", "response process",
                ),
                always_include_types=frozenset({"Figure", "Equation"}),
            ),
        }

    def get(self, task: ExtractionTask | str) -> PromptStrategy:
        try:
            normalized = ExtractionTask(task)
        except ValueError as error:
            raise KeyError(f"unknown extraction task: {task}") from error
        return self._strategies[normalized]

    def all(self) -> tuple[PromptStrategy, ...]:
        return tuple(self._strategies[task] for task in ExtractionTask)


class EvidenceChunker:
    """Keep task, section, and element-type boundaries while limiting content."""

    def __init__(self, *, max_content_chars: int = 8_000) -> None:
        if max_content_chars < 1:
            raise ValueError("max_content_chars must be positive")
        self.max_content_chars = max_content_chars

    def chunk(
        self,
        evidence: list[PromptEvidence],
        strategy: PromptStrategy,
    ) -> list[EvidenceChunk]:
        groups: OrderedDict[tuple[str, str], list[PromptEvidence]] = OrderedDict()
        for item in evidence:
            if not strategy.accepts(item):
                continue
            key = (item.section_id or "unsectioned", item.element_type)
            groups.setdefault(key, []).extend(self._split_oversized(item))

        chunks: list[EvidenceChunk] = []
        for (section_id, element_type), items in groups.items():
            current: list[PromptEvidence] = []
            current_size = 0
            group_index = 1
            for item in items:
                item_size = self._serialized_size(item)
                if current and current_size + item_size > self.max_content_chars:
                    chunks.append(EvidenceChunk(
                        strategy.task, section_id, element_type, group_index, tuple(current)
                    ))
                    group_index += 1
                    current = []
                    current_size = 0
                current.append(item)
                current_size += item_size
            if current:
                chunks.append(EvidenceChunk(
                    strategy.task, section_id, element_type, group_index, tuple(current)
                ))
        return chunks

    def _split_oversized(self, item: PromptEvidence) -> list[PromptEvidence]:
        if self._serialized_size(item) <= self.max_content_chars:
            return [item]
        empty_size = self._serialized_size(replace(item, content=""))
        content_budget = self.max_content_chars - empty_size
        if content_budget < 1:
            raise ValueError(
                "max_content_chars is too small for evidence locator metadata"
            )
        return [
            replace(item, content=item.content[start:start + content_budget])
            for start in range(0, len(item.content), content_budget)
        ]

    @staticmethod
    def _serialized_size(item: PromptEvidence) -> int:
        return len(json.dumps(item.as_dict(), ensure_ascii=False))
