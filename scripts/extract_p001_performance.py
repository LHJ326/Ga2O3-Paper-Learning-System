"""Dry-run and execute P001 Performance-only extraction."""

from __future__ import annotations

import argparse

from src.knowledge.p001_pipeline import PAPERS_ROOT, P001_RAW
from src.knowledge.performance_extractor import PerformanceExtractor
from src.knowledge.performance_pipeline import PerformanceExtractionPipeline
from src.knowledge.performance_schema import load_performance_schema
from src.knowledge.performance_validator import PerformanceValidator
from src.knowledge.performance_writer import PerformanceWriter
from src.llm import DeepSeekLLMAdapter
from src.parser.adapters.mineru_adapter import MinerUAdapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    document = MinerUAdapter().convert(P001_RAW)
    schema = load_performance_schema()
    extractor = PerformanceExtractor(DeepSeekLLMAdapter())
    prepared = extractor.prepare(document=document, schema=schema)
    print(f"Selected evidence count: {len(prepared.selected_evidence)}")
    print(f"Chunk count: {len(prepared.chunks)}")
    print(f"Max prompt characters: {prepared.max_prompt_chars}")
    print(f"Total estimated prompt characters: {prepared.total_prompt_chars}")
    if args.dry_run:
        return
    validator = PerformanceValidator(schema)
    result = PerformanceExtractionPipeline(
        extractor=extractor,
        validator=validator,
        writer=PerformanceWriter(validator=validator, papers_root=PAPERS_ROOT),
    ).run(
        document=document,
        schema=schema,
        output_dir=PAPERS_ROOT / "P001" / "knowledge",
        prepared=prepared,
    )
    print("API response status: success")
    print(f"API calls: {result.api_calls}")
    print(f"Input characters: {result.input_chars}")
    print(f"Output characters: {result.output_chars}")
    print(f"Extracted fields: {result.extracted_field_count}")
    print(f"Null fields: {result.null_field_count}")
    print(f"Evidence coverage: {result.evidence_coverage:.1%}")
    print(f"Performance: {result.performance_path}")


if __name__ == "__main__":
    main()
