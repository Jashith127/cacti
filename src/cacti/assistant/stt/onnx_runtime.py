from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OnnxRuntimeChoice:
    providers: tuple[str, ...]
    using_cuda: bool


def available_onnx_providers() -> tuple[str, ...]:
    try:
        import onnxruntime as ort
    except ImportError:
        return ()
    return tuple(ort.get_available_providers())


def prefer_gpu_providers(*, force_cpu: bool | None = None) -> OnnxRuntimeChoice:
    """CUDA first when onnxruntime reports CUDAExecutionProvider, else CPU."""
    if force_cpu is None:
        force_cpu = os.environ.get("CACTI_ASR_DEVICE", "").strip().lower() == "cpu"
    available = available_onnx_providers()
    if not force_cpu and "CUDAExecutionProvider" in available:
        providers = ("CUDAExecutionProvider", "CPUExecutionProvider")
        return OnnxRuntimeChoice(providers=providers, using_cuda=True)
    if not force_cpu and "DmlExecutionProvider" in available:
        return OnnxRuntimeChoice(
            providers=("DmlExecutionProvider", "CPUExecutionProvider"),
            using_cuda=False,
        )
    return OnnxRuntimeChoice(providers=("CPUExecutionProvider",), using_cuda=False)
