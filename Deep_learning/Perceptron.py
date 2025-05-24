import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.linear_model import Perceptron
from sklearn.model_selection import train_test_split

# data = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Deep_Learning/Day2/perceptron_1740925485280/Perceptron/spambase.csv")
# # print(data.head())

# if data.isnull().values.any():
#     data = data.fillna(0)
# df_x = data.iloc[:,:-1]
# df_y = data.iloc[:,-1]

# x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.4, random_state=4)

# from sklearn.preprocessing import StandardScaler

# scaler = StandardScaler()
# x_train_scaled = scaler.fit_transform(x_train)
# x_test_scaled = scaler.transform(x_test)


# per = Perceptron()
# per.fit(x_train_scaled, y_train)

# pred_train = per.predict(x_train_scaled)
# pred_test = per.predict(x_test_scaled)


# from sklearn.metrics import accuracy_score

# accuracy_train = accuracy_score(y_train, pred_train)
# accuracy_test = accuracy_score(y_test, pred_test)
# print("Accuracy on training data: ", accuracy_train)
# print("Accuracy on test data: ", accuracy_test)


def sigmoid(z):
    return 1/(1+np.exp(-z))

def relu(z, deriv = False):
    if(deriv): #this is for the partial derivatives (discussed in next blog post)
        return z>0
    else:
        return np.multiply(z, z>0)

def initialise_parameters(layers_units):
    #layers_units is a list consisting of number of units in each layer
    parameters = {}         # create a dictionary containing the parameters
    for l in range(1, len(layers_units)):
        #initialise weights randomly to break symmetry.
        parameters['W' + str(l)] = 0.001* np.random.randn(layers_units[l],
                                            layers_units[l-1])
        parameters['b' + str(l)] = np.zeros((layers_units[l],1))
    return parameters


def forward_propagation(X,parameters,linear):
    cache = {}
    L = len(parameters)//2 #final layer
    cache["A0"] = X #ease of notation since input = layer 0
    for l in range(1, L):
        cache['Z' + str(l)] = np.dot(parameters['W' + str(l)], cache['A' + str(l-1)])
        + parameters['b' + str(l)]
        cache['A' + str(l)] = relu(cache['Z' + str(l)])
    #final layer
    cache['Z' + str(L)] = np.dot(parameters['W' + str(L)],
    cache['A' + str(L-1)]) + parameters['b' + str(L)]
    #depending on if linear or logistic regression
    #apply activation function to final layer or not
    cache['A' + str(L)] =cache['Z' + str(L)] if linear else sigmoid(cache['Z' + str(L)])
    return cache

