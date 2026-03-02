# model.py

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import os

# 1. Define the CNN
class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))

wget https://github.com/your-repo/mnist_cnn.pth -O mnist_cnn.pth
# 2. Load model + weights
_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
_model = CNN().to(_device)
model_path = "mnist_cnn.pth"
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model weights file '{model_path}' not found. Please download or train the model first.")
_model.load_state_dict(torch.load(model_path, map_location=_device))
_model.eval()

# 3. Preprocessing pipeline
_transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((28, 28)),
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

def predict_image(img: Image.Image):
    """
    Takes a PIL image, applies transforms, 
    runs the CNN, and returns (pred_int, prob_float).
    """
    x = _transform(img).unsqueeze(0).to(_device)
    with torch.no_grad():
        logits = _model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
    pred = int(np.argmax(probs))
    prob = float(np.max(probs))
    return pred, prob
