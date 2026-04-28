import os
import json
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
from sklearn.metrics import confusion_matrix, f1_score, classification_report
import pandas as pd
from tqdm import tqdm
from model import DockClassifier
from dataset import DockDataset
import numpy as np


def train_epoch(model, loader, criterion, optimizer, device, synthetic_weight=1.0):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for inputs, labels, is_synth in tqdm(loader, desc="Training"):
        inputs, labels = inputs.to(device), labels.to(device)
        weights = torch.ones_like(labels, dtype=torch.float32, device=device)
        if synthetic_weight < 1.0:
            weights[is_synth.bool().to(device)] = synthetic_weight
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = (criterion(outputs, labels) * weights).mean()
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    return running_loss / total, 100.0 * correct / total


def eval_epoch(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for inputs, labels, _ in tqdm(loader, desc="Evaluating"):
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    return running_loss / len(all_labels), all_preds, all_labels


def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    input_size = tuple(config["model"]["input_size"])
    train_transform = transforms.Compose([
        transforms.Resize(input_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=360),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    val_transform = transforms.Compose([
        transforms.Resize(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = DockDataset(config["data"]["csv_path"], config["data"]["data_dir"], transform=train_transform)
    val_dataset = DockDataset(config["data"]["csv_path"], config["data"]["data_dir"], transform=val_transform)
    val_dataset.data = val_dataset.data[val_dataset.data['split'] == 'val']
    train_dataset.data = train_dataset.data[train_dataset.data['split'] == 'train']
    train_loader = DataLoader(train_dataset, batch_size=config["train"]["batch_size"], shuffle=True, num_workers=config["data"]["num_workers"])
    val_loader = DataLoader(val_dataset, batch_size=config["train"]["batch_size"], shuffle=False, num_workers=config["data"]["num_workers"])

    model = DockClassifier(num_classes=config["model"]["num_classes"], pretrained=True).to(device)

    class_weights = torch.tensor(config["train"]["class_weights"], device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = optim.AdamW(model.parameters(), lr=config["train"]["lr"], weight_decay=config["train"]["weight_decay"])
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config["train"]["epochs"])

    os.makedirs("checkpoints", exist_ok=True)
    best_f1 = 0.0

    for epoch in range(config["train"]["epochs"]):
        print(f"\nEpoch {epoch+1}/{config['train']['epochs']}")
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_preds, val_labels = eval_epoch(model, val_loader, criterion, device)
        val_acc = 100.0 * (np.array(val_preds) == np.array(val_labels)).sum() / len(val_labels)
        f1 = f1_score(val_labels, val_preds, average='macro')
        print(f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.2f}%, Macro F1: {f1:.4f}")
        scheduler.step()
        if f1 > best_f1:
            best_f1 = f1
            torch.save(model.state_dict(), "checkpoints/best_model.pth")
            print("Saved best model")
        torch.save(model.state_dict(), f"checkpoints/model_epoch_{epoch+1}.pth")

    print("\nFinal Evaluation:")
    model.load_state_dict(torch.load("checkpoints/best_model.pth"))
    _, val_preds, val_labels = eval_epoch(model, val_loader, criterion, device)
    print(classification_report(val_labels, val_preds, target_names=['boat_docked', 'no_boats', 'too_cloudy']))
    cm = confusion_matrix(val_labels, val_preds)
    print(f"Confusion Matrix:\n{cm}")


if __name__ == "__main__":
    main()
