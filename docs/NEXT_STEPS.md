# Next Steps

## Completed — Phase 4.4.2-D1.5 Summary Knowledge Validator

Summary Knowledge validation now runs locally after extraction. It reports
seven-section structural completeness, Evidence coverage down to page and
source element/reference, and warning-only plausibility checks for wavelength,
responsivity, detectivity, response time, and on/off ratio.

Before multi-paper processing, review P001's missing Material/System, Device
Structure, and Mechanism sections and decide whether the Summary rendering
contract should make those headings mandatory. Do not begin batch extraction,
RAG, Vector Database, Embedding, or Agent work until that review is explicitly
authorized.

## Completed — Phase 4.4.2-A Knowledge Extraction Framework

Schema loading, a provider-neutral extractor interface, strict Core/Domain and
Evidence validation, validated artifact writing, and three versioned extraction
prompt contracts are now available. The framework contains no provider client
and performs no model call.

Any later extraction implementation must return the same `KnowledgeDraft`
contract and pass validation before persistence. This milestone does not
authorize LLM API, Embedding, RAG, Vector Database, or Agent integration.

## Completed — Phase 4.4.1 Knowledge Schema Design

The Knowledge Layer now has a domain-independent Core Schema and an initial
`semiconductor.ga2o3.photodetector` extension. Paper Object templates contain
`core.yaml`, `domain.yaml`, `summary.md`, and `key_points.md`, while evidence
references continue to point back to Unified Document elements and parser
Evidence.

Future knowledge extraction or authoring must populate these structures without
inventing unsupported claims. This schema milestone does not authorize LLM,
Embedding, RAG, Vector Database, or Agent integration.

## Completed — Phase 4.3 Batch Paper Ingestion

Local PDF directories can now be imported into standard Paper Objects with
stable P-series IDs, explicit lifecycle status, and Registry records. Optional
same-stem RIS/BibTeX sidecars are connected to the canonical Metadata Pipeline.

The module deliberately stops before PDF parsing: it does not batch-run MinerU
or invoke OCR/models. Subsequent work can build processing orchestration on the
registered Paper Objects, while RAG, Vector Database, Embedding, and Agent
layers remain out of scope.

## Completed — Phase 4.2 Metadata Pipeline

One-record BibTeX and RIS ingestion now produces canonical YAML metadata and
advances the matching Paper Registry record to `metadata_ready`. The pipeline
requires prior registration, rejects ambiguous multi-record files, preserves
unknown values explicitly, and supports the legacy scalar status representation
during transition.

Subsequent Paper Processing Pipeline work may build batch import orchestration
on this boundary. RAG, Vector Database, Embedding, and Agent work remain out of
scope until the reliable knowledge structure layer is complete.

## Completed — Phase 4.1.5 Paper Object Schema

`data/papers/TEMPLATE/` now defines the standard per-paper object layout:
`source`, `metadata`, `parsed`, `assets`, and `knowledge`, with a root
`status.yaml` that mirrors the Paper Registry lifecycle fields. The template is
identity-free and contains no fabricated paper.

Existing flat P001 storage and separate B-series benchmark storage remain
supported without migration. The next Paper Processing Pipeline work may use
this contract for explicitly imported papers, but must not begin RAG, Vector
Database, Embedding, or Agent implementation.

## Started — Phase 4.1 Paper Registry

The Paper Registry foundation is now being established for batch paper
management. The first artifact is an empty, non-fabricated Registry template at
`data/papers/registry.yaml` with stable Paper IDs, bibliographic fields, storage
references, and an ordered processing lifecycle:

`imported → metadata_ready → parsed → figures_processed → tables_processed → knowledge_ready`

The next Phase 4.1 work should validate real imports against the Registry while
preserving the existing P-series library layout and separate B-series benchmark
layout. RIS/BibTeX ingestion, PDF batch ingestion, metadata normalization, and
Knowledge Card generation remain subsequent Phase 4 tasks.

Do not begin Vector Database, Embedding, Agent, or RAG integration until the
reliable knowledge structure layer is complete.

## Next Phase — Phase 4 Paper Processing Pipeline

The next phase establishes a reliable batch paper-processing and knowledge
structure pipeline before retrieval infrastructure is introduced.

Planned work:

1. Paper Registry
2. RIS/BibTeX metadata ingestion
3. PDF batch ingestion
4. Metadata normalization
5. Knowledge Card generation
6. Preparation for RAG

Phase 4 does **not** yet include a Vector Database, Embedding, or Agent layer.
The reliable knowledge structure layer must be completed first. This document
records the next phase but does not start its implementation.

## Completed — Phase 3.5 OCR-ENV-CLEANUP

The ordinary PaddleOCR lightweight fallback now runs from the independent
`ocr-runtime\.venv-ocr` environment. The obsolete PaddleOCR source checkout and
VL/document-processing model caches were removed. Only
`PP-OCRv6_medium_det` and `PP-OCRv6_medium_rec` are retained for lightweight
table OCR. PaddleOCR-VL remains optional extreme fallback only.

## Completed — TABLE-LIGHT-2 Runtime Integration

Generic failure detection, region localization, PyMuPDF cropping, isolated
ordinary PP-OCR invocation, raw-artifact caching, measured coordinate transforms,
Unified Evidence, runtime Layer C evaluation, and B02 smoke validation are now
implemented. Frozen fixture reconstruction remains available independently.

The next phase is `OCR-ENV-CLEANUP`: establish the minimal ordinary PP-OCR
environment, identify required packages/models, freeze requirements, reproduce
from a fresh environment, remove VL-only models/dependencies and unused caches,
decide whether the 1.87 GiB checkout is required, retain ordinary OCR, and record
final disk footprint. Do not start it without explicit authorization.

## Completed — MinerUAdapter v2 and B01 Layer B

MinerU 4.0.7 `docvortex.middle` schema 2.0 `middle_json` is now the primary input and converts to Unified Document Schema 0.2 with Evidence preservation.

The existing Markdown + legacy Raw Output route remains the fallback. B01 Layer B is reported independently from unchanged Layer A metrics.

## Completed — B02 Raw MinerU + Current Adapter v2 Baseline

B02 Ground Truth is frozen as `ready_v1`. MinerU 4.0.7 Raw Output and its
SHA256 fingerprints are frozen, and Layer A / Layer B results are reported
independently in `docs/B02_BENCHMARK_REPORT.md`.

Both real B02 Tables have zero structured detections. Table I is
`TABLE_BODY_MISSING`; Table II is `TABLE_MISCLASSIFIED_AS_IMAGE`. B02 therefore
proves that Table Vision Fallback is required before Parser v1 freeze.

## Completed — Lightweight OCR Table Reconstruction

Existing PP-OCR JSON plus bbox is now reconstructed deterministically into
Unified Tables with cell-level Evidence. B02 Table I and Table II are recovered
in independent Layer C while frozen Layer A/B remain unchanged. PaddleOCR-VL is
an optional extreme fallback, not the default route.

## P0 — Lightweight Table Runtime Integration

In a separately authorized phase, add failure detection, probable-region
localization, PyMuPDF crop generation, isolated ordinary PP-OCR invocation, and
crop-to-PDF coordinate transforms. Do not install or invoke PaddleOCR-VL by
default.

## Deferred — Phase OCR-ENV-CLEANUP

Build a minimal ordinary-OCR environment, freeze requirements, revalidate both
B02 Tables, remove VL-only caches/dependencies, assess the 1.87 GiB source
checkout, and preserve ordinary OCR components. This is not authorized merely
by being listed here.

## P1 — Parser v1 Freeze

After B02 table recovery validation, freeze parser interfaces, schema mapping
rules, benchmark procedures, fallback boundaries, and known limitations as
Parser v1.

## P2 — RAG-Anything Integration Pilot

With explicit user approval:

- create an isolated RAG-Anything environment
- verify dependency compatibility
- implement `RAGAnythingAdapter`
- convert Unified Document elements to `content_list`
- validate Evidence round-trip and citation accuracy

RAG-Anything remains an indexing/retrieval layer; Unified Document + Evidence Store remains authoritative.

## P3 — Translation QA / Knowledge Card

Continue translation-quality evaluation and evidence-linked Knowledge Card design only after Parser v1 and the initial RAG integration boundary are stable.

No item in this file is authorized merely by being listed. Each phase begins only on an explicit user request.
