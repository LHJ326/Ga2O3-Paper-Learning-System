# B01 Evaluation Matrix

Weights use the B01 priority scale: 5 = Critical, 4 = Important, and 3 = Optional. Every result must be computed from the unified `Document` output and checked against source references.

| Capability | Weight | Test Method | Expected Result |
|---|---:|---|---|
| Reading order | 5 | Compare extracted paragraph order with B01 text-block Ground Truth across the two-column layout and page transitions. | Correct paragraph sequence with no cross-column interleaving; page and source references retained. |
| Figure extraction | 5 | Count parent figures and subfigures, then compare exported images, identifiers, and page locations with B01 Figure Ground Truth. | Exactly 4 figures and 14 subfigures, with images, stable ids, and correct page locations. |
| Caption linkage | 5 | Match each extracted caption to its parent figure and subfigure structure using Ground Truth identifiers and page evidence. | Every expected figure has the correct caption linkage; no caption is attached only by incidental output order. |
| Equation extraction | 5 | Count equations and compare normalized equation content, location, and linked explanatory text with B01 Equation Ground Truth. | Exactly 7 equations with preserved content and location; variable meanings remain linked when supported by source text. |
| Table extraction | 3 | Compare detected tables, structure, captions, and locations with B01 Ground Truth; also check for false positives. | All Ground Truth tables are represented correctly, or an empty table collection is returned if none exist, without false positives. |
| OCR capability | 3 | For any B01 region without a usable text layer, compare OCR output with the corresponding Ground Truth text and source location. | Required text is recoverable with traceable page evidence; unsupported OCR is reported explicitly rather than silently dropping content. |
| Output extensibility | 4 | Convert native parser output through its adapter and validate all unified `Document` collections and shared fields. | Output maps without tool-specific leakage; metadata, pages, sections, figures, tables, equations, and text blocks remain extensible. |
| Evidence preservation | 5 | Trace sampled paragraphs to linked figures/equations and then to page-level source references. | Every sampled chain is complete: paragraph → figure/equation → source reference. |

No aggregate score or pass threshold is assigned in Phase 1.5B-1. Threshold selection must be recorded before the first parser benchmark is run.
