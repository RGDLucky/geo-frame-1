import os
import pandas as pd
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image


class DockDataset(Dataset):
    def __init__(self, csv_file, data_dir, transform=None, input_size=(260, 260)):
        self.data = pd.read_csv(csv_file)
        self.data_dir = data_dir
        self.input_size = input_size
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize(input_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        img_path = os.path.join(self.data_dir, row['image_path'])
        label = int(row['label'])
        is_synthetic = row.get('is_synthetic', False)

        img = Image.open(img_path).convert('RGB')

        if self.transform:
            img = self.transform(img)

        return img, label, float(is_synthetic)
