# MinerU Adapter Design

## Input Structure

`MinerUAdapter.convert()` accepts the path of one preserved MinerU raw-output directory. The first version reads:

- `metadata.json` for Paper ID, parser version, tier, checksum, and run provenance;
- `json/*_content.json` for parse metadata and the complete Markdown body;
- `json/image_exports.json` for locator-to-image mappings;
- `images/` for the exported image assets referenced by the manifest.

The adapter reads these files but does not modify them or invoke MinerU.

## Output Structure

The method returns the existing `Document` dataclass with:

- `metadata` containing parser provenance;
- `pages` split from MinerU page markers;
- `sections` derived from H1 and H2 Markdown headings;
- `text_blocks` derived from ordinary page-bounded Markdown paragraphs;
- `figures` classified from image assets using conservative caption and block-type evidence;
- empty `tables` and `equations` collections in this first version.

## Field Mapping

| Document field | MinerU source | First-version mapping |
| --- | --- | --- |
| `document_id` | `metadata.json.paper_id` | Uses the stable registered Paper ID. |
| `metadata` | `metadata.json` and content JSON `parse` | Stores JSON-encoded parser provenance without changing the schema. |
| `pages` | `<!-- page n of total -->` markers | One `Page` per continuous marker range, retaining page Markdown. |
| `sections` | Markdown H1/H2 headings | One `Section` per heading with its source page. |
| `text_blocks` | Blank-line-delimited Markdown | Excludes heading-only and image-only paragraphs. IDs are deterministic within conversion order. |
| `figures` | `image_exports.json` and adjacent Markdown | Creates a Figure only when an `Image block` has an immediately following same-page numbered `Figure` or `Fig.` caption. Formula and insufficient-evidence assets are excluded. |

MinerU Image Asset is not equivalent to Scientific Figure. The classification flow is:

```text
Raw Image Asset

↓

Classification

├── Scientific Figure → Document.figures
└── Other Asset → remain only in Raw Output
```

Accepted Figure caption data is stored inside the existing JSON-encoded `Figure.content` field. It includes `caption_status`, caption text, detected Figure number, MinerU block type, and a caption source reference.

## Figure Evidence Mapping

The adapter recognizes explicit body references using reusable `Figure`, `Figures`, `Fig.`, and `Figs.` patterns. It normalizes the Figure reference before matching and retains subfigure notation such as `a`, `(a)`, `e,f`, or `b-d` as `subfigure_hint` evidence. Supplementary references such as `Figure S4b-d` are classified as `supplementary_figure`; they remain unlinked and do not create new Figures.

```text
Markdown TextBlock

↓ explicit "Fig." / "Figure" reference

Normalized Figure ID

↓

Document Figure
```

The relationship is bidirectional:

- `Figure.content.related_text_block_ids` lists body TextBlocks that explicitly cite the Figure;
- `Figure.content.textual_references` retains each detected occurrence and its subfigure hint;
- `Figure.source_reference.related_ids` mirrors the related TextBlock IDs;
- `TextBlock.source_reference.related_ids` lists resolved Figure IDs;
- `TextBlock.source_reference.figure_references` records main, supplementary, and truly unresolved detections.

Each detected reference stores:

- `reference_type`: `main_figure`, `supplementary_figure`, or `unresolved`;
- `normalized_reference`: a stable form such as `Figure 2a` or `Figure S4b-d`;
- `subfigure_hint`: the normalized subfigure or range when present;
- `status`: `resolved`, `supplementary`, or `unresolved`;
- `figure_id`: populated only for a resolved main Figure.

No Document Schema change was required. These lightweight relationship fields use the existing JSON-encoded extension points, retain the original TextBlock content, and preserve backward compatibility.

Every `source_reference` is a JSON string containing at least:

- `paper_id`
- `parser_name`
- `parser_version`
- `source_file`
- `page`
- `mineru_locator`

The locator is `null` when MinerU does not provide block-level identity. Figure references retain the exact locator.

## Current Limitations

- This implementation supports the observed MinerU 4.0.7 Flash-tier contract, not every possible MinerU output variant.
- Text paragraphs and headings have page-level evidence only because Flash output does not provide their block locators.
- Caption matching is limited to immediately following, same-page, numbered Figure captions.
- Subfigure grouping and captions separated from their image are not handled.
- Figure-to-text mapping requires an explicit textual Figure reference; it does not infer semantic relationships.
- Supplementary Figure references are classified and retained without links because supplementary Figures are not converted in the current dataset.
- Excluded image assets remain accessible only through Raw Output because the schema has no generic image element.
- Tables and equations are not extracted because the observed raw output has no explicit table or equation objects.
- Markdown heading levels deeper than H2 are not converted to sections.
- `parse()` and `validate()` remain intentionally unimplemented.
