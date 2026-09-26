# Parser Interface

## 1. Why a unified Parser Interface is required

PDF parsers expose different APIs and produce incompatible structures. A common interface lets the project evaluate and replace parser tools without changing downstream benchmark, knowledge, or tutoring components.

## 2. Parsers do not determine the project structure

A parser is an adapter at the system boundary. Its native output must not define the repository layout, domain model, or downstream APIs. Tool-specific behavior stays inside its future adapter implementation.

## 3. Every parser converts to the unified Document Schema

All parser adapters must return `src.schema.document.Document`. Pages, sections, figures, tables, equations, and text blocks use shared traceability fields: `id`, `page_number`, `content`, and `source_reference`.

## 4. Preserve the evidence chain

Every extracted object retains a `source_reference` and its page location when available. Normalization must not remove the link back to the source PDF. Missing or uncertain information should remain explicit rather than being silently invented.

## 5. Benchmark evaluation uses unified output

Benchmarks compare the canonical `Document` output with ground truth. This keeps evaluation metrics independent of MinerU, PaddleOCR, Docling, or any other future parser and makes parser comparisons reproducible.

## Current scope

Phase 1.4 defines only the schema, abstract interface, and empty registry. No concrete parser is registered or implemented.
