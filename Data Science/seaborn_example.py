import seaborn as sns
import matplotlib.pyplot as plt
sns.set_theme()
tips = sns.load_dataset("tips")
# print(tips.head(5))
# sns.relplot(
#     data=tips,
#     x="total_bill", y="tip", col="day",hue="sex",style="day"
# )

# sns.lmplot(data=tips, x="total_bill", y="tip", col="day", hue="smoker")

# sns.regplot(data=tips, x="total_bill", y="tip", hue="smoker")
# sns.FacetGrid(tips, col="time", row="smoker",hue="sex")
# plt.show()

"""swarm Plot"""
# sns.set_theme(style="ticks")
# sns.swarmplot(data=tips, x="day", y="total_bill", hue="sex")
# plt.title("Swarm Plot")
# plt.xlabel("Day")
# plt.ylabel("Total Bill")
# plt.show()


"""3D plots"""

from mpl_toolkits.mplot3d import Axes3D
iris=sns.load_dataset("iris")
fig=plt.figure()
ax=fig.add_subplot(111, projection='3d')
ax.scatter(iris['sepal_length'],iris['sepal_width'],iris['petal_length'],c=iris['species'].map({'setosa':0,'versicolor':1,'virginica':2}))
plt.show()