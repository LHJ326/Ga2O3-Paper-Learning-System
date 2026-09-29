# Ga2O3 Paper Learning System
# AI Session Memory

## TABLE-LIGHT-2 Milestone

- Generic trigger reasons: `TABLE_BODY_MISSING`, `TABLE_MISCLASSIFIED_AS_IMAGE`.
- B02 automatic regions: page 8 right-column crop and page 11 uncaptioned-image union.
- External ordinary PP-OCR was invoked only for the two regions; no MinerU rerun.
- Runtime artifacts: `data/parsed/B02/light_ocr/runtime_raw/`; deterministic rerun hit both caches.
- Runtime reconstruction: Table I 10×3; Table II 14×7; detection 2/0/0.
- Crop-pixel and PDF-space bboxes are both retained in token/cell Evidence.
- Frozen A/B results, Ground Truth, MinerU Raw, and TABLE-LIGHT-1 fixtures were not modified.
- Known issue: runtime crop OCR text is below frozen PoC quality; do not GT-correct it.
- Next authorized candidate is `OCR-ENV-CLEANUP`; it has not been executed.

## 1. Project Goal

Build a long-lived AI learning system for Ga2O3 optoelectronic-device research papers:

```text
PDF
→ parsing
→ evidence-preserving Unified Document
→ Knowledge Card
→ multimodal RAG
→ AI research assistant
```

The project is benchmark-driven: establish independent Ground Truth before judging or optimizing parser output. Important state must live in repository documents, not chat memory.

## 2. Current Architecture

```text
PDF
→ MinerU 4.0.7
→ Raw Output
   ├── primary candidate: docvortex.middle 2.0 middle_json
   └── fallback: Markdown + legacy Raw Output
→ MinerUAdapter
→ Unified Document Schema 0.2
→ Evidence Store / Knowledge Layer
→ future RAGAnythingAdapter
→ content_list
→ RAG-Anything / LightRAG
```

Unified Document + Evidence Store is the factual layer. RAG-Anything may index and retrieve multimodal content, but must not replace the evidence model or discard provenance.

## 3. Environment

- Project: `<PROJECT_ROOT>`
- OS: Windows 11
- Python: 3.12.7
- Main environment: `.venv`
- MinerU environment: `.venv-mineru`
- MinerU: 4.0.7
- GPU: RTX 4060 Laptop GPU
- CUDA: 12.6

Do not reinstall environments, rerun completed PDF parsing, or modify Raw Output unless a future task explicitly authorizes it.

## 4. Completed Milestones

- Project/environment initialization
- Parser interface and adapter architecture
- Paper library and Raw Output contract
- P001 import, parsing, Raw analysis, and MinerUAdapter v1 conversion
- Figure-caption mapping and Scientific Figure filtering
- Figure-to-Text evidence chain and supplementary-reference classification
- Equation structural mapping, Table detection, integrity validation, and boilerplate filtering
- Document Schema 0.2 stabilization with typed `Evidence`, `FigureTextRelation`, and `EquationMetadata`
- B01 identity registration and independent Ground Truth v1
- B01 MinerU 4.0.7 Raw parsing by the user
- Layer A B01 Benchmark Evaluator v1
- MinerUAdapter v2 with `docvortex.middle` 2.0 primary input and legacy fallback
- B01 Layer B benchmark: 5 Figures, 6 Equations, and 0 Tables after adapter filtering
- Initial RAG-Anything source/interface review

## 5. P001 Status

- Role: Pilot / Integration Test Paper
- PDF: `data/papers/P001.pdf`
- Raw: `data/parsed/P001/mineru/raw/`
- Adapter: `MinerUAdapter.convert()` using the current Markdown/legacy route
- Schema: 0.2
- Pages: 12
- Sections: 10
- TextBlocks: 156
- Figures: 6
- Equations: 6, all image-only
- Tables: 0
- FigureTextRelations: 40
- Validation: `PASS_WITH_KNOWN_ISSUES`

Do not rerun MinerU on P001. Known P001 issue: a page-11 reference fragment is misclassified as a Formula block.

## 6. B01 Ground Truth and Benchmark

- Role: Primary Parser Benchmark Case
- PDF: `data/benchmark/B01/B01.pdf`
- SHA256: `71D5B029EA9928A261DB783597B00F06A48B156122DB69AE3F83D1B8275E9E7E`
- DOI: `10.1002/advs.202413074`
- Ground Truth: `data/benchmark/B01/B01_GROUND_TRUTH.yaml`
- Raw Middle JSON: `data/parsed/B01/mineru/raw/middle_json/B01.json`
- Result: `data/benchmark/B01/B01_BENCHMARK_RESULT.json`
- Report: `docs/B01_BENCHMARK_REPORT.md`

Ground Truth v1:

- 10 pages
- 4 main sections
- 4 Experimental subsections
- 5 Scientific Figures
- 7 Equations
- 0 main-text Tables

Layer A results:

- Figures: TP 5 / FP 1 / FN 0; precision 83.33%, recall 100%, F1 90.91%
- Equations: TP 6 / FP 2 / FN 1; precision 75%, recall 85.71%, F1 80%
- Pages: 10/10, 100% coverage
- Captions: 5/5, 100% coverage
- Main sections: 4/4 matched
- Experimental subsections: 4/4 matched
- Tables: GT 0 / predicted 0

Raw errors manually confirmed by the user:

- Figure FP: Advanced Science Open Access publisher logo on page 1
- Equation FPs: publisher logo on pages 9 and 10
- Equation FN: Equation (2), `Ga(OH)3 → GaOOH + H2O`, on page 2

Key commit: `2f39f7962e0e37c4a1c5a431604fcc2a34411aff`.

## 7. Schema and Adapter Decisions

- Schema version 0.2 is stable for the current Pilot node.
- Keep `source_reference` backward compatible.
- Preserve typed Evidence and relationships through every conversion.
- Do not bind project architecture directly to a parser's native schema.
- MinerUAdapter v2 uses `docvortex.middle` 2.0 `middle_json` as primary input.
- Retain the existing Markdown route as fallback.
- Do not implement v2 during archival/recovery tasks.

## 8. RAG-Anything Assessment

- Local source: `<EXTERNAL_RESEARCH_ROOT>\RAG-Anything`
- Status: `ADOPT CANDIDATE`, not adopted
- Python >= 3.10
- MIT License
- Core dependencies observed: `huggingface_hub`, `lightrag-hku<1.5`, `mineru[core]>=3.4.1`, `tqdm`
- Supports MinerU, Docling, and PaddleOCR
- `insert_content_list()` permits direct pre-parsed insertion
- Standard multimodal items: text, image, table, equation
- Relevant fields: 0-based `page_idx`, absolute `img_path`, `image_caption`, `table_caption`, `latex`, custom `doc_id`
- LightRAG backend

Not yet verified:

- Installation and dependency compatibility
- Real B01 insertion
- Evidence round-trip
- Citation accuracy
- Image-only Equation behavior

Do not clone/download again and do not modify the external source during project tasks.

## 9. User / Codex Working Agreement

User handles:

- large dependency installation
- open-source clone/download
- model downloads
- CUDA / PyTorch / Docker operations
- large file copying
- simple commands and tests when requested

Codex handles:

- architecture
- adapters
- schema
- benchmarks
- integration code
- automated tests
- status and handover documentation

Preferences:

- If a manual operation can be completed with one copy/paste, provide the full content once.
- When giving multiple commands, place every command in its own code block.
- Pause for user confirmation before large downloads, GPU stacks, Docker, or files over 500 MB.

## 10. Known Issues

1. P001 page-11 reference fragment Formula false positive.
2. B01 Equation (2) Raw false negative.
3. B01 publisher logo image/Equation false positives.
4. No stress test yet with a genuine main-text Table.
5. B01 detailed Figure annotations currently cover Figures 1–3 while the confirmed summary contains five.
6. No aggregate benchmark pass threshold is defined yet.

## 11. Resume Protocol

On every future session:

1. Read `docs/AI_SESSION_MEMORY.md`.
2. Read `docs/PROJECT_STATE.md`.
3. Run `git status` before changing anything.
4. Do not reinitialize the project or reinstall environments.
5. Do not rerun MinerU on P001 or B01 unless explicitly authorized.
6. Preserve all PDFs, Ground Truth, Raw Output, and Evidence links.

## 12. Next Priority

Add 1–2 Pilot papers including a genuine main-text Table case, freeze Parser v1,
and only then begin the isolated RAG-Anything integration pilot.
