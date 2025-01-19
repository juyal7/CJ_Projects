import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler

df=pd.read_csv("https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv")
# print(df.describe())
(df['Age'].median())
df["Age"] = df['Age'].fillna(df["Age"].mean())
df['Embarked'] = df['Embarked'].fillna(df['Embarked'].mode()[0])
df.dropna(subset=['Survived'], inplace=True)
df=df.drop(columns=['Cabin'])
# df=df.drop(columns=['Embarked'])
df=df.drop(columns=['Name'])
df=df.drop(columns=['Ticket'])
df=df.drop(columns=['PassengerId'])
# print(df.info())
label_encoder = LabelEncoder()
df['Sex'] = label_encoder.fit_transform(df['Sex'])
df['Embarked'] = label_encoder.fit_transform(df['Embarked'])
# print(df.head(5))



def clip_outlier(df,col):
    Q1=df[col].quantile(0.25)
    Q3=df[col].quantile(0.75)
    IQR=Q3-Q1
    lower_bound=Q1-1.5*IQR
    upper_bound=Q3+1.5*IQR
    df[col]=np.clip(df[col],lower_bound,upper_bound)
    return df
for col in ['Age','Fare']:
    clip_outlier(df,col)

# sns.boxplot(y = df["Age"])
# plt.show()
# sns.boxplot(y=df['Fare'])
# plt.show()

# print(df.info())

x=df.drop('Survived',axis=1)
y=df['Survived']

from sklearn.model_selection import train_test_split
X_train,X_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42)

# print(f"Training X data \n {X_train}")
# print(f"Training Y data {y_train}")
# print(f"Testing X data {X_test}")
# print(f"Testing Y data {y_test}")


scaler = StandardScaler()
scaler = StandardScaler()
numerical_features = ['Age', 'Fare', 'SibSp', 'Parch']
X_train[numerical_features] = scaler.fit_transform(X_train[numerical_features])
X_test[numerical_features] = scaler.transform(X_test[numerical_features])

# print(X_train.head())

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.model_selection import  GridSearchCV
lr=LogisticRegression()

# Defining the parameters for GridSearchCV
param_grid = {
    'penalty': ['l1', 'l2', 'elasticnet', None],
    'max_iter': [100, 500, 1000]
}

# Applying GridSearchCV for hyperparameter tuning
grid_search = GridSearchCV(estimator=lr, param_grid=param_grid, cv=5, scoring='accuracy', return_train_score=True)
grid_search.fit(X_train, y_train)

# Getting the best estimator
best_lr = grid_search.best_estimator_

# Making predictions
y_pred = best_lr.predict(X_test)
y_pred_proba = best_lr.predict_proba(X_test)[:, 1]

results_df = pd.DataFrame({
    'Actual Label': y_test,
    'Predicted Probability': y_pred_proba,
    'Predicted Label': y_pred
})

# Display the first 5 instances in the result dataframe
print(results_df.head())

# Calculating accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy * 100:.2f}%')


# sns.pairplot(df,x_vars=['Pclass','Age','SibSp','Parch'],y_vars='Survived',kind='reg')
# plt.show()