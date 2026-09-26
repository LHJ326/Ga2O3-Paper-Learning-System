# Paper Library Plan

## External Paper Library

External source:

`D:\杂\A科研\传感器`

Purpose:

Preserve original paper materials outside the project repository.

The external source is authoritative for original files. The project must not automatically scan, rename, move, overwrite, or synchronize this directory. Any future import must be explicit, limited to selected papers, and recorded by Paper ID with provenance.

## Internal Project Structure

Planned structure:

```text
data/
├── papers/
├── metadata/
├── parsed/
└── benchmark/
```

Directory purposes:

- `data/papers/` — future project-controlled working copies of explicitly selected source papers. These copies are not the authoritative originals.
- `data/metadata/` — structured metadata and Paper ID mappings, including bibliographic and source-location records.
- `data/parsed/` — immutable or versioned parser outputs organized by Paper ID, parser, parser version, and processing run.
- `data/benchmark/` — benchmark-specific paper inputs and generated evaluation artifacts. Ground Truth specifications remain under the repository-level `benchmark/` directory.

This phase defines the structure only. No `data/` directories or paper files are created or copied.

## Paper ID System

Paper IDs use a stable, zero-padded sequence:

- `P001`
- `P002`
- `P003`

The Paper ID does not depend on a filename, folder name, title spelling, DOI availability, or parser output. Once assigned, it must remain stable even if the source file is renamed or relocated. The mapping between Paper ID and external source location belongs in structured metadata.

## Paper Data Flow

```text
PDF

↓

MinerU

↓

Parser Adapter

↓

Document Schema

↓

Knowledge Card

↓

RAG
```

Every stage must preserve the Paper ID and evidence links to the original PDF location, page, and extracted object.

## Metadata Requirement

Each paper must include at least:

- `paper_id`
- `title`
- `authors`
- `year`
- `journal`
- `DOI`
- `PDF location`
- `RIS/BibTeX location`

Unknown values must remain explicit rather than being fabricated. File locations should be stored as data fields and must not be used as the stable paper identifier.

## Version Management

For each processing record, retain:

- original PDF
- parsed result
- processing date
- parser version

Recommended additional provenance includes input checksum, adapter version, configuration snapshot, environment snapshot, output checksum, and benchmark result. Parsed results must not overwrite original PDFs or previous parser runs.
