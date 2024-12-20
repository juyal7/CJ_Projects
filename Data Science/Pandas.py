import pandas as pd
import numpy as np
import os
file_path="C:/Users/Chanchal Juyal/Desktop/My Work/ipl_data.xlsx"
data=pd.read_excel(file_path)
print(data)
# if os.path.exists(file_path):
#        print("yes")
# else:
#        print("no")       
# print(type(data))
# print(data.head(5))
# print(data.info())

"""mean median of all numeric values"""
# print(data.describe())

""" Accessing 1 coloumn"""
# print(data["winner"])

"""Accessing Multiple Coloumn"""
# print(data[["winner","team1"]])


"""Access data by row"""
# print(data.iloc[0:2])

"""Access data by row and coloumn"""
# print(data.iloc[0:2, 0:2])

"""Accessing rows on givin condition"""

# mask=data["city"]=="Hyderabad" #Condition or filter

# #will give boolean
# print(mask)

# #will give data on condition
# print(data[mask])


# """create a function"""

# def get_city(city_name):
#     mask=data["city"]==city_name
#     return data[mask].shape[0]

# get_city("Hyderabad")

# """Two conditions"""
# mask1=data["city"]=="Hyderabad"
# mask2=data["date"]> '2020-01-01'

# hyd_csk=(data[mask1 & mask2])  #mask1 and mask2 are boolen that's why we will use bitwise opertor
# print(hyd_csk)


"""To find the count for particular colomn"""
# winner=data['winner'].value_counts()
# print(winner)


"""Data visualisation"""
import matplotlib.pyplot as plt
# data['winner'].value_counts().plot(kind='bar')


# data["toss_decision"].value_counts().plot(kind="pie")
# plt.show()   

# data["win_by_runs"].plot(kind="hist")
# plt.show()


"""Operations on Series"""

# my_series=data["winner"].value_counts()
# a=my_series.index
# b=my_series.values
# c=my_series.shape
# d=my_series.head(5)
# e=my_series.tail(5)
# f=my_series.sort_values(ascending=True)
# print(f)

# combine=data["team1"].value_counts() + data["team2"].value_counts() #addition of two series
# print(combine.sort_values(ascending=False).head(5))
# combine.sort_values('city',ascending=False,inplace=True) #inplace for parmanent changes
"""Shorting by 2 conditions"""
# data.sort_values(['city','date'],ascending=[True,False])
# print(data)

"""Remove"""
# data.drop_duplicates(subset=['city']).shape
# print(data)

# print(data.head(5))
# dummy_variable=pd.get_dummies(data,columns=['city'],dtype=int)
# print(data.head(5))
# print(dummy_variable)

# from sklearn.preprocessing import LabelEncoder
# le=LabelEncoder()
# data['city']=le.fit_transform(data['city'])
# print((le))
# data1={"Name":['a','b','c']
#        ,"Year":[2018,2019,2015]
#        }

# df_age=pd.DataFrame(data1)
# print(df_age)
# import datetime as date
# current_year=2024
# df_age[current_year]=2024
# df_age['Age']=current_year-df_age['Year']
# print(df_age)