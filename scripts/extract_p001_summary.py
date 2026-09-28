"""Run the real DeepSeek Summary strategy for P001 only."""

from __future__ import annotations

from src.knowledge.p001_pipeline import PAPERS_ROOT, P001_RAW
from src.knowledge.p001_summary import P001SummaryExtractor
from src.knowledge.schema import PROJECT_ROOT, load_knowledge_schema
from src.llm import DeepSeekLLMAdapter
from src.parser.adapters.mineru_adapter import MinerUAdapter


def main() -> None:
    document = MinerUAdapter().convert(P001_RAW)
    result = P001SummaryExtractor(DeepSeekLLMAdapter()).run(
        document=document,
        schema=load_knowledge_schema(),
        output_dir=PAPERS_ROOT / "P001" / "knowledge",
        source_document=P001_RAW.relative_to(PROJECT_ROOT).as_posix(),
        metadata={"document_id": document.document_id},
    )
    print(f"API response status: {result.api_response_status}")
    print(f"Evidence count: {result.evidence_count}")
    print(f"Input characters: {result.input_chars}")
    print(f"Output characters: {result.output_chars}")
    print(f"Summary: {result.summary_path}")
    print(f"Prompts: {result.prompts_path}")
    print(f"Responses: {result.responses_path}")
    print(f"Run manifest: {result.run_manifest_path}")


if __name__ == "__main__":
    main()
