# gradio_app.py

import gradio as gr
import requests
from io import BytesIO
from PIL import Image

FASTAPI_URL = "http://localhost:8001/predict"

def gradio_predict(img: Image.Image):
    """
    Sends the PIL image to the FastAPI /predict endpoint and
    returns a dict with human-readable keys.
    """
    # Encode the PIL image as PNG in memory
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # Send to FastAPI as file upload
    files = {"file": ("digit.png", buf, "image/png")}
    resp = requests.post(FASTAPI_URL, files=files)
    resp.raise_for_status()
    data = resp.json()

    # FastAPI returns {"predicted_class": int, "probability": float}
    return {
        "Digit": data["predicted_class"],
        "Confidence": f"{data['probability']:.4f}"
    }

if __name__ == "__main__":
    interface = gr.Interface(
        fn=gradio_predict,
        inputs=gr.Image(type="pil", label="Upload MNIST Digit"),
        outputs=gr.JSON(label="Prediction"),
        title="MNIST CNN Classifier (via FastAPI)",
        description="Uploads your digit to FastAPI on port 8002 for inference"
    )

    interface.launch(server_name="0.0.0.0", server_port=7861,share=True)
