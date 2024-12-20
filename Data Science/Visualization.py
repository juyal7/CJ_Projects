import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# x=np.linspace(0,10,100)
# y=np.sin(x)
# plt.plot(x,y)
# plt.plot(x, y, 'o')
# plt.xlabel('x-axis')
# plt.ylabel('y-axis')
# plt.title('Sine Wave')
# plt.grid(True)
# plt.show()


#generate bar chart
# x=np.array(["A","B","C","D"])
# y=np.array([3,8,1,10])
# color=np.array(["red", "green", "blue", "yellow"])
# plt.figure(figsize=(2, 2))
# plt.bar(x,y,color=color,width=0.5)
# plt.show()


#Box Plot
#required 
# data=[-1000,1,2,3,4,5,6,7,8,9,100,1000]
# data1=[-20,1,2,3,4,5,6,7,8,9,20]
# data1.sort()
# Q1=np.percentile(data1,25)
# Q2 =np.percentile(data1, 50)
# Q3=np.percentile(data1, 75)
# #INTER QUARTILE range
# IQR=Q3-Q1
# Uper_bound=Q3+1.5*IQR
# Lower_bound=Q1-1.5*IQR
# plt.boxplot(data1)
# plt.show()

#radar chart
# categories = ['Speed', 'Strength', 'stamina', 'agility', 'Technique']
# categories=["bandwidth","letency","multi_user"]
# LTE=[10,15,25]
# NR=[1000,10,100]
# # Values=[7,8,9,10,11]
# angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
# # data=np.concatenate((Values, [Values[0]]))
# LTE=np.concatenate((LTE, [LTE[0]]))
# NR=np.concatenate((NR, [NR[0]]))
# angle=np.concatenate((angles, [angles[0]]))
# plt.polar(angle, LTE, marker='o')
# plt.polar(angle, NR, marker='o')
# plt.fill(angle, LTE, alpha=0.3)
# plt.fill(angle, NR, alpha=0.3)
# plt.title('Radar Chart')
# plt.show()



# data={
#     "months":["a","b","c"],
#     "sale1":[20,30,40],
#     "Sale2":[100,200,300]
#     }
# df=pd.DataFrame(data)
# print(df)

# df.plot(kind="area",stacked=True)
# plt.show()


#Tree Maps


# data=[("a","b",1),("c","d",2),("e","f",3)]
# print(data[0][0])
# print(data[1][0])
# print(data[2][0])
# print(data[0][1])

# for i in data:
#     for j in i:
#         print(j)
#         print("\n")


# df =pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Lesson_05_Data_Visualization/Dataset/ADANIPORTS.csv")
# print(df.head(5))

# x=np.linspace(0, 10, 100)
# y=np.linspace(0, 20, 100)

# xx,yy=np.meshgrid(x, y)
# z=np.sin(xx)+np.cos(yy)
# fig=plt.figure()
# ax=fig.add_subplot(111, projection='3d')
# ax.plot_surface(xx, yy, z, cmap="viridis")
# plt.show()

# sns.regplot(x="win_by_runs", y="win_by_wickets", data=data)

