# MinerU Environment Record

Record date: 2026-09-27

This record freezes the state of the MinerU environment that was manually installed by the user. Codex did not perform the successful installation.

## Environment Information

Project:

Ga2O3-Paper-Learning-System

Environment:

`.venv-mineru`

Path:

`<PROJECT_ROOT>\.venv-mineru`

OS:

Microsoft Windows 11 Home Chinese Edition, version 10.0.26200, build 26200, 64-bit

Python:

3.12.7

pip:

26.2.1

Dependency validation:

`pip check` reported: `No broken requirements found.`

## MinerU Information

Package:

MinerU

Version:

4.0.7

Installation method:

```text
python -m pip install -U "mineru>=4.0,<5"
```

Installation status:

Manual installation completed by user. User-reported installation duration was approximately 40 minutes.

## Hardware

GPU:

NVIDIA GeForce RTX 4060 Laptop GPU

VRAM:

8188 MiB

GPU driver:

610.74

CUDA:

CUDA Toolkit 12.6, nvcc V12.6.77

## Verification

CLI:

```text
mineru --version
```

Observed result:

```text
MinerU 版本: 4.0.7
Python 版本: 3.12.7
```

Import:

```text
python -c "import mineru; print('MinerU import OK')"
```

User-reported result:

```text
MinerU import OK
```

Metadata version:

```text
python -c "import importlib.metadata; print(importlib.metadata.version('mineru'))"
```

Observed result:

```text
4.0.7
```

## Dependency Snapshot

The complete output of `python -m pip freeze` from `.venv-mineru` is stored in `requirements/requirements-mineru.txt`.

- Frozen distributions: 112
- Snapshot method: read-only `pip freeze`
- MinerU entry: `mineru==4.0.7`
- No dependency was installed, removed, or upgraded while creating this record.

## Purpose

This environment is used for:

- PDF parser evaluation
- MinerU adapter development
- B01 benchmark
