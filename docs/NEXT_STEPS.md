# Next Steps

## Completed — MinerUAdapter v2 and B01 Layer B

MinerU 4.0.7 `docvortex.middle` schema 2.0 `middle_json` is now the primary input and converts to Unified Document Schema 0.2 with Evidence preservation.

The existing Markdown + legacy Raw Output route remains the fallback. B01 Layer B is reported independently from unchanged Layer A metrics.

## P0 — Manual B02 Ground Truth Annotation

B02 is registered as a cross-domain Parser / Table stress benchmark, not a
Ga2O3 Pilot. Its Ground Truth status is `building`, and MinerU has not been run.

Complete manual source-PDF annotation of Figures, Equations, Table I, complex
Table II, boilerplate, and IEEE two-column reading order. Freeze Ground Truth
before authorizing any B02 parser run or evaluator work.

## P1 — Parser v1 Freeze

After B02 cross-domain validation, freeze parser interfaces, schema mapping rules, benchmark procedures, and known limitations as Parser v1.

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
