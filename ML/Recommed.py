import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

"""Data Collection"""

df1=pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/recomnadation/Books.csv")
df2=pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/recomnadation/Ratings.csv")
df3=pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/recomnadation/Users.csv")


"""Data Processing"""

#Explore dataset 1-view 2-check null values 3-check outlier

# print(df1.head(10))
# print(df2.head(10))
# print(df3.head(10))

# print(df1.info())
# print(df2.info())
# print(df3.info())

# #check null values
# print(df1.isnull().sum())
# print(df2.isnull().sum())
# print(df3.isnull().sum())

# #statical analysis
# print(df.describe())

# print(df1.duplicated().sum())
# print(df2.duplicated().sum())
# print(df3.duplicated().sum())
