# Project State

## Project

Ga2O3-Paper-Learning-System

## Current Phase

Phase 1.5D-2C completed — B01 Benchmark Evaluator v1 and milestone archive

## Current Architecture

```text
PDF
→ MinerU 4.0.7
→ docvortex.middle 2.0 middle_json (preferred future input)
→ MinerUAdapter
→ Unified Document Schema 0.2 + Evidence
→ future RAGAnythingAdapter
→ content_list
→ RAG-Anything / LightRAG
```

The existing Markdown/raw-output adapter path remains operational as a fallback. MinerUAdapter v2 has not been implemented.

## Completed

- Project and Python environments initialized
- MinerU 4.0.7 isolated environment installed and frozen
- Parser interface, adapter boundary, and Raw Output contract defined
- Paper library structure and stable Paper IDs established
- P001 imported, parsed, analyzed, and converted through MinerUAdapter v1
- P001 Figure-caption mapping and Scientific Figure filtering implemented
- P001 Figure-to-Text evidence relationships implemented
- Supplementary Figure references classified
- Formula assets mapped to Equations
- P001 Table detection and Document integrity validation completed
- Repeated publisher/header/footer boilerplate filtering implemented
- Document Schema 0.2 stabilized
- Typed `Evidence`, `FigureTextRelation`, and `EquationMetadata` added
- B01 identity and SHA256 registered
- B01 Ground Truth v1 manually authored
- B01 MinerU Raw Output manually generated
- B01 Layer A Benchmark Evaluator v1 implemented
- B01 machine-readable result and report generated
- RAG-Anything source interface review completed

## Environment

- OS: Windows 11
- Python: 3.12.7
- Main environment: `.venv`
- MinerU environment: `.venv-mineru`
- MinerU: 4.0.7
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU
- CUDA: 12.6

## Document Schema

- Version: 0.2
- Status: stable for the current Pilot milestone
- Evidence contract: typed `Evidence` plus backward-compatible `source_reference`
- Typed relations: `FigureTextRelation`
- Equation metadata: `EquationMetadata`

## P001 Status

- Role: Pilot / Integration Test Paper
- PDF: `data/papers/P001.pdf`
- Raw Output: `data/parsed/P001/mineru/raw/`
- Conversion: `MinerUAdapter.convert()`
- Pages: 12
- Sections: 10
- TextBlocks: 156
- Figures: 6
- Equations: 6
- Tables: 0
- FigureTextRelations: 40
- Validation: `PASS_WITH_KNOWN_ISSUES`

## B01 Status

- Role: Primary Parser Benchmark Case
- Title: Mg-doped α-Ga2O3 Nanorods for the Construction of Photoelectrochemical-Type Self-Powered Solar Blind UV Photodetectors and Underwater Imaging Application
- Journal: Advanced Science
- Year: 2025
- DOI: `10.1002/advs.202413074`
- PDF: `data/benchmark/B01/B01.pdf`
- SHA256: `71D5B029EA9928A261DB783597B00F06A48B156122DB69AE3F83D1B8275E9E7E`
- Ground Truth: `data/benchmark/B01/B01_GROUND_TRUTH.yaml`
- Raw Middle JSON: `data/parsed/B01/mineru/raw/middle_json/B01.json`
- Raw schema: `docvortex.middle` 2.0
- Benchmark result: `data/benchmark/B01/B01_BENCHMARK_RESULT.json`
- Benchmark report: `docs/B01_BENCHMARK_REPORT.md`

Ground Truth v1 summary:

- Pages: 10
- Main Sections: 4
- Experimental subsections: 4
- Scientific Figures: 5
- Equations: 7
- Main-text Tables: 0

Layer A benchmark metrics:

| Category | Precision | Recall | F1 | Counts |
|---|---:|---:|---:|---|
| Scientific Figures | 83.33% | 100% | 90.91% | TP 5 / FP 1 / FN 0 |
| Equations | 75% | 85.71% | 80% | TP 6 / FP 2 / FN 1 |
| Pages | 100% | 100% | 100% | 10/10 |
| Captions | 100% | 100% | 100% | 5/5 |
| Main Sections | 44.44% | 100% | 61.54% | 4 matched plus 5 ancillary titles |
| Main-text Tables | 100% | 100% | 100% | GT 0 / Predicted 0 |

All four Experimental subsections matched. Layer B / Unified Document evaluation is not yet implemented.

## Architectural Findings

MinerU 4.0.7 `middle_json` (`docvortex.middle` schema 2.0) exposes typed structures including `header`, `footer`, `page_footnote`, `paragraph_title`, `equation`, `image`, `image_caption`, and `doc_title`.

Decision for MinerUAdapter v2:

- Primary input: `middle_json`
- Fallback: existing Markdown + legacy Raw Output route

This decision is planned only; no Adapter v2 implementation exists yet.

## RAG-Anything Evaluation

- Source: `F:\Learning\open-source-research\RAG-Anything`
- Status: `ADOPT CANDIDATE`
- License: MIT
- Python: >= 3.10
- Confirmed direct pre-parsed `content_list` insertion through `insert_content_list()`
- Confirmed multimodal item support: text, image, table, equation
- Confirmed relevant fields: `page_idx`, `img_path`, `image_caption`, `table_caption`, `latex`, `doc_id`
- Parser support includes MinerU, Docling, and PaddleOCR
- Backend: LightRAG
- Not installed, not integrated, and not formally adopted

RAG-Anything is a future multimodal retrieval/indexing layer, not the project's factual source of truth. Unified Document + Evidence Store remains authoritative.

## Known Issues

1. P001 PDF page 11 reference fragment is misclassified by MinerU as a Formula block.
2. B01 Equation (2), `Ga(OH)3 → GaOOH + H2O`, is missing from MinerU Raw Equation blocks.
3. The Advanced Science publisher logo is misclassified as an image on B01 page 1 and as Equations on pages 9 and 10.
4. Table parsing has not been stress-tested on a paper containing a genuine main-text Table.
5. MinerUAdapter v2 is not implemented.
6. B01 Ground Truth YAML currently has detailed Figure records for Figures 1–3 while the manually confirmed summary contains five Scientific Figures.
7. Layer B benchmark and aggregate pass threshold are not yet defined.

## Key Git Commit

- `2f39f7962e0e37c4a1c5a431604fcc2a34411aff` — Add B01 parser benchmark evaluator

## Next Planned Phase

Phase 1.5D-3 — MinerUAdapter v2

Priority sequence:

1. Convert `docvortex.middle` 2.0 to Unified Document while preserving Markdown fallback.
2. Re-evaluate B01 at the Adapter / Layer B level.
3. Select 1–2 additional Pilot papers, including at least one genuine main-text Table paper.
4. Freeze Parser v1.
5. Create an isolated RAG-Anything environment and implement `RAGAnythingAdapter`.
6. Continue Translation QA and Knowledge Card work.
