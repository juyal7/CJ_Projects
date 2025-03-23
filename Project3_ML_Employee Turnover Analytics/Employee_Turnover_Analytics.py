import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report, roc_auc_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')

"""Data Collection"""

df=pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/ML/Project/1722506184_hr_comma_sep/HR_comma_sep.csv")


# Convert numeric columns to appropriate data types
numeric_cols = ['satisfaction_level', 'last_evaluation', 'number_project', 
                'average_montly_hours', 'time_spend_company', 'Work_accident', 
                'left', 'promotion_last_5years']
                
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col])


print(f"Total number of records: {df.shape[0]}")
print(f"Total number of features: {df.shape[1]}")
print(df.head())

# # Task 1: Data Quality Checks
print("\n--- TASK 1: DATA QUALITY CHECKS ---")
print("\nChecking for missing values:")
print(df.isnull().sum())

print("\nChecking data types:")
print(df.dtypes)

print("\nBasic statistics:")
print(df.describe())

# Task 2: EDA to understand factors contributing to employee turnover
print("\n--- TASK 2: EXPLORATORY DATA ANALYSIS ---")

# Encode categorical variables
le_salary = LabelEncoder()
df['salary_encoded'] = le_salary.fit_transform(df['salary'])
le_sales = LabelEncoder()
df['sales_encoded'] = le_sales.fit_transform(df['sales'])
# print(df.head())

# # Distribution of employees who left vs stayed
# print("\nEmployee turnover distribution:")
# print(df['left'].value_counts())
# print(f"Turnover rate: {df['left'].mean() * 100:.2f}%")

# #create the correlation matrix
# correlation_matrix = df.drop(['sales', 'salary'], axis=1).corr()

# # Create the heatmap
# plt.figure(figsize=(10, 8))
# sns.heatmap(correlation_matrix,
#             annot=True,          # Show correlation values
#             cmap='coolwarm',     # Color scheme (red for positive, blue for negative)
#             center=0,            # Center the colormap at 0
#             fmt='.2f',           # Show 2 decimal places
#             square=True,         # Make the plot square-shaped
#             linewidths=0.5,      # Add grid lines
#             cbar_kws={'label': 'Correlation Coefficient'}  # Add colorbar label
# )

# # Add title and adjust layout
# plt.title('Correlation Matrix Heatmap', pad=20)
# plt.tight_layout()

# # Rotate x-axis labels for better readability
# plt.xticks(rotation=45, ha='right')
# plt.yticks(rotation=0)

# plt.show()

# # Create visualizations
# plt.figure(figsize=(15, 10))

# # Satisfaction level vs turnover
# plt.subplot(2, 3, 1)
# sns.boxplot(x='left', y='satisfaction_level', data=df)
# plt.title('Satisfaction Level vs Turnover')

# # Last evaluation vs turnover
# plt.subplot(2, 3, 2)
# sns.boxplot(x='left', y='last_evaluation', data=df)
# plt.title('Last Evaluation vs Turnover')

# # Number of projects vs turnover
# plt.subplot(2, 3, 3)
# sns.countplot(x='number_project', hue='left', data=df)
# plt.title('Number of Projects vs Turnover')

# # Monthly hours vs turnover
# plt.subplot(2, 3, 4)
# sns.boxplot(x='left', y='average_montly_hours', data=df)
# plt.title('Monthly Hours vs Turnover')

# # Time spent in company vs turnover
# plt.subplot(2, 3, 5)
# sns.countplot(x='time_spend_company', hue='left', data=df)
# plt.title('Time in Company vs Turnover')

# # Salary vs turnover
# plt.subplot(2, 3, 6)
# sns.countplot(x='salary', hue='left', data=df)
# plt.title('Salary vs Turnover')

# plt.tight_layout()
# plt.savefig('turnover_analysis.png')
# plt.show()

# Task 3: Clustering of employees who left based on satisfaction and evaluation
print("\n--- TASK 3: CLUSTERING ANALYSIS ---")

# Filter employees who left
left_employees = df[df['left'] == 1]
print(f"\nNumber of employees who left: {left_employees.shape[0]}")

# Perform K-Means clustering
X_cluster = left_employees[['satisfaction_level', 'last_evaluation']].values

# Determine optimal number of clusters using the Elbow method
inertia = []
k_range = range(1, min(6, len(X_cluster) + 1))
for k in k_range:
    if len(X_cluster) >= k:  # Make sure we have enough samples for k clusters
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X_cluster)
        inertia.append(kmeans.inertia_)

if len(inertia) > 1:  # Make sure we calculated inertia for at least 2 values of k
    plt.figure(figsize=(8, 4))
    plt.plot(k_range[:len(inertia)], inertia, 'bo-')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Inertia')
    plt.title('Elbow Method for Optimal k')
    plt.savefig('elbow_method.png')
    plt.show()
    # Based on the elbow method (or use a default of 3 clusters if data is limited)
    optimal_k = 3 if len(inertia) >= 3 else len(inertia)
    
    # Apply K-Means with optimal k
    kmeans = KMeans(n_clusters=optimal_k, random_state=42)
    left_employees['cluster'] = kmeans.fit_predict(X_cluster)
    
    # Analyze clusters
    print(f"\nCluster analysis of employees who left (k={optimal_k}):")
    cluster_analysis = left_employees.groupby('cluster').agg({
        'satisfaction_level': 'mean',
        'last_evaluation': 'mean',
        'number_project': 'mean',
        'average_montly_hours': 'mean',
        'time_spend_company': 'mean'
    }).round(2)
    print(cluster_analysis)
    
    # Visualize clusters
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='satisfaction_level', y='last_evaluation', 
                    hue='cluster', data=left_employees, palette='viridis', s=100)
    plt.show()
    # Add centroids
    centroids = kmeans.cluster_centers_
    plt.scatter(centroids[:, 0], centroids[:, 1], marker='X', s=200, 
                linewidth=2, color='red', label='Centroids')
    
    plt.title('Clusters of Employees Who Left')
    plt.xlabel('Satisfaction Level')
    plt.ylabel('Last Evaluation')
    plt.legend()
    plt.savefig('employee_clusters.png')
    plt.show()
else:
    print("Not enough data for meaningful clustering")

# Prepare data for modeling
# Task 4: Handle class imbalance using SMOTE
print("\n--- TASK 4: HANDLING CLASS IMBALANCE WITH SMOTE ---")

# Prepare features and target
X = df.drop(['left', 'sales', 'salary'], axis=1)
y = df['left']

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

print(f"Before SMOTE - Class distribution in training set: {pd.Series(y_train).value_counts()}")

# Apply SMOTE to handle class imbalance
if len(X_train) > 5:  # Ensure we have enough samples for SMOTE
    try:
        smote = SMOTE(random_state=42)
        X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
        print(f"After SMOTE - Class distribution in training set: {pd.Series(y_train_smote).value_counts()}")
    except ValueError as e:
        print(f"SMOTE could not be applied due to: {e}")
        X_train_smote, y_train_smote = X_train, y_train
else:
    print("Not enough samples for SMOTE. Using original training set.")
    X_train_smote, y_train_smote = X_train, y_train

# Task 5: K-fold cross-validation and model training
print("\n--- TASK 5: MODEL TRAINING AND EVALUATION ---")

# Define models to evaluate
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(random_state=42)
}

# Prepare for k-fold cross-validation
kf = KFold(n_splits=5, shuffle=True, random_state=42)

# Train and evaluate models
results = {}
for name, model in models.items():
    print(f"\nTraining {name}...")
    
    # K-fold cross-validation
    cv_scores = cross_val_score(model, X_train_smote, y_train_smote, cv=kf, scoring='f1')
    print(f"Cross-validation F1 scores: {cv_scores}")
    print(f"Mean F1 score: {cv_scores.mean():.4f}")
    
    # Train on full training set and evaluate on test set
    model.fit(X_train_smote, y_train_smote)
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    try:
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_pred_proba)
    except (AttributeError, ValueError):
        auc = float('nan')
    
    # Store results
    results[name] = {
        'cv_f1': cv_scores.mean(),
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'auc': auc
    }
    
    # Print detailed evaluation
    print(f"\nTest set evaluation for {name}:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    if not np.isnan(auc):
        print(f"AUC-ROC: {auc:.4f}")
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # Feature importance (for tree-based models)
    if hasattr(model, 'feature_importances_'):
        importances = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nFeature Importance:")
        print(importances)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='importance', y='feature', data=importances)
        plt.title(f'Feature Importance - {name}')
        plt.tight_layout()
        plt.savefig(f'feature_importance_{name.replace(" ", "_").lower()}.png')

# Task 6: Identify the best model
print("\n--- TASK 6: BEST MODEL SELECTION ---")

# Convert results to DataFrame for easy comparison
results_df = pd.DataFrame.from_dict(results, orient='index')
print("\nModel Comparison:")
print(results_df)

# Determine best model based on F1 score
best_model_name = results_df['f1'].idxmax()
print(f"\nBest model based on F1 score: {best_model_name}")
print("Justification: F1 score provides a balance between precision and recall, which is important for employee turnover prediction where we want to minimize both false positives and false negatives.")

# Task 7: Retention strategies based on analysis
print("\n--- TASK 7: RETENTION STRATEGIES ---")

# Extract feature importance from the best model
if best_model_name == 'Random Forest' or best_model_name == 'Gradient Boosting':
    best_model = models[best_model_name]
    importances = pd.DataFrame({
        'feature': X_train.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    top_factors = importances['feature'].tolist()[:3]  # Top 3 factors
else:
    # If best model is not tree-based, use correlation analysis
    corr_abs = corr_with_target.abs().sort_values(ascending=False)
    top_factors = corr_abs.index.tolist()[1:4]  # Exclude 'left' itself

print(f"\nTop factors influencing employee turnover: {', '.join(top_factors)}")

# Analyze clusters if clustering was performed
cluster_strategies = {}
if 'cluster' in left_employees.columns:
    for cluster_id in left_employees['cluster'].unique():
        cluster_data = left_employees[left_employees['cluster'] == cluster_id]
        avg_satisfaction = cluster_data['satisfaction_level'].mean()
        avg_evaluation = cluster_data['last_evaluation'].mean()
        avg_projects = cluster_data['number_project'].mean()
        avg_hours = cluster_data['average_montly_hours'].mean()
        avg_tenure = cluster_data['time_spend_company'].mean()
        
        print(f"\nCluster {cluster_id} Profile:")
        print(f"- Average satisfaction: {avg_satisfaction:.2f}")
        print(f"- Average evaluation: {avg_evaluation:.2f}")
        print(f"- Average number of projects: {avg_projects:.2f}")
        print(f"- Average monthly hours: {avg_hours:.2f}")
        print(f"- Average years at company: {avg_tenure:.2f}")
        
        # Determine targeted retention strategies based on cluster profile
        strategies = []
        
        if avg_satisfaction < 0.4:
            strategies.append("Implement regular satisfaction surveys and feedback sessions")
            strategies.append("Develop personalized career growth plans")
        
        if avg_evaluation > 0.8 and avg_hours > 200:
            strategies.append("Recognize high performers with rewards and advancement opportunities")
            strategies.append("Implement work-life balance initiatives to prevent burnout")
        
        if avg_projects > 5:
            strategies.append("Review workload distribution and project assignments")
            strategies.append("Provide additional support for employees managing multiple projects")
        
        if avg_tenure > 4:
            strategies.append("Create tenure-based rewards and recognition programs")
            strategies.append("Develop new challenges for long-term employees")
        
        cluster_strategies[cluster_id] = strategies
        
        print("Recommended retention strategies:")
        for i, strategy in enumerate(strategies, 1):
            print(f"{i}. {strategy}")

print("\n--- COMPREHENSIVE RETENTION STRATEGY RECOMMENDATIONS ---")
print("""
Based on our analysis, we recommend the following retention strategies:

1. Satisfaction-Based Strategies:
   - Implement regular satisfaction surveys to catch issues early
   - Create personalized development plans for low-satisfaction employees
   - Establish mentorship programs to increase engagement

2. Workload Management:
   - Review project allocation to prevent overloading high performers
   - Implement clear policies about working hours to prevent burnout
   - Provide adequate resources and support for complex projects

3. Compensation and Recognition:
   - Ensure competitive compensation, especially for high performers
   - Develop non-monetary recognition programs to acknowledge contributions
   - Create clear promotion pathways and communicate them effectively

4. Work Environment Improvements:
   - Foster a positive team culture and improve managerial relationships
   - Offer flexible work arrangements where possible
   - Create opportunities for social connection and team building

5. Strategic Initiative Implementation:
   - Segment employees based on risk factors and develop targeted interventions
   - Establish an early warning system using the predictive model
   - Conduct stay interviews with valued employees before they consider leaving
""")

print("\n--- CONCLUSION ---")
print("""
This analysis provides Portobello Tech's HR department with data-driven insights on employee turnover patterns. By implementing the recommended targeted retention strategies and continuously monitoring the identified key factors, the company can reduce turnover rates and retain valuable talent.

The predictive model developed can be used to identify employees at risk of leaving, allowing proactive intervention. Regular model updates using new data will ensure continued accuracy and relevance as the company evolves.
""")