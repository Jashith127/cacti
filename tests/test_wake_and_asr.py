from __future__ import annotations

from cacti.assistant.stt.onnx_runtime import prefer_gpu_providers
from cacti.assistant.stt.vad import EnergyVAD


def _loud_block(n: int = 480) -> list[float]:
    return [0.2] * n


def _quiet_block(n: int = 480) -> list[float]:
    return [0.001] * n


def test_vad_starts_after_consecutive_loud_frames():
    vad = EnergyVAD(start_frames=3, hangover_frames=4)
    assert vad.feed(_quiet_block()) is None
    assert vad.feed(_loud_block()) is None
    assert vad.feed(_loud_block()) is None
    assert vad.feed(_loud_block()) == "start"


def test_vad_ends_after_hangover_silence():
    vad = EnergyVAD(start_frames=1, hangover_frames=3)
    assert vad.feed(_loud_block()) == "start"
    assert vad.feed(_quiet_block()) is None
    assert vad.feed(_quiet_block()) is None
    assert vad.feed(_quiet_block()) == "end"
    assert vad.speaking is False


def test_prefer_cuda_when_provider_listed(monkeypatch):
    monkeypatch.delenv("CACTI_ASR_DEVICE", raising=False)
    monkeypatch.setattr(
        "cacti.assistant.stt.onnx_runtime.available_onnx_providers",
        lambda: ("CUDAExecutionProvider", "CPUExecutionProvider"),
    )
    choice = prefer_gpu_providers()
    assert choice.using_cuda
    assert choice.providers[0] == "CUDAExecutionProvider"


def test_force_cpu_even_if_cuda_present(monkeypatch):
    monkeypatch.setenv("CACTI_ASR_DEVICE", "cpu")
    monkeypatch.setattr(
        "cacti.assistant.stt.onnx_runtime.available_onnx_providers",
        lambda: ("CUDAExecutionProvider", "CPUExecutionProvider"),
    )
    choice = prefer_gpu_providers()
    assert not choice.using_cuda
    assert choice.providers == ("CPUExecutionProvider",)
