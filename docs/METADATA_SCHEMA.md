# Metadata Schema

Phase 4.2 normalizes exactly one `.ris` or `.bib` record into
`data/metadata/<paper_id>.yaml`. BibTeX is parsed with the lightweight
`bibtexparser` library; RIS uses the project's small line-oriented parser.

## Canonical fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `paper_id` | string | yes | Stable Registry identity supplied by the importer |
| `title` | string | yes | Normalized paper title |
| `authors` | list of strings | yes | Ordered author names; may be empty when absent |
| `year` | integer or null | yes | Four-digit publication year when supplied |
| `journal` | string or null | yes | Journal or publication container |
| `doi` | string or null | yes | DOI without `doi:` or resolver URL, case-normalized |
| `keywords` | list of strings | yes | Ordered, deduplicated source keywords |
| `citation` | string | yes | Explicit source citation, or a deterministic display citation built only from normalized fields |

Unknown optional values remain `null` or empty lists; the importer does not
invent bibliographic facts. Title is required because a record without a title
cannot be safely identified for review.

## Source mappings

- BibTeX: `title`, `author`, `year`, `journal`/`journaltitle`, `doi`,
  `keywords`, and optional `citation`.
- RIS: `TI`/`T1`, repeated `AU`/`A1`, `PY`/`Y1`/`DA`,
  `JO`/`JF`/`T2`/`JA`, `DO`, repeated `KW`, and optional `C1`.

Each input file must contain exactly one bibliographic record. The caller must
provide an existing `paper_id` in `data/papers/registry.yaml`; successful import
writes `metadata_path` and changes `processing_status.metadata_ready` from
`false` to `true`. Other lifecycle flags are preserved. Failed parsing or a
missing/ambiguous Registry record does not update the Registry.

This metadata layer does not perform PDF parsing, RAG, Embedding, Vector DB, or
Agent operations.
