
import matplotlib.pyplot as plt
import pandas as pd
data=pd.read_excel("C:/Users/Chanchal Juyal/Desktop\My Work/Ipl_data.xlsx")
# fig=px.histogram(data,x="winner",y="winner",color="winner",title="IPL Winner")
# fig=px.choropleth_map(data, locations="winner", color="winner", title="IPL Winner")
# fig=px.pie(data, names="winner", title="IPL Winner")
# fig.show()


print(data)
"generate json data"
# import json
# data1=data.to_json()
# print(data1)

"""BoxPlot"""


df=pd.DataFrame(data)
print(df)