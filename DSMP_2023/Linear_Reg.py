import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

df =pd.read_csv("G:/My Drive/ML/placement.csv")
# print(df.head())

plt

x=df.iloc[:,0:1]
y=df.iloc[:,-1]

from sklearn.model_selection import train_test_split
X_train,X_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=2)
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import SGDRegressor
sg=SGDRegressor()
lr=LinearRegression()
lr.fit(X_train,y_train)
sg.fit(X_train,y_train)

# print((lr.predict(X_test).reshape(40,1)),y_test)
plt.scatter(df['cgpa'],df['package'])
plt.plot(X_train,lr.predict(X_train))
plt.plot(X_train,sg.predict(X_train))
plt.show()
