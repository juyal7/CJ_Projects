import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.linear_model import Perceptron
from sklearn.model_selection import train_test_split

data = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Deep_Learning/Day2/perceptron_1740925485280/Perceptron/spambase.csv")
# print(data.head())

if data.isnull().values.any():
    data = data.fillna(0)
df_x = data.iloc[:,:-1]
df_y = data.iloc[:,-1]

x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.4, random_state=4)

from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
x_train_scaled = scaler.fit_transform(x_train)
x_test_scaled = scaler.transform(x_test)


per = Perceptron()
per.fit(x_train_scaled, y_train)

pred_train = per.predict(x_train_scaled)
pred_test = per.predict(x_test_scaled)


from sklearn.metrics import accuracy_score

accuracy_train = accuracy_score(y_train, pred_train)
accuracy_test = accuracy_score(y_test, pred_test)
print("Accuracy on training data: ", accuracy_train)
print("Accuracy on test data: ", accuracy_test)