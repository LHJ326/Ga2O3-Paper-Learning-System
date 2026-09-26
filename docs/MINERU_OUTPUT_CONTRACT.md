# MinerU Output Contract

## Purpose

This contract defines how MinerU raw output is stored before adapter conversion. It separates immutable parser results from the unified project schema so that conversion can be repeated, audited, and versioned independently.

## Pipeline

```text
PDF

↓

MinerU

↓

Raw Output

↓

MinerU Adapter

↓

Document Schema
```

## Directory Structure

```text
data/
└── parsed/
    └── P001/
        └── mineru/
            └── raw/
                ├── json/
                ├── markdown/
                ├── images/
                └── metadata.json
```

The `P001` directory is an example Paper ID. Each paper receives an independent raw-output directory.

## Raw Output Principle

Raw Output must:

- preserve the original parser results;
- remain unmodified after capture;
- support repeatable conversion without rerunning MinerU.

Normalization, correction, and schema mapping belong in the adapter or downstream outputs, not in the raw-output directory.

## Metadata Requirement

Each `metadata.json` must contain:

- `paper_id`
- `parser_name`
- `parser_version`
- `processing_time`
- `source_pdf`
- `checksum`
- `adapter_version`

## Evidence Chain

Every converted `Document` element must be traceable through the following chain:

```text
PDF page

↓

MinerU block

↓

Document element
```

The adapter must preserve the source page and MinerU block reference needed to reconstruct this relationship.

## Version Control

Every conversion record must identify:

- MinerU version
- Adapter version
- Schema version

These versions allow raw output to be converted again when adapter or schema behavior changes.
