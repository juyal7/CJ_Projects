# app.py

from fastapi import FastAPI, File, UploadFile
from io import BytesIO
from PIL import Image
from model import predict_image

app = FastAPI(title="MNIST FastAPI Service", version="1.0")

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Expects form-data with an image file upload.
    Returns JSON with predicted digit and confidence.
    """
    content = await file.read()
    img = Image.open(BytesIO(content)).convert("L")
    pred, prob = predict_image(img)
    return {"predicted_class": pred, "probability": round(prob, 4)}

@app.get("/")
def read_root():
    return {"message": "POST an image to /predict to get MNIST digit prediction"}
