# External Tool Evaluation

Research status: desk research only. No candidate has been installed, executed, or benchmarked. Capabilities below are hypotheses derived from official project materials and must be validated against B01 before selection.

## Evaluation Criteria

1. **PDF structure extraction** — reading order, headings, sections, page boundaries, coordinates, and traceable block identifiers.
2. **Figure extraction** — figure detection, image export, caption association, page location, and source references.
3. **Table extraction** — table detection, cell structure, merged cells, captions, export fidelity, and cross-page behavior.
4. **Equation extraction** — display and inline equation detection, representation quality, equation numbering, and source location.
5. **Scientific paper suitability** — multi-column layouts, references, captions, symbols, supplementary material, and born-digital versus scanned PDFs.
6. **Multimodal capability** — coordinated handling of text, layout, figures, tables, equations, charts, and scanned content.
7. **Extensibility with Parser Adapter** — stable machine-readable output, deterministic identifiers, page-level evidence, API clarity, and conversion cost to the unified `Document` schema.
8. **License and maintenance** — code license, model-weight license, service terms, commercial/research restrictions, release activity, documentation, issue handling, and long-term maintenance signals.

## Candidate Tools

| Tool | Purpose | Strengths | Weaknesses | Expected role in this project | Evaluation status |
|---|---|---|---|---|---|
| [MinerU](https://github.com/opendatalab/MinerU) | General document parsing and structured extraction, including OCR-oriented workflows. | Official materials emphasize structured document conversion, tables, formulas, and page/block location support. Multiple parsing tiers may support quality/cost comparisons. | Installation/runtime complexity and model requirements still need measurement. The MinerU Open Source License includes additional conditions beyond its Apache-2.0 basis and requires review. | Primary PDF parser candidate for B01 structure, figure, equation, table, and text-block evaluation. | Candidate — official-material review only; installation and B01 validation pending. |
| [Docling](https://github.com/docling-project/docling) | Multi-format document conversion into a unified `DoclingDocument` with structured exports. | Official documentation lists PDF layout, reading order, tables, formulas, image classification, lossless JSON, and extension points. Code is MIT-licensed. | Adapter mapping from `DoclingDocument` must be designed and benchmarked. Some pipelines use downloadable models whose licenses and resource needs must be reviewed separately. | Structured PDF parser candidate and reference for adapter-friendly document models. | Candidate — official-material review only; installation and B01 validation pending. |
| [Marker](https://github.com/datalab-to/marker) | Document conversion to Markdown, JSON, HTML, and chunks. | Official documentation describes image extraction, table and equation formatting, page-oriented JSON, and extension hooks. Code is Apache-2.0 licensed. | Depends on model-backed components for full capability; model weights use a separate modified license. Optional LLM modes are outside the current project scope. Hardware cost and complex-layout behavior require testing. | Comparative parser candidate, especially for scientific layout, equation, table, and image extraction. | Candidate — official-material review only; installation and B01 validation pending. |
| [PaddleOCR-VL](https://github.com/PaddlePaddle/PaddleOCR) | Vision-language document parsing and multilingual OCR for PDFs and images. | Official documentation describes recognition of text, tables, formulas, and charts with structured Markdown/JSON output. PaddleOCR code is Apache-2.0 licensed. | Requires model/runtime deployment and may download model files. Official guidance warns that incomplete pipeline use can affect quality and may produce hallucinated text; resource use and model licensing require review. | OCR and vision-heavy candidate for scanned or visually complex B01 pages, not yet selected as the default PDF parser. | Candidate — official-material review only; model execution and B01 validation deferred. |
| [PDFMathTranslate](https://github.com/PDFMathTranslate/PDFMathTranslate) | Scientific PDF translation while preserving layout, formulas, charts, contents, and annotations. | Focused on scientific-paper translation and layout preservation; supports multiple translation-service backends. | Translation-centric rather than a general canonical document parser. Service dependencies, translation variability, experimental OCR, and AGPL-3.0 obligations require review. | Future Translation QA candidate and possible downstream consumer of parser output; not assumed to be the baseline parser. | Candidate — translation evaluation deferred; no selection decision. |

## Evaluation Process

1. Confirm license, model, hardware, and data-handling constraints.
2. Define an adapter mapping from native output to the unified `Document` schema.
3. Run the same B01 input and fixed configuration for each eligible parser.
4. Score every candidate using the criteria above and preserve raw output plus provenance.
5. Record any selection in `TOOL_DECISION_RECORD.md`; this document alone does not authorize or finalize a tool choice.

## Official Sources Reviewed

- MinerU official repository: https://github.com/opendatalab/MinerU
- Docling official repository: https://github.com/docling-project/docling
- Marker official repository: https://github.com/datalab-to/marker
- PaddleOCR official repository: https://github.com/PaddlePaddle/PaddleOCR
- PDFMathTranslate official repository: https://github.com/PDFMathTranslate/PDFMathTranslate
