import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler, Normalizer

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
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.model_selection import  GridSearchCV
lr=GaussianNB()

# Import Required Libraries and apply Naive Bayes algorithm
from sklearn.naive_bayes import GaussianNB
# Define the pipeline
pipeline = Pipeline([
    (  'normqlizer',Normalizer()),  
        ('scaler', StandardScaler()),
    ('nb', GaussianNB())
])

# Fit the pipeline on the training data
pipeline.fit(X_train, y_train)


#Predict on the training and testing set
y_pred_train_nb = pipeline.predict(X_train)
y_pred_test_nb = pipeline.predict(X_test)

# Calculate the training and testing accuracy
training_accuracy = accuracy_score(y_train, y_pred_train_nb)
testing_accuracy = accuracy_score(y_test, y_pred_test_nb)
print("\nNaïve Bayes:")
print(f"Training Accuracy: {training_accuracy}")
print(f"Testing Accuracy: {testing_accuracy}")

y_pred_prob_nb = pipeline.predict_proba(X_test)[:, 1]




