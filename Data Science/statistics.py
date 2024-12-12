import pandas as pd
import numpy as np
import random 
import matplotlib.pyplot as plt

list1=[]

for i in range(1000):
    list1.append(random.randint(1,6))

s=(pd.Series(list1).value_counts()/pd.Series(list1).value_counts().sum()).sort_index()
s.plot(kind="bar")
plt.show()


list2=[]
for i in range(10000):
    a=random.randint(1,6)
    b=random.randint(1,6)
    list2.append(a+b)
s1=(pd.Series(list2).value_counts()/pd.Series(list2).value_counts().sum()).sort_index()
s1.plot(kind="bar")
plt.show()



    
