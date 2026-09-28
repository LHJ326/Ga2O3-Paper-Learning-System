# Python Environment

## Current Environment Layout

### Main Project

- Python: 3.12.7
- Main venv: `Ga2O3-Paper-Learning-System/.venv`

### MinerU

MinerU continues to use its existing independent environment. It is isolated
from both the main project environment and the OCR runtime.

### OCR Runtime

- Location: `F:\Learning\open-source-research\ocr-runtime\.venv-ocr`
- Purpose: ordinary PaddleOCR lightweight fallback for localized table crops
- Required models: `PP-OCRv6_medium_det`, `PP-OCRv6_medium_rec`
- PaddleOCR-VL: optional extreme fallback only; not installed as a default
  runtime dependency

### GPU

- NVIDIA GeForce RTX 4060 Laptop GPU

## Environment configuration

The project uses a local virtual environment at `.venv`. Create it from the project root with:

```powershell
python -m venv .venv
```

The virtual environment isolates project packages from the global Python installation.

## Activate the virtual environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```bat
.venv\Scripts\activate.bat
```

## Install requirements

After activation, install only the declared project dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Check the environment

Run the environment report from the project root:

```powershell
python scripts/check_environment.py
```

The report includes Python and pip versions, the project path, virtual-environment status, CUDA availability, and GPU information.

## Current bootstrap environment

- Platform: Microsoft Windows 11 Home Chinese Edition 10.0.26200 (64-bit)
- Python: 3.12.7
- Initial virtual-environment pip: 24.2
- Git: 2.55.0.windows.2
- CUDA Toolkit: 12.6
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8188 MiB, driver 610.74)
