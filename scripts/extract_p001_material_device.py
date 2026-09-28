"""Dry-run and execute P001 Material/Device-only DeepSeek extraction."""

from __future__ import annotations

import argparse

from src.knowledge.material_device_extraction import P001MaterialDeviceExtractor
from src.knowledge.p001_pipeline import PAPERS_ROOT, P001_RAW
from src.knowledge.parameter_schema import load_parameter_schema
from src.llm import DeepSeekLLMAdapter
from src.parser.adapters.mineru_adapter import MinerUAdapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", help="print bounded input statistics only"
    )
    args = parser.parse_args()
    document = MinerUAdapter().convert(P001_RAW)
    schema = load_parameter_schema()
    extractor = P001MaterialDeviceExtractor(DeepSeekLLMAdapter())
    prepared = extractor.prepare(document=document, schema=schema)
    print(f"Selected evidence count: {len(prepared.selected_evidence)}")
    print(f"Chunk count: {len(prepared.chunks)}")
    print(f"Max prompt characters: {prepared.max_prompt_chars}")
    print(f"Total estimated prompt characters: {prepared.total_prompt_chars}")
    if args.dry_run:
        return
    result = extractor.run(
        document=document,
        schema=schema,
        output_dir=PAPERS_ROOT / "P001" / "knowledge",
        papers_root=PAPERS_ROOT,
        prepared=prepared,
    )
    print(f"API response status: success")
    print(f"API calls: {result.api_calls}")
    print(f"Output characters: {result.output_chars}")
    print(f"Extracted fields: {', '.join(result.extracted_fields) or 'none'}")
    print(f"Evidence-supported fields: {result.evidence_supported_fields}")
    print(f"Unsupported fields: {result.unsupported_fields}")
    print(f"Review required: {result.review_required}")
    print(f"Parameters: {result.parameters_path}")


if __name__ == "__main__":
    main()
