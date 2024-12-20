import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

data = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Project2/AusApparalSales4thQrt2020.csv")
print(data.tail(10))

# class data_wranglling():
#     def __init__(self,data):
#         self.data=data
#         self.data=data.isna().sum()
#         self.data=data.notna().sum()
#         self.data=data.dropna()
#         self.data=data.drop_duplicates()
        
#         """Choose a suitable data wrangling technique—either data standardization or normalization. 
#         Execute the preferred normalization method and present the resulting data. 
#         (Normalization is the preferred approach for this problem.)"""    
    
#     def Normalization(self):
#         from sklearn.preprocessing import MinMaxScaler
#         scaler=MinMaxScaler()
#         data['NormalisedPrice']=scaler.fit_transform(data[['Sales']])
#         print(data.head(10))
#         sns.histplot(data['NormalisedPrice'], kde=True)
#         plt.show()
#         sns.histplot(data['Sales'], kde=True)
#         plt.show()
#         return data     
    
#     """Share your insights regarding the application of the GroupBy() function 
#     for either data chunking or merging, and offer a recommendation based on your analysis."""  
#     def groupby(self):
#         print(data.groupby('Group')['Sales'].sum())
#         print(data.groupby('Group')['Sales'].var())
#         print(data.groupby('Group')['Sales'].describe())
        

# class data_analysis():
#     """Perform descriptive statistical analysis on the data in the 
#     Sales and Unit columns. Utilize
#     techniques such as mean, median, mode, and standard 
#     deviation for this analysis"""
#     def statistical_analysis_sales(self, data):
#         self.data=data
#         return data['Sales'].describe()
    
#     def statistical_analysis_unit(self, data):
#         self.data=data
#         return data['Unit'].describe()    
    
#     """Identify the group with the highest sales and the group with the 
#     lowest sales based on the data provided."""
#     def highest_sales(self, data):
#         self.data=data
#         return data.groupby('Group')['Sales'].sum().sort_values(ascending=False).head(1)
    
#     def lowest_sales(self, data):
#         self.data=data
#         return data.groupby('Group')['Sales'].sum().sort_values(ascending=True).head(1)
    
#     """Generate weekly, monthly, and quarterly reports to document 
#     and present the results of the analysis conducted."""
#     def weekly__report(self, data):
#         self.data=data
#         data['Date']=pd.to_datetime(data['Date'])
#         data['Week']=data['Date'].dt.isocalendar().week
#         data['Month']=data['Date'].dt.month
#         data['Quarter']=data['Date'].dt.quarter
#         return data.groupby('Week')['Sales'].sum()
    
#     def Monthly_report(self, data):
#         self.data=data
#         data['Date']=pd.to_datetime(data['Date'])
#         data['Month']=data['Date'].dt.month
#         return data.groupby('Month')['Sales'].sum()
    
#     def quarterly_report(self, data):
#         self.data=data
#         data['Date']=pd.to_datetime(data['Date'])
#         data['Quarter']=data['Date'].dt.quarter
#         return data.groupby('Quarter')['Sales'].sum()
        
# class data_visualization():
#     """State-wise sales analysis for different demographic groups (kids, women, men, and seniors)"""
#     def state_wise_sales(self, data):
#         self.data=data
#         return data.groupby('State')['Sales'].sum().sort_values(ascending=False).head(10)

#     """Sales analysis for different product groups (men, women, and kids)"""
#     def product_wise_sales(self, data):
#         self.data=data
#         return data.groupby('Product')['Sales'].sum().sort_values(ascending=False).head(10) 
    
#     """visualization"""
#     def visualization(self, data):
#             data = data.pivot_table(
#                     values='Sales',
#                     index='State',
#                     columns='Group',
#                     aggfunc='sum'
#                                 )
#             data.plot(kind='bar', stacked=True)
#             plt.title('Sales by State and Group')
#             plt.xlabel('State')
#             plt.ylabel('Sales')
#             plt.legend(title='Group')
#             plt.show()       
    
#     """Time-of-the-day analysis: Identify peak and off-peak 
#     sales periods to facilitate strategic planning for S&M teams"""
#     def visualize_Time_of_the_day(self,data):
#         self.data=data
#         top_periods = (data.groupby('Time', observed=True)['Sales']
#                       .agg('sum')                                
#                       .nlargest(10))
#         print(top_periods)
#         fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
#         bars = ax.bar(range(len(top_periods)), top_periods.values)
#         plt.tight_layout()
#         plt.show()

# class My_Dashboard():
#     def create_sales_dashboard(self, data):
#         """
#         Create a comprehensive sales dashboard with daily, weekly, monthly, and quarterly views.
        
#         Args:
#             data (pd.DataFrame): Input DataFrame containing Date and Sales columns
#         """
#         # Ensure Date column is datetime
#         data['Date'] = pd.to_datetime(data['Date'])
        
#         # Create date-based features
#         data['Week'] = data['Date'].dt.isocalendar().week
#         data['Month'] = data['Date'].dt.month
#         data['Quarter'] = data['Date'].dt.quarter
        
#         # Create subplots for the dashboard
#         """Total Size of the deshboard"""
#         fig = plt.figure(figsize=(10, 9))
#         """creates a 2×2 grid layout"""
#         gs = fig.add_gridspec(2, 2, hspace=0.5, wspace=0.5)
        
#         # Daily Sales Chart
#         ax1 = fig.add_subplot(gs[0, 0])
#         daily_sales = data.groupby('Date')['Sales'].sum()
#         ax1.bar(daily_sales.index, daily_sales.values, linewidth=10)    
#         ax1.set_title('Daily Sales Trend')
#         ax1.set_xlabel('Date',labelpad=1)
#         ax1.set_ylabel('Sales (*$10^6)')
#         ax1.tick_params(axis='x', rotation=45, labelsize=5)
        
#         # Weekly Sales Chart
#         ax2 = fig.add_subplot(gs[0, 1])
#         weekly_sales = data.groupby('Week')['Sales'].sum()
#         ax2.bar(weekly_sales.index, weekly_sales.values, color='skyblue')
#         ax2.set_title('Weekly Sales Distribution')
#         ax2.set_xlabel('Week Number')
#         ax2.set_ylabel('Sales ($10^7)')
        
#         # Monthly Sales Chart
#         ax3 = fig.add_subplot(gs[1, 0])
#         monthly_sales = data.groupby('Month')['Sales'].sum()
#         months = ['Oct', 'Nov', 'Dec']
#         ax3.bar(months[:len(monthly_sales)], monthly_sales.values, color='lightgreen')
#         ax3.set_title('Monthly Sales Distribution')
#         ax3.set_xlabel('Month')
#         ax3.set_ylabel('Sales ($10^6)')
#         ax3.tick_params(axis='x', rotation=45)
        
#         # Quarterly Sales Chart
#         ax4 = fig.add_subplot(gs[1, 1])
#         quarterly_sales = data.groupby('Quarter')['Sales'].sum()
#         print(quarterly_sales)
#         print(quarterly_sales.index)
#         """ist comprehension that creates labels like 'Q1', 'Q2', 'Q3', 'Q4'"""
#         quarters = [f'Q{q}' for q in quarterly_sales.index]
#         ax4.pie(quarterly_sales.values, labels=quarters, autopct='%1.1f%%',
#                 colors=['orange', 'lightgreen', 'green', 'blue'])
#         ax4.set_title('Quarterly Sales Distribution')
        
#         # Add summary statistics
#         total_sales = data['Sales'].sum()
#         avg_daily_sales = daily_sales.mean()
        
#         fig.suptitle(f'Sales Dashboard\nTotal Sales: ${total_sales:,.2f}\n'
#                     f'Average Daily Sales: ${avg_daily_sales:,.2f}',
#                     fontsize=14, y=1.05)
#         plt.tight_layout()
#         plt.show()       


# def main():
#     obj1=My_Dashboard()
#     t1=obj1.create_sales_dashboard(data)
    
    
# #calling main function
# if __name__ == "__main__":
#      main()