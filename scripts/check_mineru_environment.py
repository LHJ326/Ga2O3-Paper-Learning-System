"""Report the isolated MinerU environment without importing MinerU."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


PROJECT_PATH = Path(__file__).resolve().parents[1]


def run_command(command: list[str]) -> str | None:
    """Run a read-only system command and return normalized output."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def pip_version() -> str:
    output = run_command([sys.executable, "-m", "pip", "--version"])
    return output or "Unavailable"


def mineru_version() -> str:
    try:
        return version("mineru")
    except PackageNotFoundError:
        return "Not installed"


def gpu_information() -> str:
    if shutil.which("nvidia-smi") is None:
        return "Not detected"
    output = run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total",
            "--format=csv,noheader",
        ]
    )
    return output or "NVIDIA GPU detected, but details are unavailable"


def cuda_toolkit() -> str:
    if shutil.which("nvcc") is None:
        return "Not detected"
    output = run_command(["nvcc", "--version"])
    if output is None:
        return "Detected, but version is unavailable"
    match = re.search(r"release\s+([0-9.]+)", output)
    return match.group(1) if match else "Detected, but version is unavailable"


def main() -> None:
    in_virtual_environment = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    active_environment = os.environ.get("VIRTUAL_ENV")
    gpu = gpu_information()
    toolkit = cuda_toolkit()
    cuda_available = gpu != "Not detected" or toolkit != "Not detected"

    print(f"Python version: {platform.python_version()}")
    print(f"pip version: {pip_version()}")
    print(
        "Virtual environment path: "
        + (active_environment or (sys.prefix if in_virtual_environment else "None"))
    )
    print(f"Virtual environment status: {'Active' if in_virtual_environment else 'Inactive'}")
    print(f"Project path: {PROJECT_PATH}")
    print(f"CUDA availability: {'Available' if cuda_available else 'Not detected'}")
    print(f"CUDA toolkit version: {toolkit}")
    print(f"GPU information: {gpu}")
    print(f"MinerU version: {mineru_version()}")


if __name__ == "__main__":
    main()
