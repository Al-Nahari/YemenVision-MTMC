
import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image

class GeM(nn.Module):
    # Generalized-Mean pooling: p=1 يطابق المتوسط، p كبير يقترب من max
    def __init__(self, p=3.0, eps=1e-6):
        super().__init__(); self.p = nn.Parameter(torch.ones(1) * p); self.eps = eps
    def forward(self, x):
        return F.avg_pool2d(x.clamp(min=self.eps).pow(self.p), (x.size(-2), x.size(-1))).pow(1.0 / self.p).flatten(1)

class ReIDNetV2(nn.Module):
    # مفاتيح الأوزان backbone.* / bn.* / classifier.* مطابقة لنموذجك القديم، فيُحمَّل مباشرة (last_stride=2, pool='avg')
    def __init__(self, n_classes, backbone='resnet50', last_stride=2, pool='avg', pretrained=False):
        super().__init__()
        weights = None
        if pretrained:
            weights = getattr(models, {'resnet18': 'ResNet18_Weights', 'resnet34': 'ResNet34_Weights', 'resnet50': 'ResNet50_Weights'}[backbone]).DEFAULT
        base = getattr(models, backbone)(weights=weights)
        if last_stride == 1:                       # خريطة ميزات أدقّ مكانياً (حيلة BoT المعروفة)
            blk = base.layer4[0]
            if hasattr(blk, 'conv3'): blk.conv2.stride = (1, 1)      # Bottleneck: الخطوة في conv2
            else: blk.conv1.stride = (1, 1)                           # BasicBlock: الخطوة في conv1
            blk.downsample[0].stride = (1, 1)
        self.dim = base.fc.in_features
        self.backbone = nn.Sequential(base.conv1, base.bn1, base.relu, base.maxpool, base.layer1, base.layer2, base.layer3, base.layer4)
        self.pool = GeM() if pool == 'gem' else nn.AdaptiveAvgPool2d(1)
        self.bn = nn.BatchNorm1d(self.dim); self.bn.bias.requires_grad_(False)     # BNNeck
        self.classifier = nn.Linear(self.dim, n_classes, bias=False)
        nn.init.normal_(self.classifier.weight, std=0.001)
    def features(self, x):
        return self.pool(self.backbone(x)).flatten(1)
    def forward(self, x):
        f = self.features(x); e = self.bn(f)
        return (f, self.classifier(e)) if self.training else e

def load_reid(path, device='cpu'):
    ck = torch.load(path, map_location='cpu', weights_only=False)
    cfg = dict(ck.get('cfg', {}))
    net = ReIDNetV2(int(cfg.get('n_cls', 2)), cfg.get('backbone', 'resnet50'), int(cfg.get('last_stride', 2)), cfg.get('pool', 'avg'))
    inc = net.load_state_dict(ck['state_dict'], strict=False)
    bad = [k for k in inc.missing_keys if k.startswith(('backbone.', 'bn.', 'pool.'))]
    if bad: raise RuntimeError('أوزان ناقصة في checkpoint: %s' % bad[:3])
    return net.to(device).eval(), tuple(cfg.get('size', (224, 224))), cfg

class _ImgDS(Dataset):
    def __init__(self, paths, size_hw):
        self.paths = list(paths)
        self.tf = transforms.Compose([transforms.Resize(tuple(size_hw)), transforms.ToTensor(),
                                      transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    def __len__(self): return len(self.paths)
    def __getitem__(self, i):
        with Image.open(self.paths[i]) as im: return self.tf(im.convert('RGB'))

@torch.no_grad()
def extract_embeddings(net, paths, size_hw, batch=128, flip=True, workers=2):
    dev = next(net.parameters()).device; net.eval(); outs = []
    for x in DataLoader(_ImgDS(paths, size_hw), batch_size=batch, shuffle=False, num_workers=workers, pin_memory=(dev.type == 'cuda')):
        x = x.to(dev, non_blocking=True)
        with torch.autocast('cuda', dtype=torch.float16, enabled=(dev.type == 'cuda')):
            f = net(x).float()
            if flip: f = f + net(torch.flip(x, dims=[3])).float()
        outs.append(F.normalize(f, dim=1).cpu())
    return torch.cat(outs).numpy()
