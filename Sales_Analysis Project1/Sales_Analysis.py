import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

data = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Project2/AusApparalSales4thQrt2020.csv")
# print(data.tail(10))

class data_wranglling():
    def __init__(self,data):
        self.data=data
        self.data=data.isna().sum()
        self.data=data.notna().sum()
        self.data=data.dropna()
        self.data=data.drop_duplicates()
        
        """Choose a suitable data wrangling technique—either data standardization or normalization. 
        Execute the preferred normalization method and present the resulting data. 
        (Normalization is the preferred approach for this problem.)"""
        
    def Normalization(self):
        from sklearn.preprocessing import MinMaxScaler
        scaler=MinMaxScaler()
        data['NormalisedPrice']=scaler.fit_transform(data[['Sales']])
        print(data.head(10))
        sns.histplot(data['NormalisedPrice'], kde=True)
        plt.show()
        sns.histplot(data['Sales'], kde=True)
        plt.show()
        return data     
    
    """Share your insights regarding the application of the GroupBy() function 
    for either data chunking or merging, and offer a recommendation based on your analysis."""  
    def groupby(self):
        print(data.groupby('Group')['Sales'].sum())
        print(data.groupby('Group')['Sales'].var())
        print(data.groupby('Group')['Sales'].describe())
        

class data_analysis():
    """Perform descriptive statistical analysis on the data in the 
    Sales and Unit columns. Utilize
    techniques such as mean, median, mode, and standard 
    deviation for this analysis"""
    def statistical_analysis_sales(self, data):
        self.data=data
        return data['Sales'].describe()
    def statistical_analysis_unit(self, data):
        self.data=data
        return data['Unit'].describe()    
    
    """Identify the group with the highest sales and the group with the 
    lowest sales based on the data provided."""
    def highest_sales(self, data):
        self.data=data
        return data.groupby('Group')['Sales'].sum().sort_values(ascending=False).head(1)
    
    def lowest_sales(self, data):
        self.data=data
        return data.groupby('Group')['Sales'].sum().sort_values(ascending=True).head(1)
    
    """Generate weekly, monthly, and quarterly reports to document 
    and present the results of the analysis conducted."""
    def weekly__report(self, data):
        self.data=data
        data['Date']=pd.to_datetime(data['Date'])
        data['Week']=data['Date'].dt.isocalendar().week
        data['Month']=data['Date'].dt.month
        data['Quarter']=data['Date'].dt.quarter
        return data.groupby('Week')['Sales'].sum()
    
    def Monthly_report(self, data):
        self.data=data
        data['Date']=pd.to_datetime(data['Date'])
        data['Month']=data['Date'].dt.month
        return data.groupby('Month')['Sales'].sum()
    
    def quarterly_report(self, data):
        self.data=data
        data['Date']=pd.to_datetime(data['Date'])
        data['Quarter']=data['Date'].dt.quarter
        return data.groupby('Quarter')['Sales'].sum()
        
class data_visualization():
    """State-wise sales analysis for different demographic groups (kids, women, men, and seniors)"""
    def state_wise_sales(self, data):
        self.data=data
        return data.groupby('State')['Sales'].sum().sort_values(ascending=False).head(10)
        """plot"""
        

    """Sales analysis for different product groups (men, women, and kids)"""
    def product_wise_sales(self, data):
        self.data=data
        return data.groupby('Product')['Sales'].sum().sort_values(ascending=False).head(10)
    
    """visualization"""
    def visualization(self, data):
            plt.figure(figsize=(15, 6))
            data = data.pivot_table(
                    values='Sales',
                    index='State',
                    columns='Group',
                    aggfunc='sum'
                                ).round(2)
            data.plot(kind='bar', stacked=True, width=0.8)
            plt.title('Sales by State and Group')
            plt.xlabel('State')
            plt.ylabel('Sales')
            plt.legend(title='Group')
            # plt.tight_layout()
            plt.show()
            

class reprot_generation():
    pass


# obj1=data_wranglling(data)
obj1=data_visualization()
t1=obj1.visualization(data)
