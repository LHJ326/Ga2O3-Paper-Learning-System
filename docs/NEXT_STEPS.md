# Next Steps

## P0 — MinerUAdapter v2

Use MinerU 4.0.7 `docvortex.middle` schema 2.0 `middle_json` as the primary input and convert it to Unified Document Schema 0.2 with complete Evidence preservation.

Keep the existing Markdown + legacy Raw Output route as fallback. Do not remove or rewrite Raw Output.

## P1 — B01 Adapter-Layer Evaluation

Run the existing B01 Ground Truth against MinerUAdapter v2 / Unified Document output as Layer B. Keep Layer A Raw metrics separate.

## P2 — Additional Pilot Papers

Select 1–2 further Pilot papers. At least one must contain a genuine main-text Table so Table extraction and evidence mapping can be stress-tested.

## P3 — Parser v1 Freeze

After multi-paper validation, freeze parser interfaces, schema mapping rules, benchmark procedures, and known limitations as Parser v1.

## P4 — RAG-Anything Integration Pilot

With explicit user approval:

- create an isolated RAG-Anything environment
- verify dependency compatibility
- implement `RAGAnythingAdapter`
- convert Unified Document elements to `content_list`
- validate Evidence round-trip and citation accuracy

RAG-Anything remains an indexing/retrieval layer; Unified Document + Evidence Store remains authoritative.

## P5 — Translation QA / Knowledge Card

Continue translation-quality evaluation and evidence-linked Knowledge Card design only after Parser v1 and the initial RAG integration boundary are stable.

No item in this file is authorized merely by being listed. Each phase begins only on an explicit user request.
