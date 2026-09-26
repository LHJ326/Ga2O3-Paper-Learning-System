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
- `figures` derived from the image export manifest;
- empty `tables` and `equations` collections in this first version.

## Field Mapping

| Document field | MinerU source | First-version mapping |
| --- | --- | --- |
| `document_id` | `metadata.json.paper_id` | Uses the stable registered Paper ID. |
| `metadata` | `metadata.json` and content JSON `parse` | Stores JSON-encoded parser provenance without changing the schema. |
| `pages` | `<!-- page n of total -->` markers | One `Page` per continuous marker range, retaining page Markdown. |
| `sections` | Markdown H1/H2 headings | One `Section` per heading with its source page. |
| `text_blocks` | Blank-line-delimited Markdown | Excludes heading-only and image-only paragraphs. IDs are deterministic within conversion order. |
| `figures` | `image_exports.json` | Joins locator, page, filename, MIME type, and dimensions; verifies the image file exists. |

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
- Figure assets are converted without caption classification or subfigure grouping.
- Image assets are not assumed to be scientific figures; the schema currently has no generic image element.
- Tables and equations are not extracted because the observed raw output has no explicit table or equation objects.
- Markdown heading levels deeper than H2 are not converted to sections.
- `parse()` and `validate()` remain intentionally unimplemented.
