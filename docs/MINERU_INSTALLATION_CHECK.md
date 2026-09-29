# MinerU Installation Check

Verification date: 2026-09-26

Scope: read-only compatibility review. MinerU was not installed or executed, no model was downloaded, and the Python/CUDA environments were not modified.

## Current Environment

OS:

Microsoft Windows 11 Home Chinese Edition, version 10.0.26200, build 26200, 64-bit

Python:

Python 3.12.7

GPU:

NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB VRAM, driver 610.74

CUDA:

CUDA Toolkit 12.6 (nvcc V12.6.77)

Virtual Environment:

`<PROJECT_ROOT>\.venv` (active and isolated from the system Python)

Additional capacity observations:

- System RAM: 31.73 GiB total; 15.37 GiB free at inspection time
- F drive: 963.53 GiB free at inspection time
- WSL command: present; distribution and GPU readiness not verified
- Docker command: not found

## MinerU Requirements

The current official documentation describes MinerU 4.0. Version-specific dependency resolution must be repeated immediately before installation.

### Python Compatibility

- Supported Python versions: `>=3.10,<3.15` for the MinerU 4.0 package.
- Compatibility notes: Python 3.12 is the official practical starting point for a new environment.
- Optional Torch, vLLM, and LMDeploy engines have narrower wheel, operating-system, driver, and Python constraints; base-package compatibility does not guarantee every optional engine works.
- Current Python 3.12.7 is compatible with the package-level range. Exact optional-engine compatibility remains conditional until a version is frozen and dependency metadata is resolved.

### Installation Method

Recommended installation methods by purpose:

| Method | Official position | Project assessment |
|---|---|---|
| pip / uv | Official quick start recommends the MinerU 4.x package in an activated Python 3.12 virtual environment; pip is documented as an alternative to uv. | Preferred for the first controlled evaluation, in a dedicated MinerU environment with an exact version frozen after resolution. |
| conda | Not presented as the primary MinerU 4.0 installation path in the reviewed official quick-start material. | Do not choose without separate official compatibility evidence. |
| docker | Official NVIDIA workflow targets Linux and WSL2 on Windows. Current images have their own CUDA runtime and driver requirements. | Consider only after WSL2, Docker, NVIDIA container support, image version, and disk usage are verified. Docker is not currently available on this host. |
| source | Officially supported from a 4.0 repository checkout for development. | Not recommended for the first benchmark because it weakens reproducibility and is outside the current no-clone constraint. |

### CUDA and GPU

- CUDA requirement: the base package can use ONNX/CPU and llama.cpp; CUDA is not mandatory for every workflow.
- GPU requirement: GPU acceleration depends on the selected backend. MinerU 4.0 documents vLLM for Linux and LMDeploy for the Windows `full` extra.
- Memory consideration: official runtime guidance states that 8 GB VRAM is only a planning starting point, not a guarantee for all Standard/Advanced workloads. High-throughput local deployment is advised to have at least 16 GB system memory.
- Current assessment: 31.73 GiB system RAM is adequate for planning; 8188 MiB VRAM is a boundary configuration and carries out-of-memory and throughput risk.
- CUDA compatibility: installed CUDA Toolkit 12.6 alone does not prove optional-engine compatibility. Prebuilt wheels and containers depend on their bundled runtime and the NVIDIA driver. The current official Docker examples use CUDA 13.0 or an alternate CUDA 12.9 image, so the Docker path is not yet verified for this host.

### Model Download

- Flash/native text parsing can operate without inference models when explicitly configured for the PDF text layer.
- Basic requires the selected small-model bundle: `MinerU-4_models_onnx` or `MinerU-4_models_torch`.
- Standard requires the selected small-model bundle plus VLM weights. The VLM repository varies by engine, such as llama.cpp GGUF/mmproj or original VLM weights.
- Advanced uses the Standard deployment models; the official documentation does not define a separate Advanced download tier.
- Approximate size: the reviewed official documentation does not publish one stable consolidated download size. Size must be measured from the exact frozen version, backend, tier, and model manifest before approval.
- Storage requirement: model storage defaults under the user profile. For this project, a future approved installation should explicitly place the model directory on the F drive and record before/after disk usage. No directory was created in this phase.
- First model-backed parsing may trigger downloads unless models are explicitly prepared and local-only behavior is configured.

### Windows Compatibility

- Native Windows support: documented for the base package with ONNX/CPU and llama.cpp; the Windows `full` extra uses LMDeploy.
- WSL recommendation: official NVIDIA Docker deployment targets Linux, including WSL2 on Windows. The `wsl.exe` command exists on this host, but WSL distribution, version, storage, networking, and GPU passthrough are not verified.
- Docker option: official Docker deployment is available for NVIDIA GPUs under Linux/WSL2, but Docker is not currently installed or discoverable on this host.
- Native Windows is therefore the lowest-change first evaluation path. WSL2/Docker remains a conditional fallback rather than the starting choice.

## Compatibility Analysis

| Item | Requirement | Current | Status |
|---|---|---|---|
| Python | MinerU 4.0 package: `>=3.10,<3.15`; optional engines require compatible wheels. | Python 3.12.7 in project `.venv`. | Package-level compatible; optional engines conditional. |
| CUDA | Not required for base ONNX/CPU + llama.cpp; backend-specific for acceleration. | CUDA Toolkit 12.6; driver 610.74. | Conditional; base path does not require CUDA, accelerated path not yet verified. |
| GPU | Backend-supported NVIDIA GPU; 8 GB VRAM is a planning starting point, not a guarantee. | RTX 4060 Laptop GPU, 8188 MiB VRAM. | Conditional/high risk for memory-intensive engines. |
| OS | Base package supports Windows; NVIDIA Docker path targets Linux/WSL2. | Windows 11 64-bit; WSL command present; Docker absent. | Native base path compatible; Docker path not ready. |
| Storage | Exact requirement depends on tier, backend, models, caches, and container images. | F drive has 963.53 GiB free; official total model size not specified. | Capacity appears sufficient, but size must be measured before download. |

## Installation Decision

Recommended approach:

Do not install in this phase. When installation is explicitly approved, use a separate, ignored Python 3.12 environment for a pinned MinerU 4.x release. Start with the native Windows base package and explicit ONNX small-model plus llama.cpp VLM configuration. Place all model storage on the F drive and record exact package/model versions and disk use. Consider Windows `full`/LMDeploy or WSL2/Docker only if the base B01 result or performance requires it.

Reason:

This path matches the current OS and Python, minimizes changes to the established project `.venv`, avoids treating CUDA 12.6 as proof of engine compatibility, and creates the simplest rollback boundary. It also allows B01 correctness to be measured before adopting a higher-complexity GPU serving stack.

Risk:

- MinerU and optional-engine versions are not yet frozen.
- Model download size is not officially consolidated and could consume significant storage or bandwidth.
- The 8 GB GPU is a boundary configuration and may encounter out-of-memory or poor-throughput behavior.
- Native Windows optional-engine wheels may impose additional constraints.
- Docker is absent and WSL2 GPU readiness is unverified.
- Installing into the existing project `.venv` could create dependency conflicts, so that approach is not recommended.

## Official Sources

- [MinerU 4.0 Quick Start](https://opendatalab.github.io/MinerU/quick_start/)
- [MinerU Extension Modules](https://opendatalab.github.io/MinerU/quick_start/extension_modules/)
- [MinerU Tiers and Runtimes](https://opendatalab.github.io/MinerU/usage/tiers/)
- [MinerU Model Downloads and Configuration](https://opendatalab.github.io/MinerU/usage/model_source/)
- [MinerU Docker Deployment](https://opendatalab.github.io/MinerU/quick_start/docker_deployment/)
- [MinerU FAQ](https://opendatalab.github.io/MinerU/faq/)
