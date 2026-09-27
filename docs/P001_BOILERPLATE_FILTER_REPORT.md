# P001 Boilerplate Filter Report

## Summary

- Before TextBlocks: 214
- After TextBlocks: 156
- Filtered TextBlocks: 58
- Boilerplate groups: 5
- Scientific body blocks removed: 0 detected
- Raw Output modified: no

The adapter filters only exact text repeated across at least three pages when every occurrence is at a page edge and the group also has high-confidence decoration evidence. Raw-sequence TextBlock IDs are assigned before filtering, so retained TextBlock IDs and existing evidence links remain stable.

## Filtered Groups

### 1. Repeated journal citation footer

- Example: `Adv. Funct. Mater. 2025, 2508292`
- Occurrences: 12
- Pages: 1–12
- Reason: `repeated_page_edge_short_decoration`

### 2. Journal website banner

- Example: `[www.afm-journal.de](http://www.afm-journal.de)`
- Occurrences: 12
- Pages: 1–12
- Reason: `repeated_page_edge_url_banner`

### 3. Copyright footer

- Example: `© 2025 Wiley-VCH GmbH`
- Occurrences: 12
- Pages: 1–12
- Reason: `repeated_page_edge_copyright_notice`

### 4. Download and terms notice

- Example: `Downloaded from ... Terms and Conditions ... rules of use ...`
- Occurrences: 11
- Pages: 2–12
- Reason: `repeated_page_edge_download_notice`

### 5. Publisher website banner

- Example: `[www.advancedsciencenews.com](http://www.advancedsciencenews.com)`
- Occurrences: 11
- Pages: 2–12
- Reason: `repeated_page_edge_url_banner`

## Conservative Rule

A repeated group is filtered only when all of the following are true:

1. The complete text is identical across at least three distinct pages.
2. Every occurrence is within the first five or last four Markdown blocks of its page.
3. The group is not a Figure caption, Table caption, numbered Reference entry, or TextBlock adjacent to a Formula block.
4. The group is a download notice, copyright notice, short URL banner, or short decoration repeated across at least half of the document pages.

Repetition alone is insufficient. Repeated scientific terms or body statements away from page edges remain in the Document.

## Protected Content Checks

- Sections: 10, unchanged
- Figures: 6, unchanged
- Equations: 6, unchanged
- Tables: 0, unchanged
- Figure captions: retained
- `Table S1` contextual reference: retained
- Equation context TextBlocks: retained
- Experimental Section content: retained
- Numbered References: retained
- TextBlock source-reference coverage: 156 / 156 (100%)

## Diagnostics

The complete filtered text, page list, occurrence count, and filter reason for every group are stored in `Document.metadata.content.boilerplate_filter`. The original text remains unchanged in MinerU Raw Output.

## Current Limitation

This first filter handles exact repeated page decoration only. Near-duplicate headers or footers with changing page numbers are deliberately retained until a separate conservative normalization rule is validated.
