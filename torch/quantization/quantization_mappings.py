import torch
from torch import nn

import torch.nn.functional as F
import torch.nn.intrinsic as nni
import torch.nn.intrinsic.quantized as nniq
import torch.nn.intrinsic.qat as nniqat
import torch.nn.quantized as nnq
import torch.nn.quantized.dynamic as nnqd
import torch.nn.qat as nnqat

from .stubs import QuantStub, DeQuantStub

# Default map for swapping float module to quantized ones
DEFAULT_STATIC_QUANT_MODULE_MAPPINGS = {
    QuantStub: nnq.Quantize,
    DeQuantStub: nnq.DeQuantize,
    nn.BatchNorm2d: nnq.BatchNorm2d,
    nn.BatchNorm3d: nnq.BatchNorm3d,
    nn.Conv1d: nnq.Conv1d,
    nn.Conv2d: nnq.Conv2d,
    nn.Conv3d: nnq.Conv3d,
    nn.ConvTranspose1d: nnq.ConvTranspose1d,
    nn.ConvTranspose2d: nnq.ConvTranspose2d,
    nn.ELU: nnq.ELU,
    nn.Embedding: nnq.Embedding,
    nn.EmbeddingBag: nnq.EmbeddingBag,
    nn.GroupNorm: nnq.GroupNorm,
    nn.Hardswish: nnq.Hardswish,
    nn.InstanceNorm1d: nnq.InstanceNorm1d,
    nn.InstanceNorm2d: nnq.InstanceNorm2d,
    nn.InstanceNorm3d: nnq.InstanceNorm3d,
    nn.LayerNorm: nnq.LayerNorm,
    nn.LeakyReLU: nnq.LeakyReLU,
    nn.Linear: nnq.Linear,
    nn.ReLU6: nnq.ReLU6,
    nn.ReLU: nnq.ReLU,
    # Wrapper Modules:
    nnq.FloatFunctional: nnq.QFunctional,
    # Intrinsic modules:
    nni.BNReLU2d: nniq.BNReLU2d,
    nni.BNReLU3d: nniq.BNReLU3d,
    nni.ConvReLU1d: nniq.ConvReLU1d,
    nni.ConvReLU2d: nniq.ConvReLU2d,
    nni.ConvReLU3d: nniq.ConvReLU3d,
    nni.LinearReLU: nniq.LinearReLU,
    nniqat.ConvBn2d: nnq.Conv2d,
    nniqat.ConvBnReLU2d: nniq.ConvReLU2d,
    nniqat.ConvReLU2d: nniq.ConvReLU2d,
    nniqat.LinearReLU: nniq.LinearReLU,
    # QAT modules:
    nnqat.Linear: nnq.Linear,
    nnqat.Conv2d: nnq.Conv2d,
}

# Default map for swapping float module to qat modules
DEFAULT_QAT_MODULE_MAPPINGS = {
    nn.Conv2d: nnqat.Conv2d,
    nn.Linear: nnqat.Linear,
    # Intrinsic modules:
    nni.ConvBn2d: nniqat.ConvBn2d,
    nni.ConvBnReLU2d: nniqat.ConvBnReLU2d,
    nni.ConvReLU2d: nniqat.ConvReLU2d,
    nni.LinearReLU: nniqat.LinearReLU
}

# Default map for swapping dynamic modules
DEFAULT_DYNAMIC_QUANT_MODULE_MAPPINGS = {
    nn.GRUCell: nnqd.GRUCell,
    nn.Linear: nnqd.Linear,
    nn.LSTM: nnqd.LSTM,
    nn.LSTMCell: nnqd.LSTMCell,
    nn.RNNCell: nnqd.RNNCell,
}

# Whitelist for propagating the qconfig
_EXCLUDE_QCONFIG_PROPAGATE_LIST = {
    DeQuantStub,
}
_INCLUDE_QCONFIG_PROPAGATE_LIST = {
    nn.Sequential,
}

# Default mapping from floating point function or torch ops to quantized ops
# TODO: merge with default static mapping
DEFAULT_FLOAT_TO_QUANTIZED_OPERATOR_MAPPINGS = {
    F.elu: torch._ops.ops.quantized.elu,
    F.hardswish: torch._ops.ops.quantized.hardswish,
    F.instance_norm: torch._ops.ops.quantized.instance_norm,
    F.layer_norm: torch._ops.ops.quantized.layer_norm,
    F.leaky_relu: torch._ops.ops.quantized.leaky_relu,
}

def get_default_static_quant_module_mappings():
    ''' Get module mapping for post training static quantization
    '''
    return DEFAULT_STATIC_QUANT_MODULE_MAPPINGS

def get_static_quant_module_class(float_module_class):
    ''' Get the statically quantized module class corresponding to
    the floating point module class
    '''
    static_quant_module_class = DEFAULT_STATIC_QUANT_MODULE_MAPPINGS.get(float_module_class, None)
    assert static_quant_module_class is not None, \
        'Floating point module class {}'.format(float_module_class) + \
        ' does not have a corresponding quantized module class'
    return static_quant_module_class

def get_default_qat_module_mappings():
    ''' Get default module mapping for quantization aware training
    '''
    return DEFAULT_QAT_MODULE_MAPPINGS

def get_default_dynamic_quant_module_mappings():
    ''' Get module mapping for post training dynamic quantization
    '''
    return DEFAULT_DYNAMIC_QUANT_MODULE_MAPPINGS

def get_default_qconfig_propagation_list():
    ''' Get the default list of module types that we'll attach qconfig
    attribute to in prepare
    '''
    QCONFIG_PROPAGATE_MODULE_CLASS_LIST = (
        (set(DEFAULT_STATIC_QUANT_MODULE_MAPPINGS.keys()) |
         set(DEFAULT_QAT_MODULE_MAPPINGS.keys()) |
         set(DEFAULT_DYNAMIC_QUANT_MODULE_MAPPINGS.keys()) |
         _INCLUDE_QCONFIG_PROPAGATE_LIST) -
        _EXCLUDE_QCONFIG_PROPAGATE_LIST
    )
    return QCONFIG_PROPAGATE_MODULE_CLASS_LIST

def get_default_compare_output_module_list():
    ''' Get list of module class types that we will record output
    in numeric suite
    '''
    NUMERIC_SUITE_COMPARE_MODEL_OUTPUT_MODULE_LIST = (
        set(DEFAULT_STATIC_QUANT_MODULE_MAPPINGS.values())
        | set(DEFAULT_QAT_MODULE_MAPPINGS.values())
        | set(DEFAULT_DYNAMIC_QUANT_MODULE_MAPPINGS.values())
        | set(DEFAULT_STATIC_QUANT_MODULE_MAPPINGS.keys())
        | set(DEFAULT_QAT_MODULE_MAPPINGS.keys())
        | set(DEFAULT_DYNAMIC_QUANT_MODULE_MAPPINGS.keys())
        | _INCLUDE_QCONFIG_PROPAGATE_LIST
    ) - _EXCLUDE_QCONFIG_PROPAGATE_LIST
    return NUMERIC_SUITE_COMPARE_MODEL_OUTPUT_MODULE_LIST

# TODO: merge with get_static_quant_module_class
def get_quantized_operator(float_op):
    ''' Get the quantized operator corresponding to the float operator
    '''
    quantized_op = DEFAULT_FLOAT_TO_QUANTIZED_OPERATOR_MAPPINGS.get(float_op, None)
    assert quantized_op is not None, \
        'Operator {} does not have corresponding quantized op'.format(float_op)
    return quantized_op
