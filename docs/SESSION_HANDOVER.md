# Session Handover

## Resume First

The next Agent must read, in this order:

1. `docs/AI_SESSION_MEMORY.md`
2. `docs/PROJECT_STATE.md`
3. Run `git status`

Do not reinitialize the project, reinstall Python/MinerU, rerun P001/B01 parsing, or modify existing Raw Output.

## Current Stable Node

- Document Schema: 0.2
- P001 MinerUAdapter v1 conversion: stable Pilot node with known issues
- B01 Layer A Benchmark Evaluator v1: complete
- Full test suite at archive time: 62 passed
- Key benchmark commit: `2f39f7962e0e37c4a1c5a431604fcc2a34411aff`
- RAG-Anything: `ADOPT CANDIDATE`, not installed or integrated

## Architecture

```text
PDF
→ MinerU
→ middle_json (docvortex.middle 2.0)
→ MinerUAdapter v2
→ Unified Document + Evidence Store
→ RAGAnythingAdapter
→ content_list
→ RAG-Anything / LightRAG
```

The existing Markdown adapter route must remain a fallback. RAG-Anything is an indexing/retrieval layer, not the authoritative fact store.

## Important Files

- `docs/AI_SESSION_MEMORY.md`
- `docs/PROJECT_STATE.md`
- `docs/B01_BENCHMARK_REPORT.md`
- `docs/OPEN_SOURCE_REUSE_STATUS.md`
- `data/benchmark/B01/B01_GROUND_TRUTH.yaml`
- `data/benchmark/B01/B01_BENCHMARK_RESULT.json`
- `data/parsed/B01/mineru/raw/middle_json/B01.json`
- `src/benchmark/evaluator.py`
- `src/parser/adapters/mineru_adapter.py`
- `src/schema/document.py`

## Next Recommended Phase

Phase 1.5D-3 — MinerUAdapter v2

Goal:

```text
docvortex.middle 2.0
→ Unified Document
```

Requirements:

- preserve typed Evidence and Raw locators
- map typed header/footer/title/image/caption/Equation structures conservatively
- retain Markdown fallback
- do not infer missing scientific content
- use B01 for Layer B evaluation

## Planned Sequence After v2

1. Re-evaluate B01 Adapter / Layer B output.
2. Add 1–2 additional Pilot papers; at least one must contain a genuine main-text Table.
3. Freeze Parser v1.
4. Prepare an isolated RAG-Anything environment with user approval.
5. Implement `RAGAnythingAdapter` and test Evidence round-trip/citation accuracy.
6. Continue Translation QA and Knowledge Card work.
