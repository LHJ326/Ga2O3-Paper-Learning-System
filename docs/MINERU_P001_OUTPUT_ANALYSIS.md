# MinerU P001 Output Analysis

This analysis describes the existing P001 raw output produced by MinerU 4.0.7 with the local `flash` tier. The parse covers pages 1–12. No document was reparsed during this analysis.

## 1. Output Files

| JSON file | Purpose |
| --- | --- |
| `json/P001_content.json` | Main content response. Contains the `parse` record and a `content` object whose body is one Markdown string. It also records scope, range, truncation, and continuation state. |
| `json/parse_export.json` | Record of the first parse/export request. Contains parse identifiers, cache information, completion status, and the path of the written Markdown file. Its `content` field is `null` because the content was exported to a file. |
| `json/image_exports.json` | Manifest joining 17 MinerU image locators to exported JPEG filenames. Each entry also records MIME type, byte size, width, and height. |
| `metadata.json` | Project-side run record outside the `json/` directory. Records the paper, parser version and tier, checksum, command, timing, page range, and processing status. |

The two `*.stderr.log` files are empty, indicating that neither content export command wrote an error message.

Key parse facts:

- SHA-256: `468f0b89a752537ef06c11d979c4cd8cf3d9a84492193a5b1daa6235062f2f64`
- MinerU short ID: `468f0b8`
- Tier: `flash`
- Page range: `1-12`
- Status: `done`
- Content format: `markdown`
- Content response: not truncated; no continuation request

## 2. Document Structure

The Flash output is not a JSON array of pages or semantic blocks. `P001_content.json` has two top-level objects: `parse` and `content`. The parsed document body is stored in `content.content` as a single Markdown string.

| Concept | Representation in this output | Analysis |
| --- | --- | --- |
| Page | Markdown comments such as `<!-- page 1 of 12 -->`; image locators also contain `page:<n>` | All 12 pages have a page marker. All 17 image-locator page numbers agree with their surrounding Markdown page marker. |
| Block | Locator form `doc:468f0b8/tier:flash/page:<n>/block:<n>` | Exact block identifiers are present for image references. There is no general block array and ordinary text paragraphs do not carry block locators. The response-level `content_ranges` gives only a start and end range. |
| Text | One Markdown string in `content.content` | Paragraphs can be separated using blank lines within each page range. Scientific subscripts and superscripts are represented mainly with HTML `<sub>` and `<sup>` tags. |
| Section | Markdown heading hierarchy | The output has one H1 document title and nine H2 headings. Sections can be proposed from these headings, but they are not separate JSON objects. |
| Image | Markdown image reference targeting a MinerU locator, plus an entry in `image_exports.json` | There are 17 exported JPEG assets. The manifest provides a deterministic locator-to-file join. |
| Table | No table field, HTML table, or Markdown table was found | This output provides no explicit table object. Absence in the output must not be interpreted as proof that the PDF contains no table. |
| Equation | No equation field, MathML, LaTeX command, or display-math delimiter was found | Mathematical and scientific notation is embedded in ordinary Markdown/HTML text where preserved. This output cannot directly supply equation objects or equation-level locations. |

The Markdown contains 243 `<sub>` tags and 64 `<sup>` tags. These tags preserve useful scientific typography, but they do not by themselves distinguish variables, chemical formulae, units, or equations.

## 3. Figure Mapping

The most reliable image mapping is:

```text
Markdown image target

↓ exact locator join

image_exports.json entry

↓ file field

images/*.jpg

↓ page:<n> in locator

PDF page
```

For example, the locator is the stable join key; the exported filename is a storage detail and should not be used as the only identity.

Caption linkage is not explicit. A provisional caption candidate can be sought in the nearest text following an image reference on the same page. In this output, 6 of 17 image references are immediately followed by text matching a numbered Figure caption, while 11 have no immediately adjacent numbered caption. Therefore:

- the 17 assets must not automatically be treated as 17 scientific figures;
- figure, subfigure, logo, decoration, and other image roles remain unclassified;
- caption linkage must carry a confidence or review status;
- the image locator and page number must be preserved even when no caption is linked.

## 4. Equation Mapping

There is no dedicated equation field in any of the three analyzed JSON files. The Markdown also contains no display-math delimiters, MathML nodes, or recognized LaTeX commands.

Consequently, the current output supports only the following equation mapping proposal:

1. Treat equation detection as a later classification step over page-bounded Markdown and image blocks.
2. Preserve the original Markdown/HTML representation exactly when a candidate is identified.
3. Use the surrounding page marker as the minimum source location.
4. Use an exact MinerU block locator only when the candidate originates from a locator-bearing image block.
5. Mark variable meanings as unavailable unless supported by nearby source text; do not infer or invent them.

Equation count and equation fidelity cannot be validated from Flash-tier field structure alone.

## 5. Evidence Chain

The proposed evidence chain is:

```text
PDF checksum and page

↓

MinerU parse identity, tier, page marker, and optional block locator

↓

Document element source_reference
```

Recommended source-reference components are:

- paper ID: `P001`;
- PDF SHA-256;
- MinerU version and tier;
- MinerU `short_id`;
- page number;
- block locator when available;
- raw Markdown span or adapter-local paragraph index when no block locator exists;
- raw asset filename for image elements.

The evidence precision is asymmetric: images have exact page/block locators, while ordinary text is only directly bounded by page markers. An adapter must record this limitation rather than manufacture MinerU block IDs for text.

## 6. Adapter Mapping Proposal

This section is a design proposal only; no adapter implementation is included.

| Unified target | Proposed raw source | Mapping rule |
| --- | --- | --- |
| `Document.document_id` | `data/metadata/P001.yaml` | Use the registered Paper ID, not a filename or MinerU short ID. |
| `Document.metadata` | Paper metadata, raw `metadata.json`, and `parse` | Combine bibliographic registration with parser provenance while retaining the PDF checksum. |
| `Page` | Markdown page comments | Split the body at page markers and retain the unmodified page Markdown. |
| `Section` | H1/H2 headings | Build hierarchical ranges from headings, recording the pages spanned by each section. |
| `TextBlock` | Blank-line-delimited Markdown within a page | Assign deterministic adapter-local IDs and retain page number plus raw span/index. Do not claim a MinerU block ID. |
| `Figure` | Markdown image locator joined to `image_exports.json` | Store the exported asset, locator, page, and a separately classified caption candidate with confidence. |
| `Table` | No explicit source in this output | Emit none unless a later detection rule identifies a candidate; record that the parser supplied no table object. |
| `Equation` | Inline Markdown/HTML or locator-bearing image candidate | Emit only after explicit classification, preserve raw content, and record location precision and uncertainty. |

Before conversion is accepted, validation should confirm:

- checksum agreement among paper metadata, parse JSON, and run metadata;
- parse status is `done` and content is not truncated;
- expected page range and page-marker continuity;
- every image locator resolves to exactly one manifest entry and one existing asset;
- locator page numbers agree with Markdown page context;
- unclassified images, tables, and equations remain explicit uncertainties.
