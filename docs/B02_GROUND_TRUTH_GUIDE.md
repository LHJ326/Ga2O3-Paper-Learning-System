# B02 Ground Truth Annotation Guide

## Purpose and Independence Rule

B02 is the cross-domain Parser / Table stress benchmark for an IEEE
two-column integrated-circuit paper. It is not a Ga2O3 Pilot paper and must not
be numbered P002 or P003.

All Ground Truth must be obtained by manually checking
`data/benchmark/B02/B02.pdf`. Do not inspect MinerU output while annotating,
and do not revise Ground Truth later merely to agree with MinerU predictions.
Record uncertainty explicitly as `TODO` instead of guessing.

## Annotation Workflow

1. Confirm the PDF identity against `B02_METADATA.yaml` before each annotation
   session: 7,107,290 bytes and SHA256
   `A03C9B451F0E8358048567679DE83BB90ADB136EC72D01D1256C124FA3EAD7DF`.
2. Work page by page using the PDF's physical 1-based page numbers.
3. Read each page in logical IEEE column order, then inspect full-width objects
   that interrupt or bridge the columns.
4. Transcribe labels and captions exactly enough to distinguish punctuation,
   subscripts, superscripts, units, brackets, and footnote markers.
5. Mark each completed field as manually verified in the annotation notes.

## Required Checks

### 1. Page Count

Confirm 12 physical PDF pages. Do not confuse printed journal page numbers
3094-3105 with project page numbers 1-12.

### 2. Main Sections

Verify Roman-numeral labels, exact titles, and start pages for Sections I-V.
Confirm that References and author biographies are back matter, not main
sections.

### 3. Subsections

Verify every lettered subsection under Sections II-IV. Preserve numbered
lower-level headings such as the two coefficient-reuse strategies separately
in notes if the schema is later extended.

### 4. Figures and Captions

Verify Figures 1-20, their physical PDF pages, full captions, subfigure labels,
and whether each object spans one or both columns. Keep Figure captions linked
to their Figure even when nearby body text is geometrically closer.

### 5. Equations

Verify numbered Equations (1)-(9). Transcribe symbols, summations, fractions,
subscripts, superscripts, delimiters, and equation numbers from the PDF. Do not
reconstruct an Equation from prose if it is not visibly printed as an Equation.

### 6. Table I

For `NIST 800-22 RANDOMNESS TEST` on PDF page 8, verify:

- the exact title and page;
- the six physical columns, formed by two repeated groups of
  `Test / P-value / Pass?`;
- all five physical rows and all ten named tests;
- every P-value and every Pass result;
- whether any visible note should be treated as a table footnote.

The unusual paired layout must not be flattened into the wrong row order.

### 7. Table II

For `PERFORMANCE COMPARISON WITH STATE-OF-THE-ART ISING PROCESSORS` on
PDF page 11, verify:

- all seven columns, including the six previous/current-work columns;
- all parameter rows and exact row labels;
- multi-line cells and units such as nm, MHz, V, µm², µW, and fJ;
- normalized or bracketed values such as parenthetical area ratios;
- reference markers in column headers;
- superscript footnote markers A-D and the exact text of every footnote;
- the distinction between `N/A`, numeric ranges, and descriptive values.

Table II is the primary stress target. Transcribe cell-by-cell and perform a
second independent visual pass. Leave `TODO` for any ambiguous glyph rather
than normalizing it silently.

### 8. IEEE Repeated Headers and Footers

Record the alternating journal header and author/title header separately.
Printed page numbers belong to boilerplate. They must not enter scientific
body TextBlocks.

### 9. Authorized Licensed Use Notice

The IEEE Xplore authorized-use/download notice repeats at the bottom of all
12 pages. Record it as boilerplate and exclude it from scientific content.

### 10. Reading Order

Check reading order visually, not by raw x/y sorting alone. Pay particular
attention to:

- page 1: front matter, Figure 1, and the start of Introduction;
- page 8: Section III.G, Figures 13-14, Table I, and Sections IV.A-IV.B;
- page 11: full-width Table II, Figure 20, continuation of Section IV.E,
  Section V, and the start of References;
- page 12: continuation of References followed by author biographies.

For every ambiguity, add page-specific anchors to `reading_order_notes` before
marking Ground Truth ready.

## Completion Gate

Do not change `ground_truth_status` from `building` until:

- all Figure captions and Equations are manually transcribed;
- both Tables are verified cell-by-cell, including footnotes;
- page-level reading-order notes cover every ambiguous layout region;
- a final pass confirms that no parser output influenced the annotations.

Only after that independent review may B02 parsing and benchmark evaluation be
authorized as a separate phase.
