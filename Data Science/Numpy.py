import numpy as np

# arr=np.array([[1,2,3,4,5],[1,2,3,4,5]])
# arr=np.array([[[1,2,3],[4,5,6],[1,2,3]],[[8,9,0],[11,12,13],[0,0,0]],[[1,2,3],[4,5,6],[1,2,3]]])
# print(arr)
# print(arr.dtype)
# print(type(arr.itemsize))
# print(arr.ndim)
# print(arr.size)
# print(arr.shape)
# print(arr.reshape(1,12,1))
# print(arr.max())
# print(arr.min())
# print(arr.sum())
# print(arr.sum(axis=2))

# a=np.arange(0,20).reshape(2,5,2).ndim
# b=np.ones((3,4))
# print(b) 

a=np.random.uniform(1,100,20).reshape(2, 5, 2)
print(a)

       