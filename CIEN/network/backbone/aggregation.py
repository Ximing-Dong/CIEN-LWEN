import torch
from torch import nn
import math
import numpy as np

BN_MOMENTUM = 0.1


class DeformConv(nn.Module):
    def __init__(self, chi, cho, use_dcn=True):
        super(DeformConv, self).__init__()
        self.actf = nn.Sequential(
            nn.BatchNorm2d(cho, momentum=BN_MOMENTUM),
            nn.ReLU(inplace=True)
        )
        if use_dcn:
            from ..DCNv2_latest.dcn_v2 import DCN
            self.conv = DCN(chi, cho, kernel_size=(3, 3), stride=1, padding=1, dilation=1, deformable_groups=1)
            # from mmcv.ops import ModulatedDeformConv2dPack as DCN
            # self.conv = DCN(chi, cho, kernel_size=(3, 3), stride=1, padding=1, dilation=1, deform_groups=1)
        else:
            self.conv = nn.Conv2d(chi, cho, kernel_size=(3, 3), stride=1, padding=1, dilation=1)

    def forward(self, x):
        x = self.conv(x)
        x = self.actf(x)
        return x

def fill_fc_weights(layers):
    for m in layers.modules():
        if isinstance(m, nn.Conv2d):
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)

def fill_up_weights(up):
    w = up.weight.data
    f = math.ceil(w.size(2) / 2)
    c = (2 * f - 1 - f % 2) / (2. * f)
    for i in range(w.size(2)):
        for j in range(w.size(3)):
            w[0, 0, i, j] = \
                (1 - math.fabs(i / f - c)) * (1 - math.fabs(j / f - c))
    for c in range(1, w.size(0)):
        w[c, 0, :, :] = w[0, 0, :, :]


class IDAUp(nn.Module):
    def __init__(self, o, channels, up_f, use_dcn=True):
        super(IDAUp, self).__init__()
        for i in range(1, len(channels)):
            c = channels[i]
            f = int(up_f[i])
            proj = DeformConv(c, o, use_dcn=use_dcn)
            node = DeformConv(o, o, use_dcn=use_dcn)

            up = nn.ConvTranspose2d(o, o, f * 2, stride=f,
                                    padding=f // 2, output_padding=0,
                                    groups=o, bias=False)
            fill_up_weights(up)

            setattr(self, 'proj_' + str(i), proj)
            setattr(self, 'up_' + str(i), up)
            setattr(self, 'node_' + str(i), node)

    def forward(self, layers, startp, endp):
        for i in range(startp + 1, endp):
            upsample = getattr(self, 'up_' + str(i - startp))
            project = getattr(self, 'proj_' + str(i - startp))
            layers[i] = upsample(project(layers[i]))
            node = getattr(self, 'node_' + str(i - startp))
            layers[i] = node(layers[i] + layers[i - 1])

#chanels=[16,32,64,128,256,512]
class DLAUp(nn.Module):
    def __init__(self, startp, channels, scales, in_channels=None, use_dcn=True):
        super(DLAUp, self).__init__()
        self.startp = startp#2
        if in_channels is None:
            in_channels = channels
        self.channels = channels #[64,128,256,512]
        channels = list(channels)
        scales = np.array(scales, dtype=int) #[1,2,4,8]
        for i in range(len(channels) - 1):#0
            j = -i - 2 #-2
            setattr(self, 'ida_{}'.format(i),
                    IDAUp(channels[j], in_channels[j:],
                          scales[j:] // scales[j], use_dcn=use_dcn))
            scales[j + 1:] = scales[j]
            in_channels[j + 1:] = [channels[j] for _ in channels[j + 1:]]

    def forward(self, layers):
        out = [layers[-1]]  # start with 32
        for i in range(len(layers) - self.startp - 1):
            ida = getattr(self, 'ida_{}'.format(i))
            ida(layers, len(layers) - i - 2, len(layers))
            out.insert(0, layers[-1])
        return out