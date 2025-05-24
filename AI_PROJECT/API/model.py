# model.py

import joblib
import pandas as pd
import numpy as np

# Load the serialized scikit-learn pipeline
import os
_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "titanic_pipeline.joblib")
_pipeline = joblib.load(_model_path)

def predict_passenger(data: dict) -> dict:
    """
    data keys must be exactly:
      ["pclass","sex","age","sibsp","parch","fare","embarked"]
    Returns a dict: {"survived": bool, "probability": float}
    """
    # 1) Define the feature order
    features = ["pclass","sex","age","sibsp","parch","fare","embarked"]
    # 2) Build a single-row DataFrame
    df = pd.DataFrame([data], columns=features)
    # 3) Ask the pipeline for probabilities
    proba = _pipeline.predict_proba(df)[0][1]
    survived = bool(proba >= 0.5)
    return {"survived": survived, "probability": round(proba, 3)}
