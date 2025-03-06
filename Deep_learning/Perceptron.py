import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.linear_model import Perceptron
from sklearn.model_selection import train_test_split

data = pd.read_csv("C:/Users/Chanchal Juyal/Downloads/perceptron_1740925485280/Perceptron/spambase.csv")
print(data.head())