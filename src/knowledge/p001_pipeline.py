"""Manual, single-paper entry point for P001 knowledge extraction."""

from __future__ import annotations

from pathlib import Path

from src.llm import DeepSeekLLMAdapter
from src.parser.adapters.mineru_adapter import MinerUAdapter

from .pipeline import KnowledgeExtractionPipeline
from .schema import PROJECT_ROOT, load_knowledge_schema
from .strategy_extractor import StrategyKnowledgeExtractor
from .validator import KnowledgeValidator
from .writer import KnowledgeWriter


PAPER_ID = "P001"
P001_RAW = PROJECT_ROOT / "data" / "parsed" / PAPER_ID / "mineru" / "raw"
PAPERS_ROOT = PROJECT_ROOT / "data" / "papers"


def run_p001() -> dict[str, Path]:
    """Extract P001 only; uses preserved output and never invokes MinerU."""
    paper_object = PAPERS_ROOT / PAPER_ID
    if not paper_object.is_dir():
        raise FileNotFoundError(f"P001 Paper Object does not exist: {paper_object}")
    document = MinerUAdapter().convert(P001_RAW)
    schema = load_knowledge_schema()
    validator = KnowledgeValidator(schema)
    pipeline = KnowledgeExtractionPipeline(
        extractor=StrategyKnowledgeExtractor(DeepSeekLLMAdapter()),
        validator=validator,
        writer=KnowledgeWriter(validator=validator, papers_root=PAPERS_ROOT),
    )
    return pipeline.run(
        paper_id=PAPER_ID,
        document=document,
        schema=schema,
        source_document=P001_RAW.relative_to(PROJECT_ROOT).as_posix(),
        metadata={"document_id": document.document_id},
    )


def main() -> None:
    for name, path in run_p001().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
