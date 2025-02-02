import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

"""Data Collection"""

df=pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/ML/ML_Steps/Advertising.csv")


"""Data Processing"""

#Explore dataset 1-view 2-check null values 3-check outlier

print(df.head(10))

print(df.info())

#check null values
print(df.isnull().sum())

#statical analysis
print(df.describe())

"""check outliers"""
plt.figure(figsize=(10,6))
sns.boxplot(data=df)
plt.title('Boxplot')
plt.show()

"""clip the outliers present in newspapaper"""

def clip_outliers(df,col):
    Q1=df[col].quantile(0.25)
    Q3=df[col].quantile(0.75)
    IQR=Q3-Q1
    lower_bound=Q1-1.5*IQR
    upper_bound=Q3+1.5*IQR
    df[col]=np.clip(df[col],lower_bound,upper_bound)
    return df
for col in ['TV','radio','newspaper']:
    df=clip_outliers(df,col)

plt.figure(figsize=(10,6))
sns.boxplot(data=df)
plt.title('Boxplot after cliping outlier')
plt.show()

"""Correletion"""

correlation_matrix=df.corr()

#Plot Correlation
plt.figure(figsize=(10,8))
sns.heatmap(correlation_matrix,annot=True,cmap='coolwarm',fmt=".2f")
plt.title("Correleation Matrix")
plt.show()

"""pairplot"""

x=df.drop('sales',axis=1)
y=df['sales'] 

sns.pairplot(df,x_vars=['TV','radio','newspaper'],y_vars='sales',kind='reg')
plt.show()


"""separet independent variable from target variable"""
#sales is dependent variable

ind_variable=df.drop('sales',axis=1)
dep_variable=df['sales']

# print(ind_variable.head())


"""Normalization and standarization
            Normalization(minmaxscaler)
                -scale data b/w 0 and 1
                -it preserve the original distribution
                -it is senstive to outliers
            Standardization(standard scaler)
                -Transform data to have mean of 0 and SD 1
                -Can be more robust to outliers
                -may not be ideal when data is not normally distributed"""
#why it is required 
"""If we have two parameters have large difference in range
            expample A - 10,20,30,40...100
                     B - 100,200,300..1000
            gradient decent will fluctuate near to minimum value of error"""
            
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
X=scaler.fit_transform(x)
# print(X)


"""Data splitting 80-20"""
from sklearn.model_selection import train_test_split
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42)

# print(X_train.shape)


"""Model Selection"""
from sklearn.linear_model import LinearRegression
model=LinearRegression()

"""Train Model"""

model.fit(X_train,y_train)
coef=model.coef_
intercept=model.intercept_
# print(intercept)
# print(coef)

"""Predict based on model"""
y_predict=model.predict(X_test)

# print(y_predict)


"""Model evalute
    calculate R2"""

from sklearn.metrics import mean_squared_error,r2_score

mse=mean_squared_error(y_test,y_predict)
r2=r2_score(y_test,y_predict)

print(f" Mean squred value is {mse},  and R-squred value is {r2}")

"""Train score ensures the model has learned patterns from the training data.
Test score ensures the model can generalize to unseen data."""

train_score=model.score(X_train,y_train)
test_score=model.score(X_test,y_test)

print(f" trainscore is {train_score},  and testscore {test_score}")