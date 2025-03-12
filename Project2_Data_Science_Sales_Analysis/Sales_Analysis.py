import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

data = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Project2/AusApparalSales4thQrt2020.csv")
# print(data.tail(10))

#This class handles data cleaning and preparation.
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

#This Class gives statistical_analysis
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

#This Class Gives data visualization        
class data_visualization():
    """State-wise sales analysis for different demographic groups (kids, women, men, and seniors)"""
    
    def state_wise_sales(self, data):
        # Store data as instance variable
        self.data=data
        # data.groupby('State')['Sales'].sum().sort_values(ascending=False).head(10)
            # Create subplots for the dashboard
        """Total Size of the deshboard"""
        fig = plt.figure(figsize=(10, 9))
        
        # creates a 2×2 grid layout
        gs = fig.add_gridspec(2, 2, hspace=0.5, wspace=0.5)
        ax1 = fig.add_subplot(gs[0, 0])
        
        # Group data and calculate sales
        daily_sales = data.groupby('State')['Sales'].sum()
        
          # Sort values for better visualization
        daily_sales = daily_sales.sort_values(ascending=False)
        
        ax1.bar(daily_sales.index, daily_sales.values, linewidth=10)    
        ax1.set_title('State wise Sales Trend')
        ax1.set_xlabel('states',labelpad=1)
        ax1.set_ylabel('Sales (*$10^6)')
        ax1.tick_params(axis='x', rotation=45, labelsize=5)
        plt.tight_layout()
        plt.show()

    """Sales analysis for different product groups (men, women, and kids)"""
    def product_wise_sales(self, data):
        # Store data as instance variable
        self.data = data
        
        # Create figure with specified size
        fig, ax = plt.subplots(figsize=(10, 9))
        
        # Group data and calculate sales
        daily_sales = data.groupby('Group', observed=True)['Sales'].sum()
        
        # Sort values for better visualization
        daily_sales = daily_sales.sort_values(ascending=False)

        # Create group labels
        groups = [f'{group}\n(${sales:,.2f})' for group, sales in daily_sales.items()]
       
        # Define a better color palette
        colors = sns.color_palette('husl', n_colors=len(daily_sales))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            daily_sales.values,
            labels=groups,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            shadow=True,
            explode=[0.05] * len(daily_sales)  # Slight separation between slices
        )
        
        # Enhance text appearance
        plt.setp(autotexts, size=9, weight='bold')
        plt.setp(texts, size=8)
        
        # Add title
        plt.title('Sales Distribution by Product Group', 
                 pad=20, 
                 size=14, 
                 weight='bold')
        
        # Add legend
        plt.legend(
            wedges, 
            groups,
            title="Product Groups",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )        
        # Ensure layout fits well
        plt.tight_layout()
        
        # Show plot
        plt.show()
  
    def unit_wise(self,data):
        # Store data as instance variable
        self.data = data
        
        # Create figure with specified size
        fig, ax = plt.subplots(figsize=(10, 9))
        
        # Group data and calculate sales
        Unit= data.groupby('Group', observed=True)['Unit'].sum()
        
        # Sort values for better visualization
        Unit = Unit.sort_values(ascending=False)

        # Create group labels
        groups = [f'{group}\n({unit} units)' for group, unit in Unit.items()]
        
        for i , j in Unit.items():
            print(i, j)
       
        # Define a better color palette
        colors = sns.color_palette('husl', n_colors=len(Unit))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            Unit.values,
            labels=groups,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
        )
        
        # Enhance text appearance
        plt.setp(autotexts, size=9, weight='bold')
        plt.setp(texts, size=8)
        
        # Add title
        plt.title('Sales Distribution by Product Group', 
                 pad=20, 
                 size=14, 
                 weight='bold')
        
        # Add legend
        plt.legend(
            wedges, 
            groups,
            title="Product Groups",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )        
        # Ensure layout fits well
        plt.tight_layout()
        
        # Show plot
        plt.show()
  
    """visualization"""    
    def visualization(self, data):
            data = data.pivot_table(
                    values='Sales',
                    index='State',
                    columns='Group',
                    aggfunc='sum'
                                )
            data.plot(kind='bar', stacked=True)
            plt.title('Sales by State and Group')
            plt.xlabel('State')
            plt.ylabel('Sales')
            plt.legend(title='Group')
            plt.show()       
    
    """Time-of-the-day analysis: Identify peak and off-peak 
    sales periods to facilitate strategic planning for S&M teams"""
    def visualize_Time_of_the_day(self,data):
        self.data=data
        top_periods = (data.groupby('Time', observed=True)['Sales']
                      .agg('sum')                                
                      .nlargest(10))
        print(top_periods)
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        bars = ax.bar(range(len(top_periods)), top_periods.values)
        plt.tight_layout()
        plt.show()

#This class create a Dashboard
class My_Dashboard():
    def create_sales_dashboard(self, data):
        """
        Create a comprehensive sales dashboard with daily, weekly, monthly, and quarterly views.
        
        Args:
            data (pd.DataFrame): Input DataFrame containing Date and Sales columns
        """
        # Ensure Date column is datetime
        data['Date'] = pd.to_datetime(data['Date'])
        
        # Create date-based features
        data['Week'] = data['Date'].dt.isocalendar().week
        data['Month'] = data['Date'].dt.month
        data['Quarter'] = data['Date'].dt.quarter
        
        # Create subplots for the dashboard
        """Total Size of the deshboard"""
        fig = plt.figure(figsize=(10, 9))
        """creates a 2×2 grid layout"""
        gs = fig.add_gridspec(2, 2, hspace=0.5, wspace=0.5)
        
        # Daily Sales Chart
        ax1 = fig.add_subplot(gs[0, 0])
        daily_sales = data.groupby('Date')['Sales'].sum()
        ax1.bar(daily_sales.index, daily_sales.values, linewidth=10)    
        ax1.set_title('Daily Sales Trend')
        ax1.set_xlabel('Date',labelpad=1)
        ax1.set_ylabel('Sales (*$10^6)')
        ax1.tick_params(axis='x', rotation=45, labelsize=5)
        
        # Weekly Sales Chart
        ax2 = fig.add_subplot(gs[0, 1])
        weekly_sales = data.groupby('Week')['Sales'].sum()
        ax2.bar(weekly_sales.index, weekly_sales.values, color='skyblue')
        ax2.set_title('Weekly Sales Distribution')
        ax2.set_xlabel('Week Number')
        ax2.set_ylabel('Sales ($10^7)')
        
        # Monthly Sales Chart
        ax3 = fig.add_subplot(gs[1, 0])
        monthly_sales = data.groupby('Month')['Sales'].sum()
        months = ['Oct', 'Nov', 'Dec']
        ax3.bar(months[:len(monthly_sales)], monthly_sales.values, color='lightgreen')
        ax3.set_title('Monthly Sales Distribution')
        ax3.set_xlabel('Month')
        ax3.set_ylabel('Sales ($10^6)')
        ax3.tick_params(axis='x', rotation=45)
        
        # Quarterly Sales Chart
        ax4 = fig.add_subplot(gs[1, 1])
        quarterly_sales = data.groupby('Quarter')['Sales'].sum()
        print(quarterly_sales)
        print(quarterly_sales.index)
        """ist comprehension that creates labels like 'Q1', 'Q2', 'Q3', 'Q4'"""
        quarters = [f'Q{q}' for q in quarterly_sales.index]
        ax4.pie(quarterly_sales.values, labels=quarters, autopct='%1.1f%%',
                colors=['orange', 'lightgreen', 'green', 'blue'])
        ax4.set_title('Quarterly Sales Distribution')
        
        # Add summary statistics
        total_sales = data['Sales'].sum()
        avg_daily_sales = daily_sales.mean()
        
        fig.suptitle(f'Sales Dashboard\nTotal Sales: ${total_sales:,.2f}\n'
                    f'Average Daily Sales: ${avg_daily_sales:,.2f}',
                    fontsize=14, y=1.05)
        # plt.tight_layout()
        plt.show()       

#This Class will give Outliers 
class Outliers():
    def analyze_outliers(self,data):
        self.data = data
        """
        Create comprehensive box plot analysis for sales outliers
        """
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Box plot by Group
        sns.boxplot(x='Group', y='Sales', data=self.data, ax=ax1)
        ax1.set_title('Sales Distribution by Product Group', fontsize=8, pad=10)
        ax1.set_xlabel('Product Group', fontsize=10,loc='left')
        ax1.set_ylabel('Sales ($)', fontsize=5)
        ax1.tick_params(axis='x', rotation=0)
        
        # Add outlier statistics for each group
        outlier_stats = self.get_outlier_stats()
        ax1.text(1.02, 0.6, outlier_stats, transform=ax1.transAxes,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'),
                fontsize=9,
                verticalalignment='center')
        
        # Monthly box plot
        self.data['Month'] = pd.to_datetime(self.data['Date']).dt.strftime('%B')
        sns.boxplot(x='Month', y='Sales', data=self.data, ax=ax2) 
        ax2.set_title('Sales Distribution by Month', fontsize=8, pad=10)
        ax2.set_xlabel('Month', fontsize=5)
        ax2.set_ylabel('Sales ($)', fontsize=5)
        ax2.tick_params(axis='x')
        
        # Add grid for better readability
        ax1.grid(True, alpha=1)
        ax2.grid(True, alpha=1)
        
        plt.tight_layout()
        plt.show()
        
        # Print detailed outlier analysis
        self.print_outlier_analysis()
    
    def get_outlier_stats(self):
        """Calculate outlier statistics for each group"""
        stats = []
        for group in self.data['Group'].unique():
            group_data = self.data[self.data['Group'] == group]['Sales']
            # print(group_data)
            Q1 = group_data.quantile(0.25)
            Q3 = group_data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = group_data[(group_data < (Q1 - 1.5 * IQR)) | 
                                (group_data > (Q3 + 1.5 * IQR))]
            stats.append(f"{group}:\n"
                        f"Outliers: {len(outliers)}\n"
                        f"Min: ${group_data.min():,.2f}\n"
                        f"Max: ${group_data.max():,.2f}\n")
        return "\n".join(stats)
    
    def print_outlier_analysis(self):
        """Print detailed analysis of outliers"""
        print("\nDetailed Outlier Analysis")
        print("-" * 50)
        
        # Overall statistics
        print("\nOverall Sales Statistics:")
        print(f"Mean Sales: ${self.data['Sales'].mean():,.2f}")
        print(f"Median Sales: ${self.data['Sales'].median():,.2f}")
        print(f"Std Dev: ${self.data['Sales'].std():,.2f}")
        
        # Group-wise analysis
        print("\nGroup-wise Outlier Analysis:")
        for group in self.data['Group'].unique():
            group_data = self.data[self.data['Group'] == group]['Sales']
            Q1 = group_data.quantile(0.25)
            Q3 = group_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = group_data[(group_data < lower_bound) | 
                                (group_data > upper_bound)]
            
            print(f"\n{group}:")
            print(f"Number of outliers: {len(outliers)}")
            print(f"Outlier percentage: {(len(outliers)/len(group_data))*100:.2f}%")
            print(f"Normal range: ${lower_bound:,.2f} to ${upper_bound:,.2f}")
            if len(outliers) > 0:
                print(f"Outlier range: ${outliers.min():,.2f} to ${outliers.max():,.2f}")    
    
def main():
    def analyze_sales_data():
        try:
            # Create instances of the analysis classes
            data_analysis_obj = data_analysis()
            data_viz_obj = data_visualization()
            dash_Board_obj=My_Dashboard()
            outlier_obj=Outliers()
            
            
            # Function to display menu and get user choice
            def display_menu():
                print("\n=== Sales Analysis Dashboard ===")
                print("1. View Statistical Analysis")
                print("2. View Sales by Group")
                print("3. View State-wise Sales")
                print("4. View Time of Day Analysis")
                print("5. View Unit-wise Analysis")
                print("6. View All Reports")
                print("7. View analysis_report")
                print("8. View analysis_report")
                print("0. Exit")
                return input("\nEnter your choice (0-8): ")

            while True:
                choice = display_menu()
                
                if choice == '1':
                    print("\n=== Statistical Analysis ===")
                    print("\nSales Statistics:")
                    print(data_analysis_obj.statistical_analysis_sales(data))
                    print("\nUnit Statistics:")
                    print(data_analysis_obj.statistical_analysis_unit(data))
                    
                    print("\nHighest Sales Group:")
                    print(data_analysis_obj.highest_sales(data))
                    print("\nLowest Sales Group:")
                    print(data_analysis_obj.lowest_sales(data))

                elif choice == '2':
                    print("\n=== Sales by Product Group ===")
                    data_viz_obj.product_wise_sales(data)

                elif choice == '3':
                    print("\n=== State-wise Sales Analysis ===")
                    data_viz_obj.state_wise_sales(data)

                elif choice == '4':
                    print("\n=== Time of Day Analysis ===")
                    data_viz_obj.visualize_Time_of_the_day(data)

                elif choice == '5':
                    print("\n=== Unit-wise Analysis ===")
                    data_viz_obj.unit_wise(data)

                elif choice == '6':
                    print("\n=== Generating All Reports ===")
                    print("\nWeekly Report:")
                    print(data_analysis_obj.weekly__report(data))
                    print("\nMonthly Report:")
                    print(data_analysis_obj.Monthly_report(data))
                    print("\nQuarterly Report:")
                    print(data_analysis_obj.quarterly_report(data))
                    
                    # Generate all visualizations
                    data_viz_obj.state_wise_sales(data)
                    data_viz_obj.product_wise_sales(data)
                    data_viz_obj.unit_wise(data)
                    data_viz_obj.visualization(data)
                    data_viz_obj.visualize_Time_of_the_day(data)
                
                elif choice == '7':
                    print("\n=== Dashboard ===")
                    dash_Board_obj.create_sales_dashboard(data)
                
                elif choice == '8':
                    print("\n=== Dashboard ===")
                    outlier_obj.analyze_outliers(data)
                
                elif choice == '0':
                    print("\nExiting the program!!!!")
                    break

                else:
                    print("\nInvalid choice! Please try again.")

                input("\nPress Enter to continue...")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
    
    #calling Function
    analyze_sales_data()

# Call the function to start the analysis
if __name__ == "__main__":
    main()