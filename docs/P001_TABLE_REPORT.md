# P001 Table Report

## Summary

- Detected Table references: 1
- Reference found: `Table S1 (Supporting Information)`
- Scientific Tables present in the available P001 PDF/Raw Output: 0
- `structured_table`: 0
- `image_table`: 0
- `textual_table_reference`: 1
- `no_table`: true for embedded main-document Tables
- `Document.tables`: 0

## Raw Output Findings

The available P001 Markdown and content JSON contain one explicit Table reference:

> `Table S1 (Supporting Information)`

This points to a supplementary Table that is not included in the available P001 PDF or MinerU Raw Output. The Raw Output contains:

- no `Table 1`, `Table 2`, `TABLE I`, or other main-document Table reference;
- no Markdown table separator rows;
- no HTML `<table>` element;
- no MinerU `Table block` locator;
- no table-labeled image asset;
- 11 `Image block` assets and 6 `Formula block` assets, none classified as Table.

## Classification

P001 is classified as `textual_table_reference` because it mentions an external supplementary `Table S1` without including structured or image Table content. No Table is created in `Document.tables`.

Ordinary multi-column paper layout, References, Figure composites, and Formula images are not treated as Tables.

## False Positives

No Table false positive was detected. The `Table S1` sentence is retained as ordinary TextBlock content and is not converted into a fabricated Table.

## MinerU Table Capability for P001

This Raw Output provides no Table object, Table locator, Markdown table, HTML table, or table image. Therefore, P001 can confirm conservative no-Table handling, but it cannot evaluate MinerU's structured Table extraction quality. A future benchmark paper containing a known Table is required for that evaluation.

## Current Limitations

- The referenced supplementary Table is outside the available P001 PDF/Raw Output.
- No structured or image Table exists here to exercise positive Table mapping.
- Table caption linkage, cells, spans, and row/column structure remain untested.
- This phase intentionally does not infer a Table from prose or obtain Supporting Information.
