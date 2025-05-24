# gradio_app.py

import gradio as gr
import requests

FASTAPI_URL = "http://localhost:8001/predict_passenger"

def gradio_predict(pclass, sex, age, sibsp, parch, fare, embarked):
    payload = {
        "pclass":   pclass,
        "sex":      sex,
        "age":      age,
        "sibsp":    sibsp,
        "parch":    parch,
        "fare":     fare,
        "embarked": embarked
    }
    try:
        resp = requests.post(FASTAPI_URL, json=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        survived = data.get("survived", False)
        prob     = data.get("probability", 0.0)
        return "Yes" if survived else "No", prob
    except requests.RequestException as e:
        return "Error", f"API call failed: {e}"

demo = gr.Interface(
    fn=gradio_predict,
    inputs=[
        gr.Dropdown([1, 2, 3], label="Pclass"),
        gr.Radio(["male", "female"], label="Sex"),
        gr.Slider(0, 100, step=1, label="Age"),
        gr.Number(value=0, label="Siblings/Spouses Aboard"),
        gr.Number(value=0, label="Parents/Children Aboard"),
        gr.Number(value=32.20, label="Fare"),
        gr.Dropdown(["C", "Q", "S"], label="Embarked"),
    ],
    outputs=[
        gr.Label(label="Survived?"),
        gr.Textbox(label="Probability")
    ],
    title="Titanic Survival Predictor (via FastAPI)",
    description="This UI sends inputs to FastAPI and shows the result."
)

if __name__ == "__main__":
    print(f"⚙️  Make sure FastAPI is running at {FASTAPI_URL}")
    demo.launch(server_name="0.0.0.0", server_port=7861,share=True)
