# P001 Equation Report

## Summary

- Raw Formula block assets: 6
- `Document.equations`: 6
- `markdown_math`: 0
- `image_only`: 6
- Machine-readable equation numbers stored: 0
- Equations without a stored number: 6
- Equation numbers visibly present in formula images: 5 (`1` through `5`), recorded as a diagnostic observation only

MinerU 4.0.7 Flash output contains Formula block image assets and locators, but no Markdown/LaTeX math for P001. The adapter therefore leaves every `Equation.content` empty and preserves the formula image as evidence. It does not use OCR or reconstruct formulas from surrounding prose.

## Equation Inventory

| Equation | Page | MinerU locator | Formula image | Representation | Content | Stored number | Adjacent TextBlocks |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `P001-equation-001` | 6 | `doc:468f0b8/tier:flash/page:6/block:8` | `images/page_006_block_008.jpg` | `image_only` | empty | none | `P001-text-0059`, `P001-text-0060` |
| `P001-equation-002` | 6 | `doc:468f0b8/tier:flash/page:6/block:10` | `images/page_006_block_010.jpg` | `image_only` | empty | none | `P001-text-0060`, `P001-text-0061` |
| `P001-equation-003` | 7 | `doc:468f0b8/tier:flash/page:7/block:11` | `images/page_007_block_011.jpg` | `image_only` | empty | none | `P001-text-0078`, `P001-text-0079` |
| `P001-equation-004` | 8 | `doc:468f0b8/tier:flash/page:8/block:12` | `images/page_008_block_012.jpg` | `image_only` | empty | none | `P001-text-0090`, `P001-text-0091` |
| `P001-equation-005` | 8 | `doc:468f0b8/tier:flash/page:8/block:13` | `images/page_008_block_013.jpg` | `image_only` | empty | none | `P001-text-0090`, `P001-text-0091` |
| `P001-equation-006` | 11 | `doc:468f0b8/tier:flash/page:11/block:55` | `images/page_011_block_055.jpg` | `image_only` | empty | none | `P001-text-0185`, `P001-text-0186` |

## Number Status

The first five Formula images visibly contain the printed equation numbers `(1)` through `(5)`. These numbers are not exposed as structured text by MinerU. They are not stored in `equation_number`, because doing so would require OCR or P001-specific manual hardcoding. The sixth asset contains no equation number.

## Current Limitations

- Formula semantics and LaTeX are unavailable in the current Raw Output.
- Printed equation numbers cannot be captured without a future OCR or formula-recognition stage.
- The page-11 Formula block is visually a continuation of reference `[58]`, not a scientific equation. This is a MinerU block-classification false positive. It remains mapped with its raw evidence so the classification error is explicit and benchmarkable; no content is fabricated.
- Adjacent TextBlock links express layout proximity only and do not provide a physical interpretation of an equation.
- The current mapping intentionally performs no OCR, semantic reconstruction, or equation-quality scoring.
