# Git History Cleanup Plan

## Status

Executed locally in Phase 6.3 after explicit approval. The original history is
preserved in a verified offline bundle, and no remote was configured or pushed.
See `docs/GIT_HISTORY_CLEANUP_REPORT.md` for the exact paths, original commits,
size change, backup location, and verification results.

## Audit Findings

The current `HEAD` does not track source PDFs, `.env`, FAISS indexes, model
weights, or local virtual environments. The full Git object graph still retains
three removed paper PDFs:

| Historical path | Blob size | First relevant milestone |
| --- | ---: | --- |
| `data/benchmark/B02/B02.pdf` | 7,107,290 bytes | `40f38c0` |
| `data/benchmark/B01/B01.pdf` | 3,417,943 bytes | `2f39f79` |
| `data/papers/P001.pdf` | 3,100,033 bytes | `c96b7ca` |

Total historical PDF payload: 13,625,266 bytes. Commit `5374c51` removed these
paths from the current tree, but ordinary deletion does not remove their blobs
from earlier commits or from a public clone.

Other large research-derived artifacts remain in the current history and need
a redistribution decision before publication:

| Path | Approximate size | Current role |
| --- | ---: | --- |
| `data/parsed/B02/mineru/raw/zip/B02.zip` | 6.58 MB | Frozen B02 Raw Output |
| `data/parsed/B01/mineru/raw/zip/B01.zip` | 3.60 MB | Frozen B01 Raw Output |
| `data/parsed/B01/mineru/inspection/model_output.json` | 2.76 MB | Parser inspection fixture |
| `data/parsed/**/images/*` | Multiple files | Figure/parser fixtures |

These are not model weights, but they may contain content derived from
third-party papers. Their size is acceptable to Git, while their redistribution
status—not merely file size—must be reviewed.

The history scan found no `.env`, FAISS/index database, or recognized model
weight extension. API-key-like matches were limited to README placeholders and
test fake-key fixtures; no real key was identified by the path-only scan.

## Required Decision

At minimum, remove all three PDF paths from every ref before a public push.
Separately decide whether frozen ZIP, image, text, JSON, Ground Truth, and
benchmark artifacts may legally be redistributed. If not, replace them with
synthetic or independently licensed fixtures and remove the originals from all
refs as part of the same rewrite.

## Proposed Safe Procedure

Perform these steps only after explicit approval:

1. Stop all writes and coordinate with every collaborator.
2. Create an offline mirror backup of all branches and tags.
3. Record the pre-rewrite refs and verify the backup can be cloned.
4. Install and use `git filter-repo` in a disposable mirror clone.
5. Remove the three exact PDF paths from all refs with `--invert-paths`.
6. Add any research-derived paths rejected by the redistribution review to the
   same filtering operation.
7. Rescan all objects for PDFs, secrets, model weights, and oversized blobs.
8. Clone the rewritten repository into a fresh directory and repeat
   `docs/INSTALL_TEST.md`, including the full pytest suite.
9. Compare tags, branch tips, release documentation, and benchmark fixtures.
10. Only then replace the remote refs with a coordinated force push.
11. Ask collaborators to reclone instead of merging old history.

Do not run reflog expiration or garbage collection on the original repository
until the rewritten clone, backup, and clean-install verification are accepted.

## Example Filter Scope (Not Executed)

```text
data/benchmark/B01/B01.pdf
data/benchmark/B02/B02.pdf
data/papers/P001.pdf
```

The exact `git filter-repo` command must be reviewed at execution time and run
only against a disposable mirror. This plan intentionally does not provide an
automatic cleanup script because a history rewrite is destructive and changes
every affected commit ID.

## Publication Gate

The repository must remain private or local until:

- the PDF blobs are absent from every ref;
- derived fixture redistribution is approved or the fixtures are replaced;
- secret and large-object scans are clean;
- a fresh clone installs successfully; and
- tests pass without relying on unpublished files.
