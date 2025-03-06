import numpy as np 
import pandas as pd 
df = pd.read_csv('C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/unsupervised/mnist.csv')
import matplotlib.pyplot as plt
plt.imshow(df.iloc[577,1:].values.reshape(28,28))

X = df.iloc[:,1:]
y = df.iloc[:,0]

from sklearn.model_selection import train_test_split
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42)

print(X_train.shape)

from sklearn.neighbors import KNeighborsClassifier

knn = KNeighborsClassifier()
knn.fit(X_train,y_train)

# import time
# start = time.time()
y_pred = knn.predict(X_test)
# print(time.time() - start)

from sklearn.metrics import accuracy_score
print(accuracy_score(y_test,y_pred))

######PCA#######

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# PCA 
from sklearn.decomposition import PCA
pca = PCA(n_components=None)

X_train_1 = pca.fit_transform(X_train)
X_test_1 = pca.transform(X_test)
X_train_1.shape
knn = KNeighborsClassifier()
knn.fit(X_train_1,y_train)
y_pred = knn.predict(X_test_1)
accuracy_score(y_test,y_pred)

"""PCA with reduced components"""

# PCA 
from sklearn.decomposition import PCA
pca = PCA(n_components=200)
X_train_200 = pca.fit_transform(X_train)
X_test_200 = pca.transform(X_test)
X_train_200.shape
knn = KNeighborsClassifier()
knn.fit(X_train_200,y_train)
y_pred_200 = knn.predict(X_test_200)
print(accuracy_score(y_test,y_pred_200))

# for i in range(1,785):
#     pca = PCA(n_components=i)
#     X_train_trf = pca.fit_transform(X_train)
#     X_test_trf = pca.transform(X_test)
    
#     knn = KNeighborsClassifier()
    
#     knn.fit(X_train_trf,y_train)
    
#     y_pred = knn.predict(X_test_trf)
    
#     print(accuracy_score(y_test,y_pred))

pca = PCA(n_components=2)
X_train_trf = pca.fit_transform(X_train)
X_test_trf = pca.transform(X_test)

X_train_trf.shape
knn = KNeighborsClassifier()
knn.fit(X_train_trf,y_train)
y_pred_trf = knn.predict(X_test_trf)
# print(accuracy_score(y_test,y_pred_trf))
# print(pca.components_.shape)
# print(pca.explained_variance_)
# print(pca.explained_variance_ratio_)
# print(np.cumsum(pca.explained_variance_ratio_))



pca = PCA().fit(X_train)

# Calculate cumulative explained variance
explained_variance = np.cumsum(pca.explained_variance_ratio_)

# Initialize list to store accuracy results
# accuracies = []
# times = []
# import time

# for i in range(1, len(explained_variance) + 1):
#     start_time = time.time()
#     # Perform PCA with i components
#     pca = PCA(n_components=i)
#     X_train_trf = pca.fit_transform(X_train)
#     X_test_trf = pca.transform(X_test)
    
#     # Train the KNN model
#     knn = KNeighborsClassifier()
#     knn.fit(X_train_trf, y_train)
    
#     # Predict and calculate accuracy
#     y_pred = knn.predict(X_test_trf)
#     accuracy = accuracy_score(y_test, y_pred)
#     accuracies.append(accuracy)
    
#     end_time = time.time()
#     time_taken = end_time - start_time
#     times.append(time_taken)
#     print(f"PCA Components: {i}, Variance Explained: {explained_variance[i-1]:.4f}, Accuracy: {accuracy:.4f}, Time Taken: {time_taken:.4f} seconds")



""""LDA"""

from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import time

accuracies = []
times = []

# Assuming that the number of components in LDA is constrained by the number of classes (n_classes - 1)
n_classes = len(set(y_train))

for i in range(1, min(n_classes, len(X_train))):  # LDA components can't exceed (n_classes - 1)
    start_time = time.time()
    
    # Perform LDA with i components (i is constrained by the number of classes)
    lda = LDA(n_components=i)
    X_train_lda = lda.fit_transform(X_train, y_train)
    X_test_lda = lda.transform(X_test)
    
    # Train the KNN model
    knn = KNeighborsClassifier()
    knn.fit(X_train_lda, y_train)
    
    # Predict and calculate accuracy
    y_pred = knn.predict(X_test_lda)
    accuracy = accuracy_score(y_test, y_pred)
    accuracies.append(accuracy)
    
    end_time = time.time()
    time_taken = end_time - start_time
    times.append(time_taken)
    
    print(f"LDA Components: {i}, Accuracy: {accuracy:.4f}, Time Taken: {time_taken:.4f} seconds")
