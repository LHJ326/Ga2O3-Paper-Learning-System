# P001 Figure-Caption Report

## Summary

- Raw image assets: 17
- Captions matched: 6
- Unmatched assets: 11
- Suspected non-Figure assets: 11
- Detected Figure numbers: 1, 2, 3, 4, 5, 6

This is a diagnostic report for the existing P001 MinerU Flash-tier output. It is not a Benchmark score.

## Observed Caption Form

The real P001 Markdown uses the following caption form for every reliable match:

```text
Figure <number>. <caption text>
```

No reliable `Fig.` caption was observed in P001. The matcher accepts both `Figure` and `Fig.` forms, but a match is only created when the numbered caption is the immediately following Markdown block on the same page.

## Matched Figures

| Figure number | Page | MinerU locator | Match basis |
| --- | ---: | --- | --- |
| 1 | 2 | `doc:468f0b8/tier:flash/page:2/block:6` | Same-page caption immediately after image |
| 2 | 3 | `doc:468f0b8/tier:flash/page:3/block:6` | Same-page caption immediately after image |
| 3 | 4 | `doc:468f0b8/tier:flash/page:4/block:6` | Same-page caption immediately after image |
| 4 | 5 | `doc:468f0b8/tier:flash/page:5/block:6` | Same-page caption immediately after image |
| 5 | 8 | `doc:468f0b8/tier:flash/page:8/block:6` | Same-page caption immediately after image |
| 6 | 9 | `doc:468f0b8/tier:flash/page:9/block:6` | Same-page caption immediately after image |

## Suspected Non-Figure Assets

The 11 unmatched assets are treated as suspected non-Figure assets, not as confirmed classifications:

- 6 assets are explicitly labeled `Formula block` by MinerU: pages 6 (blocks 8 and 10), 7 (block 11), 8 (blocks 12 and 13), and 11 (block 55).
- 5 small `Image block` assets occur in the title or reference regions without an adjacent numbered caption: page 1 (block 3), page 11 (blocks 4 and 35), and page 12 (blocks 4 and 9).

They remain in `Document.figures` because the current schema has no generic image-asset type. Each is explicitly marked `caption_status: unmatched`; no caption or Figure number is invented.

## Matching Rules

The first mapping implementation requires all of the following:

1. The image reference and caption candidate occur within the same MinerU page range.
2. The caption candidate is the first Markdown block immediately after the image reference.
3. The candidate begins with a numbered `Figure` or `Fig.` label.
4. The image locator page agrees with its Markdown page context.
5. The caption source records the Markdown content file, page, and adjacency relation.

The implementation does not use text similarity and does not search across page boundaries.

## Stored Figure Content

Because the current `Figure` schema has no dedicated caption fields, `Figure.content` remains a JSON string and now includes:

- image path and dimensions;
- MinerU block type;
- `caption_status`;
- caption text or `null`;
- detected Figure number or `null`;
- caption source reference or `null`.

The element-level `source_reference` continues to preserve the image manifest source, page, and exact MinerU locator.

## Known Issues

- The rule does not link captions placed before images or separated by intervening blocks.
- It does not group subfigures or interpret subfigure labels.
- It does not prove that every unmatched asset is non-scientific; unmatched remains the authoritative status.
- Formula blocks remain represented as `Figure` objects until the schema gains a more suitable generic asset or equation mapping.
- Caption quality and completeness have not yet been compared with Ground Truth.
