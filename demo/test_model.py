import sys
import os

try:
    import torch
    from torchvision import transforms
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required module - {e}")
    print("\nPlease run this script with the Python environment that has torch installed.")
    print("For example, if you trained the model in ml/, use that Python environment:")
    print("  cd ml && python ../demo/test_model.py <image_path>")
    print("Or activate the correct virtual environment first.")
    sys.exit(1)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml'))
from model import DockClassifier


def load_model(model_path, num_classes=3, input_size=(260, 260), device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    model = DockClassifier(num_classes=num_classes, pretrained=False)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model, device


def predict_image(model, image_path, input_size=(260, 260), device=None):
    if device is None:
        device = next(model.parameters()).device

    transform = transforms.Compose([
        transforms.Resize(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    img = Image.open(image_path).convert('RGB')
    img_tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(img_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)

    class_names = ['boat_docked', 'no_boats', 'too_cloudy']
    return class_names[predicted.item()], confidence.item(), probabilities.squeeze().cpu().numpy()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_model.py <image_path>")
        print("Example: python test_model.py ../ml/data/train/no_boats/Ras_Tanura_Juaymah_5_2026426.png")
        sys.exit(1)

    image_path = sys.argv[1]
    model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'checkpoints', 'best_model.pth')

    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        print("Please train the model first using: cd ml && python train.py")
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        sys.exit(1)

    print(f"Loading model from {model_path}...")
    model, device = load_model(model_path, device=torch.device("cpu"))
    print(f"Using device: {device}")

    print(f"Running inference on {image_path}...")
    predicted_class, confidence, all_probs = predict_image(model, image_path, device=device)

    print(f"\nPrediction: {predicted_class}")
    print(f"Confidence: {confidence:.2%}")
    print(f"\nAll probabilities:")
    class_names = ['boat_docked', 'no_boats', 'too_cloudy']
    for name, prob in zip(class_names, all_probs):
        print(f"  {name}: {prob:.2%}")
