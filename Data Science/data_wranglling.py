import pandas as pd
import numpy as np
data = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Lesson_09_Data_Wrangling/HousePrices.csv")
# print(data.head(10))
# print(data.tail(10))
# print(data.info())
# print(data.describe())
# print(data.shape)
# print(data.iloc(1))
# print(data.loc[1])
# print(data.loc[1:5])
# print(data.iloc[:5,:3])
"""2,5,8 row and 0,3,6th coloumn"""
# print(data.iloc[[2,5,8], [0,3,6]])

"""habndle missing values in data"""
# print(data.isnull().sum())
# print(data.notnull().sum())
# print(data.notna().sum())

"""duplicate values"""
# print(data.drop_duplicates())

"""data cleaning"""
# print(data.duplicated().sum())
# print(data.drop_duplicates(inplace=True))

"""data transformation"""

if 'price' in data.columns:
    data['Log_price']=data['price'].apply(lambda x: np.log(x))
    
import matplotlib.pyplot as plt
import seaborn as sns
# sns.histplot(data['price'], kde=True)
# plt.show()
sns.histplot(data['Log_price'], kde=True)
plt.show()

"""data normalization"""
# from sklearn.preprocessing import MinMaxScaler


"""Handling outliers"""
winsorization=data['price'].quantile(0.99)

result=pd.merge(data[data['price']<winsorization], data[data['price']>winsorization], how='outer')