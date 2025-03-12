import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

"""Data Collection"""

df=pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/ML/Project/1722506184_hr_comma_sep/HR_comma_sep.csv")


"""Perform data quality checks by checking for missing values, if any"""
print(df.head())
print(df.describe())
# check null values
print(df.isnull().sum())

"""Understand what factors contributed most to employee turnover at EDA"""
# extract the features impacting on turnover

# print(df.groupby('left').mean())

"""Data Visualization"""