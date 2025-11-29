import torch
from torch import quantization

def quantize_sovits(model):
    """
    Applies dynamic int8 quantization to SoVITS linear layers.
    Safe and effective for CPU inference.
    """
    model.eval()

    quantized = quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},
        dtype=torch.qint8
    )

    return quantized
