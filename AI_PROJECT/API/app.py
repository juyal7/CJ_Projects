# fastapp_api.py

from fastapi import FastAPI
from pydantic import BaseModel, Field
from model import predict_passenger  # or inline predict logic

class Passenger(BaseModel):
    pclass:   int   = Field(..., ge=1, le=3, description="Ticket class (1 = 1st)")
    sex:      str   = Field(..., pattern="^(male|female)$")
    age:      float = Field(..., gt=0)
    sibsp:    int   = Field(..., ge=0, description="# siblings / spouses aboard")
    parch:    int   = Field(..., ge=0, description="# parents / children aboard")
    fare:     float = Field(..., ge=0)
    embarked: str   = Field(..., pattern="^(C|Q|S)$", description="Port: C=Cherbourg, Q=Queenstown, S=Southampton")

class Prediction(BaseModel):
    survived:    bool
    probability: float

app = FastAPI(title="Titanic Survival Predictor", version="1.0")

@app.post("/predict_passenger", response_model=Prediction)
def predict(passenger: Passenger):
    result = predict_passenger(passenger.dict())
    return Prediction(**result)

@app.get("/")
def read_root():
    return {"message": "POST to /predict for JSON predictions"}
