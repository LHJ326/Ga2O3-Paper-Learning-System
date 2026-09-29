"""Convert an existing Paper Object into deterministic evidence-linked chunks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator

import yaml

from .schema import EmbeddingChunk, EmbeddingSchemaError

EVIDENCE_PATTERN = re.compile(r"\bE\d{5}\b")


class PaperObjectChunker:
    """Chunk only knowledge already present in the validated Paper Object."""

    GROUPS = ("summary", "parameters", "performance", "mechanism")

    def chunk_file(self, path: str | Path) -> list[EmbeddingChunk]:
        source_path = Path(path)
        payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise EmbeddingSchemaError("Paper Object must be a YAML mapping")
        return self.chunk(payload, source_file=source_path.as_posix())

    def chunk(self, payload: dict[str, Any], *, source_file: str) -> list[EmbeddingChunk]:
        identity = payload.get("paper_identity")
        knowledge = payload.get("knowledge")
        source = payload.get("source")
        if not isinstance(identity, dict) or not isinstance(knowledge, dict) or not isinstance(source, dict):
            raise EmbeddingSchemaError("Paper Object identity, source, and knowledge are required")
        paper_id = identity.get("paper_id")
        if not isinstance(paper_id, str) or not paper_id:
            raise EmbeddingSchemaError("Paper Object paper_id is required")
        evidence_index = source.get("evidence_index")
        if not isinstance(evidence_index, list):
            raise EmbeddingSchemaError("Paper Object evidence_index must be a list")
        known_ids = {
            item.get("evidence_id") for item in evidence_index
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        }

        chunks: list[EmbeddingChunk] = []
        for group in self.GROUPS:
            content = knowledge.get(group)
            candidates = (
                self._summary_candidates(content)
                if group == "summary"
                else self._structured_candidates(content, group)
            )
            for text, evidence_ids in candidates:
                unresolved = set(evidence_ids) - known_ids
                if unresolved:
                    raise EmbeddingSchemaError(
                        f"{group} chunk references unknown Evidence IDs: {sorted(unresolved)}"
                    )
                sequence = sum(1 for item in chunks if item.chunk_id.startswith(f"{paper_id}-{group}-")) + 1
                chunks.append(EmbeddingChunk(
                    chunk_id=f"{paper_id}-{group}-{sequence:04d}",
                    paper_id=paper_id,
                    source_file=source_file,
                    evidence_ids=tuple(sorted(evidence_ids)),
                    text=text.strip(),
                ))
        return chunks

    @staticmethod
    def _summary_candidates(content: Any) -> Iterator[tuple[str, set[str]]]:
        if not isinstance(content, str):
            return
        heading: str | None = None
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                continue
            evidence_ids = set(EVIDENCE_PATTERN.findall(line))
            if evidence_ids:
                text = f"{heading}: {line}" if heading else line
                yield text, evidence_ids

    def _structured_candidates(
        self, content: Any, group: str
    ) -> Iterator[tuple[str, set[str]]]:
        yield from self._walk(content, path=group)

    def _walk(self, value: Any, *, path: str) -> Iterator[tuple[str, set[str]]]:
        if isinstance(value, dict):
            evidence_ids = self._direct_evidence_ids(value)
            if evidence_ids:
                cleaned = {key: item for key, item in value.items() if key != "evidence_index"}
                body = yaml.safe_dump(cleaned, allow_unicode=True, sort_keys=False).strip()
                yield f"Knowledge field: {path}\n{body}", evidence_ids
                return
            for key, item in value.items():
                if key == "evidence_index":
                    continue
                yield from self._walk(item, path=f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                yield from self._walk(item, path=f"{path}[{index}]")

    @staticmethod
    def _direct_evidence_ids(value: dict[str, Any]) -> set[str]:
        found: set[str] = set()
        evidence_id = value.get("evidence_id")
        if isinstance(evidence_id, str) and evidence_id:
            found.add(evidence_id)
        evidence_refs = value.get("evidence_refs")
        if isinstance(evidence_refs, list):
            for reference in evidence_refs:
                if isinstance(reference, str) and reference:
                    found.add(reference)
                elif isinstance(reference, dict):
                    nested_id = reference.get("evidence_id")
                    if isinstance(nested_id, str) and nested_id:
                        found.add(nested_id)
        return found


def build_dry_run_report(
    chunks: list[EmbeddingChunk],
    *,
    paper_id: str,
    source_file: str,
    registry_embedding_status: str,
) -> dict[str, Any]:
    """Summarize planned embedding work without generating vectors."""

    evidence_ids = sorted({item for chunk in chunks for item in chunk.evidence_ids})
    by_group: dict[str, int] = {}
    for chunk in chunks:
        group = chunk.chunk_id.removeprefix(f"{paper_id}-").rsplit("-", 1)[0]
        by_group[group] = by_group.get(group, 0) + 1
    return {
        "paper_id": paper_id,
        "mode": "dry_run",
        "source_file": source_file,
        "registry_embedding_status": registry_embedding_status,
        "chunk_count": len(chunks),
        "chunks_by_knowledge_group": by_group,
        "evidence_bound_chunk_count": len(chunks),
        "unique_evidence_ids": len(evidence_ids),
        "total_text_chars": sum(len(chunk.text) for chunk in chunks),
        "adapter_calls": 0,
        "vectors_generated": 0,
        "vector_store_written": False,
        "status": "ready_for_embedding" if chunks else "no_evidence_linked_knowledge",
    }
