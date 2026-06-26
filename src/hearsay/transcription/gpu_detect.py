"""Detect CUDA GPU availability and recommend model/compute_type.

Detection here is deliberately decoupled from PyTorch. The component that
actually runs inference is CTranslate2 (via faster-whisper), which has its own
CUDA runtime and *no* torch dependency. So we probe CTranslate2 directly for
CUDA usability and use ``nvidia-smi`` (which ships with the NVIDIA driver) to
read the GPU name and VRAM for model-tier selection. PyTorch is never imported.
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass

from hearsay.constants import (
    DEFAULT_CPU_COMPUTE,
    DEFAULT_CPU_MODEL,
    DEFAULT_GPU_COMPUTE,
    DEFAULT_GPU_MODEL,
)

log = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU detection result."""

    cuda_available: bool
    gpu_name: str
    vram_gb: float
    recommended_model: str
    recommended_compute: str
    recommended_device: str


def _ctranslate2_cuda_count() -> int | None:
    """Number of CUDA devices CTranslate2 can use, or None if it can't tell.

    This is the authoritative probe: it reflects whether the *inference engine*
    can initialize CUDA, not merely whether a GPU exists. Returns None (rather
    than 0) when CTranslate2 itself can't be queried, so callers can distinguish
    "no CUDA" from "couldn't check."
    """
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count()
    except Exception:
        log.debug("Could not query CTranslate2 CUDA device count", exc_info=True)
        return None


def _query_nvidia_smi() -> tuple[str, float]:
    """Return (gpu_name, vram_gb) from nvidia-smi, or ("", 0.0) if unavailable.

    nvidia-smi is installed alongside the NVIDIA driver, so this works without
    any Python GPU packages. We read only the first GPU.
    """
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            # Don't pop a console window when frozen with PyInstaller --windowed.
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        log.debug("nvidia-smi not available", exc_info=True)
        return "", 0.0

    if out.returncode != 0 or not out.stdout.strip():
        return "", 0.0

    first_line = out.stdout.strip().splitlines()[0]
    parts = [p.strip() for p in first_line.split(",")]
    if len(parts) < 2:
        return "", 0.0

    name = parts[0]
    # memory.total is reported in MiB with nounits.
    match = re.search(r"[\d.]+", parts[1])
    vram_mib = float(match.group()) if match else 0.0
    return name, round(vram_mib / 1024, 1)


def _recommend_model(vram_gb: float) -> str:
    """Pick a Whisper model size from available VRAM."""
    if vram_gb >= 6:
        return DEFAULT_GPU_MODEL
    if vram_gb >= 2:
        return "small.en"
    return "tiny.en"


def detect_gpu() -> GPUInfo:
    """Detect CUDA GPU and return a model/device recommendation."""
    name, vram_gb = _query_nvidia_smi()
    ct2_count = _ctranslate2_cuda_count()

    if name:
        log.info("NVIDIA GPU found via nvidia-smi: %s (%.1f GB VRAM)", name, vram_gb)
    if ct2_count is not None:
        log.info("CTranslate2 reports %d CUDA device(s)", ct2_count)

    # Authoritative: trust CTranslate2 when it can be queried. Otherwise fall
    # back to "a GPU exists per nvidia-smi" and let the engine's runtime
    # fallback catch a missing CUDA library at load time.
    if ct2_count is not None:
        cuda_usable = ct2_count > 0
    else:
        cuda_usable = bool(name)

    if name and ct2_count == 0:
        log.warning(
            "NVIDIA GPU detected but CTranslate2 cannot initialize CUDA. "
            "GPU inference needs the CUDA libraries (nvidia-cublas-cu12, "
            "nvidia-cudnn-cu12). Falling back to CPU."
        )

    if cuda_usable:
        # If nvidia-smi gave us no VRAM (rare), assume a capable card.
        model = _recommend_model(vram_gb) if vram_gb else DEFAULT_GPU_MODEL
        return GPUInfo(
            cuda_available=True,
            gpu_name=name or "NVIDIA GPU",
            vram_gb=vram_gb,
            recommended_model=model,
            recommended_compute=DEFAULT_GPU_COMPUTE,
            recommended_device="cuda",
        )

    return GPUInfo(
        cuda_available=False,
        gpu_name="",
        vram_gb=0,
        recommended_model=DEFAULT_CPU_MODEL,
        recommended_compute=DEFAULT_CPU_COMPUTE,
        recommended_device="cpu",
    )
