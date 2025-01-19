# Import necessary libraries
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.model_selection import KFold, StratifiedKFold, LeaveOneOut
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

data = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/ML/Hitters.csv")
print(data.tail(10))
