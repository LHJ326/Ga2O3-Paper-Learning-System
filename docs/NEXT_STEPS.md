# Next Steps

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
