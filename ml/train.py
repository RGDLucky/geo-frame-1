import os
import random
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from tqdm import tqdm
from huggingface_hub import push_to_hub, create_repo
from model import CNN

def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    torch.manual_seed(config["train"]["seed"])
    random.seed(config["train"]["seed"])

    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    if config["data"]["dataset"] == "cifar10":
        train_dataset = torchvision.datasets.CIFAR10(root=config["data"]["data_dir"], train=True, download=True, transform=transform)
    else:
        raise ValueError("Unsupported dataset")

    train_loader = DataLoader(train_dataset, batch_size=config["train"]["batch_size"], shuffle=True, num_workers=config["data"]["num_workers"])

    model = CNN(input_channels=config["model"]["input_channels"], num_classes=config["model"]["num_classes"])
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=config["train"]["lr"])

    os.makedirs("checkpoints", exist_ok=True)

    for epoch in range(config["train"]["epochs"]):
        model.train()
        running_loss = 0.0
        for inputs, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}"):
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        avg_loss = running_loss / len(train_loader)
        print(f"Epoch {epoch+1}, Loss: {avg_loss:.4f}")
        torch.save(model.state_dict(), f"checkpoints/cnn_epoch_{epoch+1}.pth")

    if config["hf"]["repo_id"] is not None:
        create_repo(config["hf"]["repo_id"], exist_ok=True)
        push_to_hub(repo_id=config["hf"]["repo_id"], folder_path="checkpoints", commit_message="Initial model commit")

if __name__ == "__main__":
    main()