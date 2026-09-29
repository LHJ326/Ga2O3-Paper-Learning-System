# Git History Cleanup Report

## Safety Record

- Original branch: `master`
- Original HEAD: `e368b619b7f9221f70e881de6b727ef4e1377ffb`
- Original worktree status: clean
- Original packed repository size: 25.46 MiB (`914` packed objects)
- Complete backup bundle:
  `<PRIVATE_BACKUP_ROOT>\before-phase-6.3-e368b619-20260929.bundle`
- Bundle verification: complete history, `master` and `HEAD` present
- Local ZIP backup:
  `<PRIVATE_BACKUP_ROOT>\local-assets-before-phase-6.3`

No history-changing command was run until the original ref, clean status, and
verified bundle were recorded.

## Historical Large-File Audit

The audit inspected every reachable blob, archive extensions, common model and
cache extensions, and blobs of at least 100,000 bytes. The following paths were
removed from every ref:

| Historical path | Blob size | Original introducing commit | Decision |
| --- | ---: | --- | --- |
| `data/benchmark/B02/B02.pdf` | 7,107,290 bytes | `40f38c07eb39a36472b2d8705dcbddf58810e971` | Remove: third-party paper PDF |
| `data/benchmark/B01/B01.pdf` | 3,417,943 bytes | `2f39f7962e0e37c4a1c5a431604fcc2a34411aff` | Remove: third-party paper PDF |
| `data/papers/P001.pdf` | 3,100,033 bytes | `c96b7ca30c4899ed3811442677249b783126dc52` | Remove: third-party paper PDF |
| `data/parsed/B02/mineru/raw/zip/B02.zip` | 6,577,370 bytes | `4ba460351be154bf339d1e5de9bda8b3e8101790` | Remove: bundled MinerU raw archive |
| `data/parsed/B01/mineru/raw/zip/B01.zip` | 3,595,697 bytes | `2f39f7962e0e37c4a1c5a431604fcc2a34411aff` | Remove: bundled MinerU raw archive |

The five removed blobs total 23,798,333 bytes. The local PDFs and ZIPs were not
deleted: their SHA-256 values were recorded before filtering, and the same
values were verified after the ZIPs were restored from the safety copy. Archive
extensions are now ignored so these local inputs do not re-enter history.

## Retained Fixtures

The audit retained source code, documentation, requirements, schemas, YAML,
JSON, tests, and the evidence-bearing parsed-image fixtures. In particular,
`data/parsed/B01/mineru/inspection/model_output.json` remains because it is an
auditable parser fixture rather than a temporary cache. No tracked TAR, 7Z,
RAR, model-weight, virtual-environment, or temporary-cache payload was found.

## Rewrite

History was rewritten with `git-filter-repo` 2.47.0 using exact path filters
and `--invert-paths`. The first rewritten tip after filtering was
`d263cc4c3a1c43186196a53b9317cdc33bc784e6`. No remote was configured, so no
remote ref was changed or force-pushed.

## Post-Rewrite Verification

- Packed repository size after filtering: 4.76 MiB (`900` packed objects)
- Pack reduction: approximately 20.70 MiB (about 81%)
- Reachable PDF paths: none
- Reachable ZIP paths: none
- Reachable `.env` paths: none
- Local PDF/ZIP content hashes: unchanged
- `git diff --check`: passed
- Full test suite: `208 passed in 2.13s`

The backup bundle intentionally retains the original private history and must
not be published. Collaborators must re-clone after any later force-push of the
rewritten history.
