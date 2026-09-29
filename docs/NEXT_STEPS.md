# Next Steps

## Completed — Phase 6.4 Final Release Check

An isolated `--no-local` clone, new Python 3.12.7 virtual environment, editable
install, dependency check, full public-clone test suite, secret/path scan, and
release-document review all pass. See `docs/RELEASE_CHECK_REPORT.md`.

The repository is ready to enter the GitHub v0.1.0 release operation only after
explicit authorization. The next operation may configure or verify the remote,
push the rewritten history, create the release tag, and publish release notes;
none of those actions occurred in Phase 6.4. Do not begin Phase 7 implicitly.

## Completed — Phase 6.3 Git History Cleanup

A verified offline bundle protects the original `master` history. Three paper
PDFs and two MinerU ZIP archives were removed from every reachable commit with
`git-filter-repo`; post-rewrite scans also confirm that `.env` was never present.
The working dataset remains locally available through ignored files, and the
testable source/fixture tree is preserved.

The next step is not Phase 7. Review
`docs/GIT_HISTORY_CLEANUP_REPORT.md`, decide whether the rewritten history is
accepted, and only then coordinate a public remote force-push and `v0.1.0` tag.
Anyone with an older clone must re-clone after that push. No remote operation or
release tag is authorized by this entry.

## Completed — Phase 6.2 Release Preparation (Publication Blocked)

MIT licensing, README disclosure, packaging metadata, architecture alignment,
ignore coverage, dependency review, and release checks are complete. The
working tree is ready for a release candidate, but public publication remains
blocked by three historical PDF blobs and a redistribution review for derived
MinerU/benchmark fixtures.

Before pushing to a public GitHub repository or creating `v0.1.0`:

1. Back up the current repository and coordinate a history rewrite.
2. Remove all historical paper PDF blobs from every ref.
3. Review derived parser ZIP, image, text, and benchmark fixtures for lawful
   redistribution; remove or replace any that cannot be published.
4. Rescan secrets and large objects, then repeat the clean-clone install test.
5. Force-push rewritten refs only after explicit approval and collaborator
   coordination.

No history rewrite, GitHub push, tag, release, or Phase 7 work is authorized by
this status entry.

## Completed — Phase 6.1 Clean Installation Verification

The v0.1.0 README workflow was reproduced in an isolated clone with a new
Python 3.12.7 virtual environment. Editable installation, dependency checks,
package imports, and the public-clone test suite all pass. See
`docs/INSTALL_TEST.md` for commands, versions, results, and the three expected
external-asset skips.

The next release action remains an explicit license decision and final Git
history review before remote publication or creation of a `v0.1.0` tag. Do not
enter Phase 7 without separate authorization.

## Completed — Phase 6.0 v0.1.0 Release Preparation

Public README and architecture documentation now describe the evidence-first
pipeline, installation, safe usage, current mock-vector limitation, and future
roadmap. Release hygiene excludes secrets, source PDFs, local indexes, and cache
artifacts from future commits. The repository metadata already declares version
`0.1.0` and all imported runtime dependencies.

Before publishing a GitHub Release, choose and add an explicit project license,
review the final public Git history for previously committed copyrighted or
sensitive content, configure repository metadata, and create the `v0.1.0` tag
only with separate authorization. Do not treat release preparation as approval
to add LLM answer generation or begin an autonomous Agent phase.

## Completed — Phase 5.5 Evidence-Aware Retrieval

The project now accepts a natural-language question and returns structured
FAISS retrieval results with Paper ID, Chunk ID, similarity, Evidence IDs, and
source location. The P001 dry-run used `top_k=5` and saved
`data/papers/P001/rag_report.yaml`; it did not call an LLM or generate an
answer.

The current deterministic mock vectors are suitable only for interface and
traceability validation. Do not interpret their ranking as semantic retrieval
quality. A later authorized phase must connect a real, versioned Embedding
adapter, build a persisted index, and define retrieval evaluation before
advancing Registry `embedding_status`, `vectorstore_status`, or `rag_status`.

## Completed — Phase 5.4 Local Vector Store Layer

A local FAISS boundary now supports validated addition, cosine search, atomic
index/metadata persistence, and lossless loading of Evidence-linked chunks.
The P001 dry-run built 149 in-memory index entries from deterministic mock
vectors and wrote `data/papers/P001/vectorstore_report.yaml`. It made no
Embedding API call and did not persist `data/vectorstore/P001.faiss`.

P001 `vectorstore_status` remains `pending`. A future production indexing phase
must first select and version a real Embedding adapter, then persist and verify
the index before advancing `embedding_status` or `vectorstore_status`. This
milestone does not authorize RAG, retrieval evaluation, or Agent integration.

## Completed — Phase 5.3 Embedding Foundation

Evidence-linked Paper Object chunking, an abstract embedding adapter, and a
dependency-free local vector-store interface are now available. The P001
dry-run produced 149 deterministic chunks referencing all 33 indexed Evidence
IDs, without calling an API or generating vectors. Its audit report is
`data/papers/P001/embedding_report.yaml`.

Before selecting a concrete embedding model, review chunk granularity and the
retained Paper Object warnings, then define model/version metadata, vector
normalization, persistence compatibility, and lifecycle transition criteria.
Only a successful future embedding run may advance Registry
`embedding_status`; this dry-run intentionally leaves it `pending`. Vector
Database and RAG integration remain outside this phase and require explicit
authorization.

## Completed — Phase 5.2 Paper Registry Upgrade

Registry v2 now tracks five lifecycle stages for each paper and supports
validated status updates, pending-task discovery, and completed-paper queries.
The batch dry-run reads these states and reports both completed and pending
stages. For P001, metadata, knowledge, and Paper Object stages are complete;
Embedding and RAG remain pending.

Pending lifecycle status is informational and does not authorize automatic
Embedding, Vector Database, RAG, model calls, or Agent work. Any such stage
requires a separately reviewed implementation and explicit authorization.

## Completed — Phase 5.1 Batch Paper Object Pipeline

P-series discovery, readiness tracking, dry-run planning, optional executor
injection, Paper Object reuse, and aggregate YAML reporting are now available.
The default path never calls DeepSeek. The current
`data/papers/batch_report.yaml` records P001 as completed with no pending or
failed papers.

Any later batch knowledge execution must explicitly configure an executor and
turn off dry-run. Do not infer that this milestone authorizes automatic API
calls, Embedding, Vector Database, RAG, cross-paper comparison, or Agent work.

## Next Phase — Phase 5 Multi-Paper Knowledge System

Phase 4 is complete. Its final architecture, test baseline, Git milestones,
P001 artifacts, and validation status are recorded in
`docs/PHASE4_FINAL_REPORT.md`.

Phase 5 is planned to scale the reliable Paper Object boundary across multiple
papers and later prepare Embedding, Vector Database, RAG, cross-paper
comparison, and an AI Research Assistant. This entry records direction only;
Phase 5 implementation has not started and requires separate authorization.

## Completed — Phase 4.4.4 Paper Object Finalization

P001 now has one validated `paper_object.yaml` containing paper identity, source
paths, the complete Summary/Parameters/Performance/Mechanism payloads, a unified
33-record Evidence index, and aggregate validation status. Evidence coverage is
100%; `authors` and `doi` intentionally remain null because existing metadata
does not supply them.

Before any downstream indexing, review the 8 retained warnings and decide
whether the corresponding source knowledge observations should remain as-is.
This milestone does not authorize batch processing, RAG, Vector Database,
Embedding, or Agent integration.

## Completed — Phase 4.4.3-B3 Mechanism Extraction (Review Required)

P001 Mechanism extraction completed from 23 selected Evidence records in 6
bounded DeepSeek calls. The run used 66,423 input characters and saved
`mechanism.yaml`, prompt/response JSONL, and `mechanism_extraction_run.yaml`
under `data/papers/P001/knowledge/`.

Before downstream use, review observations whose `review_status` is
`review_required`. `gain_mechanism` remains null because the run did not produce
a supported value. Do not begin batch processing, RAG, Vector Database,
Embedding, or Agent work without separate authorization.

## Completed — Phase 4.4.3-B2 Performance Extraction (Review Required)

P001 now has a separately validated Performance artifact generated from 20
selected Evidence records in 5 bounded DeepSeek calls. The run used 63,061
input characters and saved `performance.yaml`, prompt/response JSONL, and a run
manifest under `data/papers/P001/knowledge/`.

Before using the extracted performance values downstream, review the single
semantic warning for `on_off_ratio` / E00169. The validator intentionally keeps
the original model output and reports the conflict instead of rewriting it.
Mechanism Extraction must wait for separate authorization; batch processing,
RAG, Vector Database, Embedding, and Agent work remain out of scope.

## Completed — Phase 4.4.3-B1 Material + Device Extraction

P001 now has an Evidence-closed Material/Device knowledge artifact generated
from 23 selected records in 4 bounded DeepSeek calls. The run used 55,267 input
characters, retained full prompt/response provenance, and wrote
`data/papers/P001/knowledge/device_parameters.yaml` only after schema, type,
page, source-element, and Evidence-reference validation.

Any Performance Extraction must use a separately reviewed task-specific
selector and schema. It must not reuse Material/Device outputs as factual input,
and Mechanism Extraction, batch processing, RAG, Vector Database, Embedding,
and Agent work remain out of scope until separately authorized.

## Completed — Phase 4.4.3-A Parameter Extraction Framework

A schema-driven, model-neutral Parameter Extraction boundary is ready for
Ga2O3 photodetector papers. It preserves nulls for unsupported fields, requires
closed Evidence references with 1-based pages and source locators, checks
measurement-unit consistency, and writes only validated
`device_parameters.yaml` artifacts.

The next separately authorized step is Phase 4.4.3-B real Parameter Extraction.
It must begin with one explicitly selected paper and a reviewed Evidence-input
strategy. This framework milestone does not authorize a DeepSeek call, batch
processing, RAG, Vector Database, Embedding, or Agent work.

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
