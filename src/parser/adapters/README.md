# Parser Adapter Layer

## Purpose

The adapter layer isolates external parser-specific output from the rest of the project. Each adapter is responsible for converting a tool's output into the unified `Document` schema while preserving source references and making unsupported or uncertain fields explicit.

## Architecture

```text
External Parser

↓

Adapter

↓

Document Schema
```

## Supported adapters

- MinerU: `docvortex.middle` 2.0 `middle_json` primary conversion, with the
  preserved Markdown/legacy Raw Output contract as fallback
- Docling: candidate
- Marker: candidate
