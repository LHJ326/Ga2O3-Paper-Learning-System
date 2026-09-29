# v0.1.0 Final Release Check Report

## Release Candidate

- Phase 6.4 base commit: `20d55e568b58a73f2d8e19a7ce807ca0f3c5369d`
- Final report commit: the commit containing this file,
  `docs: complete final release check`
- Branch: `master`
- Package version: `0.1.0`
- Required Python: `>=3.12`
- Verification interpreter: Python 3.12.7 on Windows

## Clean-Clone Installation

The repository was cloned with `git clone --no-local` into a previously absent
temporary directory. The clone did not reuse the project's `.venv`; a new
virtual environment was created inside the temporary clone.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- pip upgraded successfully from 24.2 to 26.2.1.
- Editable package build and installation succeeded.
- `pip check`: `No broken requirements found.`
- Clean-clone tests: `205 passed, 3 skipped`.
- Fully provisioned development workspace: `208 passed`.

The three clean-clone skips are intentional external-resource checks: the
separate MinerU environment, the user-provided P001 PDF, and the user-provided
B02 PDF used by the OCR cache-hit integration test.

## Public-Repository Safety Scan

The committed release tree contains 316 tracked files. The tracked-file audit
found:

- `.env`: none
- PDF: none
- ZIP/archive bundle: none
- Python/test/build cache: none
- credential-shaped `sk-` value: none
- repository-specific absolute local path: none
- tracked file larger than 3 MiB: none

`git grep -n "DEEPSEEK_API_KEY"` matched only the documented environment
variable name, adapter lookup, connection checks, and tests using
`test-only-key`. `git grep -n "sk-"` matched ordinary English fragments such as
`task-specific` and `Disk-space`; the stricter credential-shaped scan returned
zero matches. No real API key or token was found.

Three provenance-only local path strings in frozen JSON fixtures were replaced
with repository-relative paths or explicit placeholders. Their integrity
manifests and snapshot hashes were updated; OCR tokens, bounding boxes, parsed
text, Ground Truth, and benchmark meaning were unchanged.

## Documentation Review

The following release documents exist and are mutually consistent:

- `README.md`: Python 3.12+, editable install, pytest, external resources,
  security policy, roadmap, and MIT license.
- `docs/ARCHITECTURE.md`: current Ingestion through Evidence-aware Retrieval
  module boundaries; no LLM answer-generation claim.
- `LICENSE`: MIT License for original project code and documentation.
- `docs/INSTALL_TEST.md`: reproducible clean-install workflow and expected
  external-resource skips.

## External Resources

The public repository intentionally excludes paper PDFs, MinerU ZIP archives,
`.env`, API keys, model weights, local vector indexes, and virtual environments.
Users must supply research papers lawfully and prepare MinerU or ordinary OCR
runtimes separately when those paths are exercised. Real DeepSeek calls require
a user-managed `DEEPSEEK_API_KEY`; release verification made no API call.

## Known Limitations

- v0.1.0 validates a P001-centered evidence and Paper Object workflow; it is not
  yet a production multi-paper corpus.
- MinerU and OCR are external runtimes and are not installed by the editable
  package workflow.
- Embedding and retrieval foundations use deterministic/mock vectors for
  interface validation, not production semantic ranking.
- RAG returns evidence-aware retrieval results but has no LLM answer-generation
  layer.
- Uncertain extracted knowledge remains review-required by design.

## Release Decision

The isolated installation, dependency check, tests, tracked-file scan, secret
scan, history cleanup, and documentation review pass. The repository is ready
to proceed to a separately authorized GitHub `v0.1.0` release operation. This
check does not create a tag, push a remote, or start Phase 7.
