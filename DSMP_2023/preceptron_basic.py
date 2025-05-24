from sklearn.datasets import make_classification
import numpy as np
import matplotlib.pyplot as plt
X,y=make_classification(n_samples=100,n_features=2, n_informative=1,n_redundant=0,n_classes=2,n_clusters_per_class=1,random_state=41,hypercube=False,class_sep=10)

def preceptron(X,y):
    X=np.insert(X, 0, 1, axis=1)
    weights=np.ones(X.shape[1])
    lr=0.1
    for i in range(50000):
        j=np.random.randint(0,100)
        y_hat=step(np.dot(X[j], weights))
        weights=weights+lr*(y[j]-y_hat)*X[j]
    return weights[0],weights[1:]

def step(z):
    return 1 if z>0 else 0

intercept,coef_=preceptron(X, y)
m=-(coef_[0]/coef_[1])
b=-intercept/coef_[1]
x_input=np.linspace(-3, 3, 100)
y_input=m*x_input+b
plt.figure(figsize=(10, 6))
plt.scatter(X[:, 0], X[:, 1], c=y, cmap='winter', s=100)
plt.plot(x_input, y_input, color='red')
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.title('Scatter Plot of Two Features with Two Classes')
plt.show()          
