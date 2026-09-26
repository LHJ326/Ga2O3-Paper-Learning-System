# PDF Parser Decision Record

This record defines how a PDF parser will be selected. It does not select or approve a parser in Phase 1.5C-1.

## Project Requirements

The authoritative requirements are defined in [B01 Parser Requirements](B01_PARSER_REQUIREMENTS.md). The decision must evaluate at least:

- Reading order
- Figure extraction
- Caption linkage
- Equation extraction
- Evidence chain
- Adapter compatibility

Candidate claims are not evidence of compliance. Each requirement must be validated through the B01 benchmark and represented through the unified `Document` schema.

## Candidates

### MinerU

Role:

Primary PDF parser candidate

Evaluation status:

Pending

### Docling

Role:

Alternative parser candidate

Evaluation status:

Pending

### Marker

Role:

Alternative PDF-to-Markdown candidate

Evaluation status:

Pending

## Evaluation Matrix

Weights follow the B01 priority scale. Candidate cells remain `Pending` until results are produced under the same benchmark procedure.

| Criterion | Weight | MinerU | Docling | Marker |
|---|---:|---|---|---|
| Reading order | 5 | Pending | Pending | Pending |
| Figure extraction | 5 | Pending | Pending | Pending |
| Equation extraction | 5 | Pending | Pending | Pending |
| Caption linkage | 5 | Pending | Pending | Pending |
| Scientific suitability | 4 | Pending | Pending | Pending |
| Adapter compatibility | 4 | Pending | Pending | Pending |
| Maintenance | 3 | Pending | Pending | Pending |

No total score, ranking, or selection is recorded yet.

## Decision Process

Selection follows:

```text
Requirements

↓

Benchmark

↓

Evaluation

↓

Decision
```

The final choice must be supported by preserved benchmark inputs, tool versions and configuration, native outputs, adapter outputs, scores, known limitations, and a completed decision record.
