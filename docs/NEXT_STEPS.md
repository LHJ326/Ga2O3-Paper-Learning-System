# Next Steps

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

## P0 — Table Vision Fallback Evaluation

With explicit user approval, define and benchmark an isolated table-capable
vision fallback such as PaddleOCR-VL or an equivalent parser. Preserve the
frozen B02 Ground Truth, MinerU Raw Output, Layer A metrics, and current Adapter
v2 baseline. Do not treat this recommendation as authorization to install or
implement the fallback.

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
