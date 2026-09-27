# P001 Document Validation Report

## Validation Result

`PASS_WITH_KNOWN_ISSUES`

The current P001 conversion is structurally consistent. The known MinerU Formula false positive is preserved and documented, not fixed in this validation phase.

## Document Statistics

| Component | Count |
| --- | ---: |
| Pages | 12 |
| Sections | 10 |
| TextBlocks | 214 |
| Figures | 6 |
| Equations | 6 |
| Tables | 0 |

- `document_id`: `P001`
- Metadata: present
- Total IDs across Page, Section, TextBlock, Figure, Equation, and Table: 248

## Integrity Checks

- All 248 element IDs are non-empty.
- All 248 element IDs are unique; duplicate ID count is 0.
- Two independent conversions produce the same ordered IDs for every collection.
- Page objects are continuous from 1 through 12.
- Every element has a page in the valid 1–12 range.
- Empty or invalid `page_number` count is 0.

## Evidence Coverage

| Element type | Complete source references | Coverage |
| --- | ---: | ---: |
| Figures | 6 / 6 | 100% |
| Equations | 6 / 6 | 100% |
| TextBlocks | 214 / 214 | 100% |

Complete evidence requires `paper_id`, `parser_name`, `parser_version`, `source_file`, and `page`. All Figures and Equations also retain a non-empty MinerU locator. TextBlocks retain a null locator when the Raw Output provides only page-level evidence.

## Relationship Checks

- Main Figure references: 40
- Supplementary Figure references: 23
- Truly unresolved Figure references: 0
- Dangling related IDs: 0
- Missing reverse Figure/TextBlock relationships: 0
- Supplementary references linked to main Figures: 0
- Equation adjacent-TextBlock IDs all resolve and contain reverse Equation IDs.

## Duplicate and Contamination Checks

- Duplicate Figure numbers: 0
- Duplicate Figure locators: 0
- Duplicate Sections: 0
- Formula locators present in Figures: 0
- Figure or Formula assets present in Tables: 0
- `Table S1` reference converted into a fabricated Table: no
- Duplicate TextBlock groups: 5, totaling 58 occurrences; maximum repetition is 12

All repeated TextBlocks are publisher or download boilerplate: journal-site links, the article citation footer, the Wiley copyright footer, and the Wiley Online Library download notice. No fully duplicated scientific body paragraph was found.

## Raw Output Snapshot

- Files: 24
- Deterministic SHA-256: `284c94c19cb634a3c17b592137a482603f213248b9178d6c6a7a1fd827358bb8`
- Git status under `data/parsed/P001/mineru/raw/`: unchanged

## Known Issues

1. MinerU classified one page-11 reference fragment as a Formula block. It remains represented as an image-only Equation until a later false-positive filtering phase.
2. Publisher headers, footers, site links, and download notices remain as repeated TextBlocks. They do not break identity or evidence integrity, but they are extraction noise for future filtering.

## Scope

This phase validates existing behavior only. It does not repair Equation classification, remove boilerplate, add Table extraction, or perform Benchmark scoring.
