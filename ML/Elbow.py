import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.datasets import make_blobs
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# # Generate a synthetic dataset
# X, y = make_blobs(n_samples=500, centers=4, random_state=42)

# # List to store silhouette scores for different K values
# sil_scores = []

# # Test K values from 2 to 10
# for k in range(2, 11):
#     kmeans = KMeans(n_clusters=k, random_state=42)
#     kmeans.fit(X)
    
#     # Calculate Silhouette Score
#     score = silhouette_score(X, kmeans.labels_)
#     sil_scores.append(score)

# # Plot the silhouette scores for different K values
# plt.plot(range(2, 11), sil_scores, marker='o')
# plt.title("Silhouette Scores for Different K")
# plt.xlabel("Number of Clusters (K)")
# plt.ylabel("Silhouette Score")
# plt.show()

# # Print the best K value (highest Silhouette Score)
# optimal_k = range(2, 11)[np.argmax(sil_scores)]
# print(f"The optimal number of clusters is: {optimal_k}")



# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.cluster.hierarchy import dendrogram, linkage
# from sklearn.datasets import make_blobs

# # Generate synthetic data
# X, y = make_blobs(n_samples=100, centers=3, random_state=42)

# # Perform hierarchical/agglomerative clustering
# Z = linkage(X, 'ward')

# # Create the dendrogram
# plt.figure(figsize=(10, 7))
# dendrogram(Z)
# plt.title("Dendrogram")
# plt.xlabel("Sample index")
# plt.ylabel("Distance")
# plt.show()

# from scipy.cluster.hierarchy import fcluster

# # Cut the dendrogram at a specified distance (threshold)
# max_distance = 10  # For example, this can be set based on your analysis of the dendrogram plot
# clusters = fcluster(Z, max_distance, criterion='distance')

# print(f"Cluster labels: {clusters}")















# np.random.seed(42)
# X1 = np.random.normal(50, 10, 100)  # Mean=50, Std=10
# X2 = np.random.normal(60, 15, 100)  # Mean=60, Std=15
# X3 = np.random.normal(40, 5, 100)   # Mean=40, Std=5

# # Create DataFrame
# df = pd.DataFrame({'X1': X1, 'X2': X2, 'X3': X3})

# # Compute covariance matrix
# cov_matrix = df.cov()

# # Plot covariance matrix
# plt.figure(figsize=(6,4))
# sns.heatmap(cov_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=1)
# plt.title("Covariance Matrix Heatmap")
# plt.show()


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Sample Data
np.random.seed(42)
X = np.random.rand(100, 3)  # 100 samples, 3 features

# 1️⃣ Standardize the data
# scaler = StandardScaler()
# X_scaled = scaler.fit_transform(X)

# 2️⃣ Apply PCA
# pca = PCA(n_components=2)  # Reduce to 2 principal components
# X_pca = pca.fit_transform(X_scaled)

# 3️⃣ Explained Variance Ratio (Choosing k)
# explained_variance = pca.explained_variance_ratio_

# Plot Scree Plot (Elbow Method)
# plt.plot(range(1, len(explained_variance) + 1), np.cumsum(explained_variance), marker='o')
# plt.xlabel('Number of Components')
# plt.ylabel('Cumulative Explained Variance')
# plt.title('PCA Scree Plot')
# plt.show()

# # 4️⃣ Transformed Data
# print("Original Shape:", X.shape)
# print("Reduced Shape:", X_pca.shape)
