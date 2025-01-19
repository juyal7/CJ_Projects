import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler

df=pd.read_csv("https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv")

x=df.drop('Survived',axis=1)
y=df['Survived']
from sklearn.model_selection import train_test_split
X_train,X_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42)

X_train=X_train.drop(columns=['Name'])
X_train=X_train.drop(columns=['Ticket'])
X_train=X_train.drop(columns=['PassengerId'])
X_train=X_train.drop(columns=['Cabin'])

# print(y_train.info())
# print(y_test.info())

print(X_train.head())
X_test=X_test.drop(columns=['Name'])
X_test=X_test.drop(columns=['Ticket'])
X_test=X_test.drop(columns=['PassengerId'])
X_test=X_test.drop(columns=['Cabin'])

print(X_test.head())
print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
(X_train['Age'].median())
X_train["Age"] = X_train['Age'].fillna(X_train["Age"].mean())
X_train['Embarked'] = X_train['Embarked'].fillna(df['Embarked'].mode()[0])

label_encoder=LabelEncoder()
X_train['Sex'] = label_encoder.fit_transform(X_train['Sex'])
X_train['Embarked'] = label_encoder.fit_transform(X_train['Embarked'])

(X_test['Age'].median())
X_test["Age"] = X_test['Age'].fillna(X_test["Age"].mean())
X_test['Embarked'] = X_test['Embarked'].fillna(df['Embarked'].mode()[0])

label_encoder=LabelEncoder()
X_test['Sex'] = label_encoder.fit_transform(X_test['Sex'])
X_test['Embarked'] = label_encoder.fit_transform(X_test['Embarked'])

def clip_outlier(df,col):
    Q1=df[col].quantile(0.25)
    Q3=df[col].quantile(0.75)
    IQR=Q3-Q1
    lower_bound=Q1-1.5*IQR
    upper_bound=Q3+1.5*IQR
    df[col]=np.clip(df[col],lower_bound,upper_bound)
    return df
for col in ['Age','Fare']:
    clip_outlier(X_train,col)
    
for col in ['Age','Fare']:
    clip_outlier(X_test,col)
    


from sklearn.model_selection import train_test_split
# X_train,X_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42)

print(X_train.head())
print("============================================================================")   
# print(X_train.info())
# print(X_test.info())

scaler = StandardScaler()
scaler = StandardScaler()
numerical_features = ['Age', 'Fare', 'SibSp', 'Parch']
X_train[numerical_features] = scaler.fit_transform(X_train[numerical_features])
X_test[numerical_features] = scaler.fit_transform(X_test[numerical_features])

print(X_train.head())

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


