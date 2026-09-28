# Knowledge Schema

## Architecture

The knowledge layer uses **Core Schema + Domain Extension**:

```text
Unified Document + Evidence
→ Core Knowledge Schema
   ├── paper identity
   ├── research problem
   ├── methodology
   ├── results
   ├── innovation
   ├── limitations
   └── evidence traceability
→ optional Domain Extension
   └── semiconductor / Ga2O3 photodetector fields
```

Core knowledge remains portable across scientific domains. Domain extensions
add vocabulary and measurements without redefining Core fields. Neither layer
is an embedding format, Vector Database schema, RAG payload, or Agent state.

## Core Schema

The per-paper Core record is stored at
`data/papers/<paper_id>/knowledge/core.yaml`.

### `paper_identity`

- `paper_id`: stable Registry ID.
- `title`: canonical title or null until metadata is ready.
- `doi`: normalized DOI or null.
- `metadata_path`: canonical metadata artifact.

### `research_problem`

A list of explicit research questions, gaps, or objectives. Each item contains
`statement` and `evidence_refs`.

### `methodology`

A list of experimental, computational, analytical, or fabrication approaches.
Each item contains `name`, `description`, and `evidence_refs`.

### `results`

A list of reported findings. Each item may contain `claim`, `metric`, `value`,
`unit`, `conditions`, and `evidence_refs`. Missing values remain null; values
must not be inferred solely to fill the schema.

### `innovation`

A list of author-claimed or reviewer-confirmed contributions. Each item contains
`claim` and `evidence_refs`.

### `limitations`

A list of stated or explicitly reviewed limitations. Each item contains
`statement`, `scope`, and `evidence_refs`.

### `evidence_traceability`

Every knowledge claim points to entries in `evidence_index`. An evidence entry
contains:

- `evidence_id`: stable ID inside the Knowledge record.
- `element_id`: Unified Document element ID.
- `element_type`: Section, TextBlock, Figure, Table, or Equation.
- `page`: project-standard 1-based page number.
- `source_reference`: preserved parser Evidence payload or locator.
- `quote`: optional short supporting excerpt; null when not recorded.

Knowledge without supporting evidence may remain as a draft, but it must not be
marked `knowledge_ready`.

## Domain Extensions

`domain.yaml` identifies an extension using `domain_id` and `schema_path`, then
stores extension values under `fields`. Domain extensions use the same
`evidence_refs` identifiers as Core; they do not create a separate provenance
system.

The initial extension is
`data/domains/semiconductor/ga2o3/schema.yaml`, covering Ga2O3 photodetectors.
Additional semiconductor or non-semiconductor extensions may be added without
changing the Core Schema.

## Human-readable views

- `summary.md`: evidence-grounded paper overview.
- `key_points.md`: concise findings, innovations, and limitations with evidence
  references where available.

These Markdown files are views of structured knowledge, not replacements for
`core.yaml`, `domain.yaml`, or Unified Document Evidence.
