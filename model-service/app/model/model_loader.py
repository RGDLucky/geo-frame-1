import os
from pathlib import Path
from typing import Optional
import torch
from torchvision import transforms
from PIL import Image
from io import BytesIO
from app.model.dock_classifier import DockClassifier, CLASS_NAMES, IMAGENET_MEAN, IMAGENET_STD


class ModelLoader:
    _instance: Optional["ModelLoader"] = None
    _model: Optional[DockClassifier] = None
    _device: Optional[torch.device] = None
    _input_size: tuple[int, int] = (260, 260)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_path: Optional[str] = None,
        input_size: tuple[int, int] = (260, 260),
        device: Optional[str] = None,
    ):
        if self._model is not None:
            return

        if model_path is None:
            ml_dir = Path(__file__).parent.parent.parent / "ml"
            model_path = ml_dir / "checkpoints" / "best_model.pth"

        if device is None:
            device = os.getenv("MODEL_DEVICE", "cpu")

        self._model_path = model_path
        self._input_size = input_size
        self._device = torch.device(
            "cuda" if device == "cuda" and torch.cuda.is_available()
            else "mps" if device == "mps" and torch.backends.mps.is_available()
            else "cpu"
        )

        self._transform = transforms.Compose([
            transforms.Resize(input_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])

    def _ensure_model_loaded(self) -> None:
        if self._model is not None:
            return

        if not os.path.exists(self._model_path):
            raise FileNotFoundError(f"Model not found at {self._model_path}")

        self._model = DockClassifier(num_classes=3, pretrained=False)
        state_dict = torch.load(self._model_path, map_location=self._device, weights_only=True)
        self._model.load_state_dict(state_dict)
        self._model.to(self._device)
        self._model.eval()

    def predict(self, image_source) -> dict:
        self._ensure_model_loaded()

        if isinstance(image_source, bytes):
            img = Image.open(BytesIO(image_source)).convert("RGB")
        elif isinstance(image_source, str):
            img = Image.open(image_source).convert("RGB")
        else:
            raise ValueError("image_source must be bytes or file path")

        img_tensor = self._transform(img).unsqueeze(0).to(self._device)

        with torch.no_grad():
            outputs = self._model(img_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)

        class_name = CLASS_NAMES[predicted.item()]
        confidence_val = confidence.item()
        all_probs = probabilities.squeeze().cpu().numpy().tolist()

        return {
            "class_name": class_name,
            "confidence": confidence_val,
            "probabilities": all_probs,
        }

    @property
    def device(self) -> torch.device:
        self._ensure_model_loaded()
        return self._device

    @property
    def is_loaded(self) -> bool:
        return self._model is not None
