# MinerU Setup Notes

Status: preparation only; MinerU is not installed.

Complete this record before changing the Python environment or downloading any model.

## Version

- Candidate version family: MinerU 4.x
- Package range in current official quick start: `>=4.0,<5`
- Exact version: not frozen
- Release date:
- Source reference: https://opendatalab.github.io/MinerU/quick_start/
- Verification date: 2026-09-26

## Python Compatibility

- Supported Python versions: `>=3.10,<3.15`
- Compatibility with project Python 3.12.7: compatible at package level
- Optional-engine compatibility: pending exact-version wheel resolution
- Required virtual environment changes: none made; a separate MinerU environment is recommended
- Verification source: official Quick Start and Extension Modules documentation

## CUDA Requirement

- CPU support: yes, through base-package ONNX/CPU and llama.cpp paths
- CUDA required or optional: optional for the base path; backend-specific for acceleration
- Supported CUDA versions: must be verified against the frozen engine/wheel or container
- GPU memory guidance: 8 GB is a planning starting point, not a guarantee
- Compatibility with current CUDA 12.6 and RTX 4060 Laptop GPU: conditional; not yet proven by installation or inference
- Verification source: official Tiers, Extension Modules, and Docker documentation

## Installation Method

- Official installation method: package installation with uv; pip documented as an alternative
- Preferred project method: native Windows base package in a separate Python 3.12 environment
- Package or distribution source: official Python package index source, exact version to be frozen
- Expected dependencies: base ONNX/llama.cpp stack; optional Torch/LMDeploy only if separately approved
- Expected model downloads: selected small-model bundle plus VLM weights for Standard tier
- Disk-space estimate: not quantified in reviewed official documentation; must be measured before download
- Model storage target: explicit F-drive location, to be approved before creation
- Rollback plan: remove the dedicated environment and model directory after preserving manifests and logs

## Known Issues

- Windows-specific issues: optional Windows `full` engine uses LMDeploy and requires compatible wheels
- Python-version issues: optional engines may support a narrower range than MinerU itself
- CUDA or GPU issues: 8 GB VRAM may be insufficient for some workloads; CUDA toolkit version alone does not establish compatibility
- Model-download issues: first model-backed parse may download weights; local-only readiness must be configured and verified
- Parsing limitations relevant to B01: unknown until the B01 benchmark is executed
- License or data-handling concerns: license and model-source terms must be reviewed with the exact frozen version

## Installation Decision

Recommended approach:

Use a separate, ignored Python 3.12 environment and start with a pinned MinerU 4.x base package on native Windows. Use explicit ONNX small-model and llama.cpp VLM settings, with model storage redirected to the F drive. Escalate to LMDeploy or WSL2/Docker only if B01 quality or runtime evidence requires it.

Reason:

The base path is compatible with the current Python and documented Windows support while minimizing dependency, CUDA, Docker, and rollback risk.

Risk:

Exact model size, optional-engine wheel compatibility, 8 GB VRAM behavior, and B01 quality remain unverified. No installation should begin until the MinerU version and model manifest are frozen and storage/download impact is approved.

# Environment Preparation

Base environment:

`.venv`

MinerU environment:

`.venv-mineru`

Python:

3.12.7

Purpose:

Keep MinerU dependencies isolated.

Preparation result:

- Environment path: `F:\Learning\Ga2O3-Paper-Learning-System\.venv-mineru`
- Initial pip version: 24.2
- Isolation check: `sys.prefix` points to `.venv-mineru`; `sys.base_prefix` points to the system Python
- Installed MinerU packages: none
- Installed PyTorch packages: none
