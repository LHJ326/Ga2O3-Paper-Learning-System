"""Dry-run and execute P001 Mechanism-only extraction."""

from __future__ import annotations

import argparse

from src.knowledge.mechanism_extractor import MechanismExtractor
from src.knowledge.mechanism_pipeline import MechanismExtractionPipeline
from src.knowledge.mechanism_schema import load_mechanism_schema
from src.knowledge.mechanism_validator import MechanismValidator
from src.knowledge.mechanism_writer import MechanismWriter
from src.knowledge.p001_pipeline import PAPERS_ROOT, P001_RAW
from src.llm import DeepSeekLLMAdapter
from src.parser.adapters.mineru_adapter import MinerUAdapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    document = MinerUAdapter().convert(P001_RAW)
    schema = load_mechanism_schema()
    extractor = MechanismExtractor(DeepSeekLLMAdapter())
    prepared = extractor.prepare(document=document, schema=schema)
    low, high = prepared.estimated_input_cost_usd
    print(f"Selected evidence count: {len(prepared.selected_evidence)}")
    print(f"Estimated DeepSeek calls: {len(prepared.chunks)}")
    print(f"Max prompt characters: {prepared.max_prompt_chars}")
    print(f"Total prompt characters: {prepared.total_prompt_chars}")
    print(f"Estimated input tokens: {prepared.estimated_input_tokens}")
    print(f"Estimated input fee (USD, cache-miss off-peak to peak): {low:.6f}-{high:.6f}")
    print("Estimated fee excludes output tokens and is not the final billed amount.")
    if args.dry_run:
        return
    validator = MechanismValidator(schema)
    result = MechanismExtractionPipeline(
        extractor=extractor, validator=validator,
        writer=MechanismWriter(validator=validator, papers_root=PAPERS_ROOT),
    ).run(
        document=document, schema=schema,
        output_dir=PAPERS_ROOT / "P001" / "knowledge", prepared=prepared,
    )
    print("API response status: success")
    print(f"API calls: {result.api_calls}")
    print(f"Input characters: {result.input_chars}")
    print(f"Output characters: {result.output_chars}")
    print(f"Extracted fields: {result.extracted_field_count}")
    print(f"Null fields: {result.null_field_count}")
    print(f"Mechanism: {result.mechanism_path}")


if __name__ == "__main__":
    main()
