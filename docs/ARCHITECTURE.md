# System Architecture

## Design Principles

Ga2O3 Paper Learning System uses an evidence-first, layered architecture. The
Unified Document and its Evidence records are the factual boundary. Every
downstream asset must either retain source references or explicitly remain
null. Components are modular, batch operations are dry-run first, and external
model calls require explicit execution.

```text
Sources
  -> Ingestion
  -> Metadata
  -> Parser / Unified Document / Evidence
  -> Knowledge
  -> Paper Object
  -> Registry
  -> Embedding
  -> VectorStore
  -> RAG Retrieval
```

## Ingestion

Location: `src/ingestion/`

Ingestion scans PDF directories, assigns collision-free P-series IDs, creates
the standard paper directory layout, copies source assets, links optional
metadata sidecars, and registers papers. It does not parse PDFs or call an LLM.

Standard paper layout:

```text
data/papers/<paper_id>/
  source/
  metadata/
  parsed/
  assets/
  knowledge/
  status.yaml
```

## Metadata

Location: `src/metadata/`

The metadata pipeline accepts RIS and BibTeX, normalizes bibliographic fields,
writes `data/metadata/<paper_id>.yaml`, and advances the corresponding import
state. Core fields include title, authors, year, journal, DOI, keywords, and a
formatted citation. Missing source values are preserved as null rather than
inferred.

## Parser, Unified Document, and Evidence

Locations: `src/parser/`, `src/schema/`

MinerU 4.0.7 `docvortex.middle` schema 2.0 is the primary structured parser
input; Markdown and legacy raw outputs remain fallbacks. The adapter maps text,
sections, figures, equations, tables, pages, and locators into Unified Document
Schema 0.2. Project pages are 1-based.

Headers, footers, and page footnotes are excluded from normal body TextBlocks.
Scientific figures require both an image and a recognizable scientific caption.
Parser omissions are not reconstructed from ground truth or domain knowledge.

Table recovery follows a separate failure boundary:

```text
MinerU table failure
  -> probable region localization
  -> PyMuPDF crop
  -> isolated ordinary PaddleOCR runtime
  -> deterministic spatial reconstruction
  -> Unified Table + cell-level Evidence
```

MinerU and PaddleOCR are external runtimes. They are not implicit dependencies
of the main Python environment.

## Knowledge

Location: `src/knowledge/`

The Knowledge layer combines a general research-paper schema with a Ga₂O₃
domain extension. It provides model-neutral extractors, task-specific prompt
strategies, validators, and writers for:

- Summary
- Material and device structure
- Optical, electrical, dynamic, and stability performance
- Physical and device mechanisms

Every populated scientific field must retain Evidence references. Validators
check structure, field types, units, page/source locators, Evidence coverage,
and selected semantic conflicts. Warnings never silently rewrite model output.

The LLM boundary is defined under `src/llm/`. DeepSeek is the first optional
adapter; the API key is read only from `DEEPSEEK_API_KEY`. Mock adapters support
tests without network calls.

## Paper Object

Location: `src/paper_object/`

The Paper Object is the canonical per-paper knowledge asset. It combines:

- Paper identity and source locations
- Summary, Parameters, Performance, and Mechanism
- A deduplicated Evidence index
- Evidence coverage, warnings, and review status

The builder reads existing artifacts and never fills missing knowledge. The
validator rejects unresolved Evidence references. Export is atomic YAML.

## Registry and Batch Lifecycle

Locations: `src/registry/`, `src/batch/`

`data/papers/registry.yaml` records metadata, knowledge, Paper Object,
embedding, vector-store, and RAG state. RegistryManager currently validates and
queries metadata, knowledge, Paper Object, embedding, and RAG lifecycle fields;
`vectorstore_status` is an additive record field read by the Phase 5.4 dry-run
and is not yet advanced by RegistryManager. The batch layer discovers papers,
consults its supported Registry state, and reports completed, pending, and
failed work.

Batch execution defaults to dry-run. Knowledge generation requires an explicit
executor; no LLM call occurs solely because a Registry stage is pending.

## Embedding

Location: `src/embedding/`

`PaperObjectChunker` converts validated Paper Object knowledge into
deterministic `EmbeddingChunk` records:

```text
chunk_id
paper_id
source_file
evidence_ids
text
```

Only evidence-linked knowledge is eligible. Unknown Evidence IDs fail fast.
`EmbeddingAdapter` defines `embed(texts) -> vectors` but v0.1.0 does not select
a production embedding model.

## VectorStore

Location: `src/vectorstore/`

The backend-neutral VectorStore contract supports `add`, `search`, `save`, and
`load`. The default local backend uses normalized FAISS `IndexFlatIP` vectors
for cosine similarity. A persisted index is paired with JSON metadata containing
the complete chunks and Evidence references.

The checked-in P001 vector-store report is a dry-run using deterministic mock
vectors. No production index is committed.

## RAG Retrieval

Location: `src/rag/`

The current RAG layer is retrieval only. A natural-language question is encoded
through an injected query encoder, searched against the VectorStore, and
returned as structured results:

```text
paper_id
chunk_id
similarity
evidence_ids
source
```

There is no LLM answer-generation layer in v0.1.0. Mock-vector rankings validate
interfaces and traceability only and must not be interpreted as semantic
retrieval quality.

## Trust and Dependency Boundaries

1. Original PDFs and external parser outputs are user-controlled inputs.
2. Unified Document + Evidence is the internal factual source layer.
3. Knowledge and Paper Objects are validated derived assets.
4. Embeddings and indexes are replaceable retrieval artifacts.
5. Retrieval results expose Evidence; they are not scientific conclusions.
6. Human review remains required for warnings and uncertain knowledge.
