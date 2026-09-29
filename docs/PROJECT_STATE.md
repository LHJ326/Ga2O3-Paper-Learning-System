# Project State

## Phase 5.3 Embedding Layer Completed

The project now has a model-independent embedding foundation under
`src/embedding/`. `EmbeddingChunk` preserves `chunk_id`, `paper_id`, source
Paper Object path, Evidence IDs, and text. `PaperObjectChunker` produces
deterministic chunks only from evidence-linked Summary, Parameter, Performance,
and Mechanism knowledge already present in a Paper Object; unknown Evidence
references fail validation instead of being silently indexed.

`EmbeddingAdapter` defines the future `embed(texts) -> vectors` boundary without
selecting a provider or model. `LocalVectorStore` supports validated vector
addition, cosine-similarity search, and atomic JSON persistence. No embedding
API, model, Vector Database, or RAG system is connected.

The P001 dry-run generated `data/papers/P001/embedding_report.yaml`: 149 chunks
across four knowledge groups, 33 unique Evidence IDs, and 34,729 total text
characters. Adapter calls and generated vectors are both zero. Registry
`embedding_status` remains `pending`; the dry-run reads Registry state but does
not mutate it.

## Phase 5.2 Paper Registry Upgrade Completed

The Paper Registry is upgraded to version 2.0 with explicit lifecycle fields:
`metadata_status`, `knowledge_status`, `object_status`, `embedding_status`, and
`rag_status`. `RegistryManager` provides validated loading, atomic status
updates, pending-task queries, and stage-specific completed-paper queries.

The Batch Paper Object Pipeline now consults Registry state before selecting
the next task while preserving its legacy artifact/status fallback for
unregistered papers. Reports include per-paper and aggregate completed/pending
stage counts. P001 is registered from existing facts with metadata, knowledge,
and object stages completed; embedding and RAG remain pending.

No Paper Object content or knowledge extraction logic was changed, and the
pipeline remains dry-run by default with no automatic DeepSeek call.

## Phase 5.1 Batch Paper Object Pipeline Completed

The project now has a dry-run-first batch coordinator under `src/batch/`.
It discovers P-series Paper Object directories and legacy P-series PDF files,
resolves metadata/knowledge/object readiness, and writes
`data/papers/batch_report.yaml` with completed, pending, and failed counts.

Metadata-incomplete papers stop before knowledge work. Knowledge-incomplete
papers receive a planned `run_knowledge_pipeline` action, but no model is called
unless a caller explicitly injects a knowledge executor and disables dry-run.
Papers with complete knowledge can reuse the existing `PaperObjectBuilder` when
execution is explicitly enabled. Existing P001 logic is unchanged.

The first repository dry-run discovered P001 as fully completed:
`total=1`, `completed=1`, `pending=0`, `failed=0`.

## Phase 4 Completed

Phase 4 has completed the P001 single-paper knowledge-engineering loop from
parsed PDF Evidence through validated Summary, Parameters, Performance,
Mechanism, and final Paper Object generation. The canonical phase summary is
`docs/PHASE4_FINAL_REPORT.md`; the finalized object is
`data/papers/P001/paper_object.yaml` with 100% Evidence coverage.

The next planned stage is Phase 5 — Multi-Paper Knowledge System. Phase 5 has
not started.

## Phase 4.4.4 Paper Object Finalization Completed

P001 Summary, Material/Device Parameters, Performance, Mechanism, Evidence, and
Validation are now assembled into the standard
`data/papers/P001/paper_object.yaml` artifact. The object embeds each source
knowledge artifact without rewriting extracted values and exposes a unified,
deduplicated Evidence index containing 33 traceable records. All 33 referenced
Evidence IDs resolve with 1-based page, source element type, source locator, and
quote, yielding 100% Evidence coverage.

Paper identity is loaded only from existing metadata. Missing `authors` and
`doi` remain null. The aggregate review status is `review_required`, preserving
8 existing Summary, Performance, and Mechanism warnings. The builder does not
call an LLM, rerun MinerU, infer missing bibliographic fields, or alter any
upstream knowledge artifact.

## Phase 4.4.3-B3 Mechanism Extraction Completed — Review Required

P001 Mechanism extraction now uses a dedicated schema, task-specific Evidence
selector, bounded prompt chunks, strict locator validation, and atomic knowledge
writing. The real run selected 23 Unified Document Evidence records, produced 6
prompts (66,423 input characters), and made 6 successful DeepSeek calls.

Seven of eight mechanism fields were populated; `gain_mechanism` remains null.
All populated observations contain Evidence ID, 1-based page, source element
type, confidence, and review status. Evidence closure is 100%. The overall run
is `review_required` because several model observations explicitly requested
review; no extracted content was silently corrected or deleted.

The validated artifact is `data/papers/P001/knowledge/mechanism.yaml`, with
prompt, response, and run provenance beside it. No MinerU, parser, metadata,
ingestion, Summary, Material/Device, or Performance process was rerun.

## Phase 4.4.3-B2 Performance Extraction Completed — Review Required

P001 Performance extraction uses a separate task schema and Evidence selector.
The bounded run selected 20 Unified Document Evidence records, produced 5
prompts (63,061 input characters), and made 5 successful DeepSeek calls. It
wrote `data/papers/P001/knowledge/performance.yaml` plus JSONL prompt/response
provenance and `performance_extraction_run.yaml`.

Six of fifteen performance fields were populated and all structural records
passed type, unit, 1-based page, source-element, and Evidence-closure checks.
A non-destructive semantic keyword check marked the run `review_required`:
`on_off_ratio` value `81%` cites E00169, whose nearby value context describes
W.R./S.R. rather than an unambiguous on/off or switching ratio. The model result
and raw response were preserved without deletion or automatic correction.

No parser, MinerU Adapter, metadata, ingestion, Evidence-base, Material/Device,
Summary, or Mechanism extraction behavior was changed.

## Phase 4.4.3-B1 Material + Device Extraction Completed

P001 Material/Device extraction now uses the reviewed task-specific Evidence
Selector as its only model input. The bounded run selected 23 Unified Document
Evidence records, produced 4 prompts (55,267 total input characters), and made
4 successful DeepSeek calls. The model output contained 9 populated
Material/Device fields; all 9 closed against existing 1-based Evidence records,
with no unsupported fields or validation warnings.

The validated knowledge artifact is
`data/papers/P001/knowledge/device_parameters.yaml`. Prompt, response, and run
provenance are stored beside it as `device_extraction_prompts.jsonl`,
`device_extraction_responses.jsonl`, and `device_extraction_run.yaml`.
Performance, mechanism, and comparison groups remain null. No Summary or
MinerU rerun occurred, and parser, metadata, ingestion, benchmark, and table
recovery components were unchanged.

## Phase 4.4.3-A Parameter Extraction Framework Completed

The Ga2O3 photodetector knowledge layer now has a dedicated Parameter Schema
covering material, device, performance, mechanism, and comparison fields. Every
field is nullable and may otherwise contain a structured object or a list of
structured observations, so absent paper data is never fabricated.

The model-neutral framework provides schema loading, a parameter-only Prompt
Builder and extractor interface, strict Paper ID/Evidence/page/unit validation,
validated YAML writing, and extraction-pipeline orchestration. Tests use only
`MockLLMAdapter`; no real paper parameters or model calls were produced.

This phase does not change parser, metadata, ingestion, MinerU Adapter, or table
recovery code and does not introduce RAG, Vector Database, Embedding, or Agent
components.

## Phase 4.4.2-D1.5 Summary Knowledge Validator Completed

The existing PDF → Unified Document → DeepSeek Summary → Knowledge flow now
has a deterministic post-generation quality layer. It validates the required
scientific-summary structure, closes every Summary claim against prompt
Evidence with page and source-element locators, and emits warnings for broadly
implausible Ga2O3 photodetector parameters without rewriting extracted facts.

Validation artifacts are written beside each paper's existing knowledge:
`quality_report.yaml` provides the decision summary and
`validation_log.json` retains detailed checks. P001 is the first real case.
Its current report intentionally requires review because the Summary lacks
separate Material/System, Device Structure, and Mechanism sections; this result
does not trigger another LLM call or alter `summary.md`.

This phase does not introduce RAG, Vector Database, Embedding, Agent, parser,
metadata, ingestion, MinerU Adapter, or table-recovery changes.

## Phase 4.4.2-A Knowledge Extraction Framework Completed

The project now has a model-independent knowledge engineering boundary under
`src/knowledge/`:

- Schema Loader combines the Core template with an optional Domain Extension.
- `KnowledgeExtractor` defines an abstract input/output contract without a
  provider implementation or API dependency.
- `KnowledgeValidator` validates required Core fields, Domain field types,
  Paper ID consistency, 1-based Evidence records, and closed evidence references.
- `KnowledgeWriter` validates before writing `core.yaml`, `domain.yaml`,
  `summary.md`, `key_points.md`, and `device_parameters.yaml` inside an existing
  Paper Object.
- Versioned prompt contracts cover summaries, device parameters, and mechanisms
  but are not connected to a model runtime.

This is an engineering framework only. It does not call an LLM, generate
knowledge for an actual paper, update `knowledge_ready`, or connect Embedding,
RAG, Vector Database, or Agent components.

## Phase 4.4.1 Knowledge Schema Design Completed

The research knowledge layer now follows a Core Schema + Domain Extension
architecture. The Core Schema defines paper identity, research problem,
methodology, results, innovation, limitations, and evidence traceability for any
scientific paper. Domain-specific vocabulary remains outside Core.

The first Domain Extension is
`data/domains/semiconductor/ga2o3/schema.yaml`, defining evidence-linked fields
for material, crystal phase, doping, substrate, device structure, fabrication,
optical performance, electrical performance, mechanism, and comparison.

Each new Paper Object now includes knowledge templates for structured Core and
Domain YAML plus human-readable summary and key-point views. This phase defines
schemas and empty templates only; it does not generate knowledge, call an LLM,
or connect Embedding, RAG, Vector Database, or Agent components.

## Phase 4.3 Batch Paper Ingestion Completed

The project now scans a local PDF directory in deterministic filename order,
allocates collision-free P-series IDs across the Registry, legacy flat PDFs,
and Paper Object directories, and creates one standard object per imported PDF:

```text
PDF input directory
→ scan PDFs
→ allocate paper_id
→ data/papers/<paper_id>/{source,metadata,parsed,assets,knowledge}
→ status.yaml
→ registry.yaml
→ optional same-stem RIS/BibTeX metadata import
```

PDFs are copied rather than moved. A same-stem `.ris` or `.bib` file is
preserved under the object's `metadata/` directory and normalized through the
Phase 4.2 pipeline into `data/metadata/<paper_id>.yaml`. Successful metadata
import synchronizes both Registry and object status. Ambiguous dual sidecars are
rejected before an object is created.

The command-line entry point is `python -m src.ingestion <PDF_DIRECTORY>`.
This ingestion phase does not invoke MinerU, parse PDFs, or enter RAG,
Embedding, Vector Database, or Agent work.

## Phase 4.2 Metadata Pipeline Completed

The project now imports one `.bib` or `.ris` bibliographic record into the
canonical `data/metadata/<paper_id>.yaml` schema. BibTeX uses the lightweight
`bibtexparser==2.0.1` dependency; RIS uses a small project-owned line parser.

Canonical fields are `paper_id`, `title`, `authors`, `year`, `journal`, `doi`,
`keywords`, and `citation`. Unknown optional values remain null or empty rather
than being fabricated. Import requires an existing Registry record and, on
success, updates `metadata_path` and changes
`processing_status.metadata_ready` from false to true while preserving other
lifecycle flags. Legacy scalar Registry status values are upgraded when that
record is imported.

The metadata schema is documented in `docs/METADATA_SCHEMA.md`. This phase does
not modify PDF parsing, benchmarks, MinerUAdapter, table recovery, or any RAG,
Embedding, Vector Database, or Agent layer.

## Phase 4.1.5 Paper Object Schema Completed

The standard directory contract for one newly imported paper is now defined by
`data/papers/TEMPLATE/`:

```text
data/papers/<paper_id>/
├── status.yaml
├── source/
├── metadata/
├── parsed/
├── assets/
└── knowledge/
```

- `source/` contains the project-controlled source PDF and explicitly imported
  source records.
- `metadata/` contains normalized bibliographic metadata and provenance.
- `parsed/` contains parser outputs associated with the paper object.
- `assets/` contains derived figures, table crops, and other traceable assets.
- `knowledge/` is reserved for structured Knowledge Cards and related factual
  artifacts; it is not a Vector Database or embedding store.
- `status.yaml` identifies the paper and records each Registry lifecycle stage
  as an explicit boolean.

The template contains no paper identity or fabricated metadata. Existing P001,
B01, B02, benchmark, metadata, and parsed paths remain unchanged and compatible;
their migration is not part of this architecture-only phase.

## Phase 4.1 Paper Registry Started

Phase 4.1 establishes the management layer for batch paper processing. The
initial Registry is `data/papers/registry.yaml`; it defines the canonical paper
record fields and ordered processing lifecycle without inventing records for
papers that have not been explicitly imported.

The current storage layout must remain backward compatible:

- `P001` is a regular library paper with its PDF in `data/papers`, metadata in
  `data/metadata`, and parser output in `data/parsed/P001`.
- `P002` does not currently exist and is not created by this phase.
- `B01` and `B02` are benchmark identities, with PDFs and benchmark metadata in
  `data/benchmark/<ID>` and parser outputs in `data/parsed/<ID>`.
- Existing benchmark, metadata, PDF, and parsed paths are not moved. Registry
  paths are references to those assets, not a replacement storage hierarchy.

This phase is limited to the reliable knowledge-structure foundation. It does
not introduce RAG-Anything, a Vector Database, Embedding, or Agent behavior.

## Phase 3.5 OCR-ENV-CLEANUP Completed

OCR runtime separation and cleanup are complete.

- The former `F:\Learning\open-source-research\PaddleOCR` source checkout was
  removed because it is no longer a runtime dependency.
- The independent ordinary OCR runtime is retained at
  `F:\Learning\open-source-research\ocr-runtime\.venv-ocr`.
- Removed PaddleX models: `PaddleOCR-VL-1.6`, `PP-DocLayoutV3`,
  `PP-LCNet_x1_0_doc_ori`, `PP-LCNet_x1_0_textline_ori`, and `UVDoc`.
- Retained lightweight fallback models: `PP-OCRv6_medium_det` and
  `PP-OCRv6_medium_rec`.
- Python: 3.12.7.
- Main project environment: `.venv`.
- Full test status: 112 passed.

The current default architecture is:

```text
PDF
→ MinerU
→ Unified Document Schema
→ Table Recovery
→ Knowledge Layer
```

When MinerU table extraction fails, generic failure detection invokes the
independent ordinary PaddleOCR runtime for lightweight OCR fallback and then
performs deterministic table reconstruction. PaddleOCR-VL remains an optional
extreme fallback only and is not a default dependency.

## TABLE-LIGHT-2 Completed — Lightweight Table Fallback Runtime

The default fallback now detects missing/misclassified MinerU tables, derives
localized PDF regions, renders with PyMuPDF, invokes configurable external
ordinary PP-OCR, caches raw artifacts, maps crop coordinates back to PDF space,
and reuses TABLE-LIGHT-1 reconstruction. B02 automatically produced Table I
10×3 and Table II 14×7. Runtime Layer C table detection is TP/FP/FN 2/0/0;
frozen Layer A/B and TABLE-LIGHT-1 fixtures are unchanged. Automatic-crop text
accuracy (29/30; 85/98 exact and 86/98 semantic) remains a known tuning issue.
`OCR-ENV-CLEANUP` is next but not started.

## Project

Ga2O3-Paper-Learning-System

## Current Phase

Phase 4.4.2-A Knowledge Extraction Framework completed

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

The existing Markdown/raw-output adapter path remains operational as a fallback.

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
- MinerUAdapter v2 implemented with Evidence-preserving `middle_json` conversion
- B01 Layer B benchmark implemented without changing Layer A
- B01 machine-readable result and report generated
- B02 cross-domain Table stress benchmark Ground Truth finalized as `ready_v1`
- B02 MinerU 4.0.7 Raw Output fingerprints frozen and benchmarked
- B02 Layer A and independent Layer B baseline reports generated
- Lightweight OCR token/bbox model and deterministic spatial Table reconstruction implemented
- B02 Layer C recovered Table I and Table II without changing Layer A/B
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

All four Experimental subsections matched in both layers.

Layer B Adapter output:

- 10 Pages, 9 Sections, 114 TextBlocks, 5 Figures, 6 Equations, 0 Tables
- Figures: TP 5 / FP 0 / FN 0; precision/recall/F1 100%
- Equations: TP 6 / FP 0 / FN 1; precision 100%, recall 85.71%, F1 92.31%
- Captions: 5/5; all four main sections and Experimental subsections matched

## B02 Status

- Role: Cross-domain Parser / Table Stress Benchmark; not a Ga2O3 Pilot
- PDF: `data/benchmark/B02/B02.pdf`
- SHA256: `A03C9B451F0E8358048567679DE83BB90ADB136EC72D01D1256C124FA3EAD7DF`
- Layout: IEEE two-column
- Primary stress targets: Table I and complex multi-column Table II
- Ground Truth: `ready_v1`, frozen before MinerU parsing
- Raw schema: `docvortex.middle` 2.0; 12 pages
- Raw Output: `data/parsed/B02/mineru/raw/`
- Benchmark result: `data/benchmark/B02/B02_BENCHMARK_RESULT.json`
- Benchmark report: `docs/B02_BENCHMARK_REPORT.md`
- Layer A: 20/26 scientific Figure detections, 17/20 typed Figure captions,
  9/10 Equation detections, and 0/2 Table detections
- Layer B: 12 Pages, 27 heading records, 133 TextBlocks, 16 Figures,
  10 Equations, and 0 Tables
- Table failures: `TABLE_BODY_MISSING` (Table I) and
  `TABLE_MISCLASSIFIED_AS_IMAGE` (Table II)
- Layer C result: `data/benchmark/B02/B02_LIGHTWEIGHT_TABLE_RECOVERY_RESULT.json`
- Layer C Tables: TP 2 / FP 0 / FN 0; precision/recall/F1 100%
- Table I: 10×3, 30/30 exact normalized core cells
- Table II: 14×7, 98/98 occupied, 97/98 exact and 98/98 semantic-normalized core cells

## Architectural Findings

MinerU 4.0.7 `middle_json` (`docvortex.middle` schema 2.0) exposes typed structures including `header`, `footer`, `page_footnote`, `paragraph_title`, `equation`, `image`, `image_caption`, and `doc_title`.

MinerUAdapter v2 behavior:

- Primary input: `middle_json`
- Fallback: existing Markdown + legacy Raw Output route

The mapping is implemented and covered by the full test suite.

B02 establishes that MinerU 4.0.7 did not produce a table entity for either
real body Table across its reviewed structural outputs. A separate Table Vision
Fallback is required before Parser v1 freeze; PaddleOCR-VL or an equivalent
table-capable vision parser is a future evaluation candidate, not installed or
implemented in this phase.

The preferred lightweight fallback is now ordinary PP-OCR on a PyMuPDF crop,
followed by deterministic spatial reconstruction. PaddleOCR-VL is retained only
as an optional extreme fallback. Runtime OCR invocation is not implemented.

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
4. B02 Table I body is missing from Raw structural/text rows; Table II is misclassified as an image.
5. B01 Ground Truth YAML currently has detailed Figure records for Figures 1–3 while the manually confirmed summary contains five Scientific Figures.
6. An aggregate benchmark pass threshold is not yet defined.
7. Lightweight reconstruction still needs runtime failure detection, region localization, crop-to-PDF transforms, and ordinary OCR integration.

## Key Git Commit

- `2f39f7962e0e37c4a1c5a431604fcc2a34411aff` — Add B01 parser benchmark evaluator

## Next Planned Phase

Lightweight Table runtime integration before Parser v1 freeze

Priority sequence:

1. Add generic MinerU Table-failure detection and probable-region localization.
2. Integrate PyMuPDF crop + ordinary PP-OCR through an isolated runtime boundary.
3. Preserve crop-to-PDF coordinate transforms and evaluate failure thresholds.
4. Complete separately authorized `Phase OCR-ENV-CLEANUP`.
5. Freeze Parser v1 only after runtime validation; keep PaddleOCR-VL optional.
