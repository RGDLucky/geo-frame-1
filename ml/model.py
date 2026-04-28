import torch
import torch.nn as nn
import torchvision.models as models


class DockClassifier(nn.Module):
    def __init__(self, num_classes=3, pretrained=True, dropout=0.3):
        super().__init__()
        self.backbone = models.efficientnet_b2(pretrained=pretrained)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.dropout1 = nn.Dropout(dropout)
        self.bn = nn.BatchNorm1d(in_features)
        self.fc1 = nn.Linear(in_features, 512)
        self.relu = nn.ReLU()
        self.dropout2 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.backbone.features(x)
        x = self.global_pool(x)
        x = torch.flatten(x, 1)
        x = self.dropout1(x)
        x = self.bn(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        return x


def get_model(num_classes=3, pretrained=True):
    return DockClassifier(num_classes=num_classes, pretrained=pretrained)
