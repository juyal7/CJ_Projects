import numpy as np
import time

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

# a=np.random.uniform(1,100,20).reshape(2, 5, 2)
# print(a)

# a=np.arange(1,19).reshape(2,3,3)
# print(a)

# print(a[1,0::2,0::2])
       
# for i in np.nditer(a):
#     print(i)

"""Reduce time by Numpy"""

# a=[i for i in range(10000000)]
# b=[i for i in range(10000000,20000000)]
# c=[]
# import time
# start=time.time()
# for i in range(len(a)):
#     c.append(a[i]+b[i])
# print(time.time()-start)


# a=np.arange(10000000)
# b=np.arange(10000000, 20000000)
# start=time.time()
# c=a+b
# print(time.time()-start)

""" Memory """


# list1=[i for i in range(10000000)]
# import sys
# print(sys.getsizeof(list1))

# ar=np.arange(10000000,dtype=np.int32)
# print(sys.getsizeof(ar))
# print(ar.size*ar.itemsize)


"""Advance indexing"""

# a=np.arange(1, 17).reshape(4,4)
# print(a[1,0])
# print(a[[1,1]])
# print(a)


"""Boolean indexing"""
# a=np.random.randint(1, 100, 20).reshape(4, 5)
# print(a)
# b=a%2==0 #filter
# c= a[b]
# c.sort
# print(c)
# # for i in c:
# #     print(i)

"""Broadcasting"""

# a=np.arange(6).reshape(2, 3)
# # b=np.arange(4).reshape(4)
# b=np.arange(3).reshape(3)
# print(a+b)

""""sigmoid function"""
# def sigmoid(array):
#     return 1/(1+np.exp(-array))
# a=np.array([1, 2, 3, 4, 5])

# # sigmoid(a)
# print(sigmoid(a))


"""Mean Squared error"""

# acutul_result=np.random.randint(1, 10, 5)
# predicted_result=np.random.randint(1, 10, 5)
# print(np.square(acutul_result))
# def mse(a,b):
#      print(np.mean(np.square(acutul_result-predicted_result)))

# mse(acutul_result, predicted_result)


"""Binary cross """
# def binary_cross_entropy(a, b):
#     return np.mean(-a*np.log(b)-(1-a)*np.log(1-b))

# binary_cross_entropy(acutul_result, predicted_result)


"""Working with missing values"""

# a=np.array([1, 2, 3, 4, 5, np.nan, 6, 7, 8, 9, 10])
# print(a[~np.isnan(a)])


"""Ploting graph"""
# x=np.linspace(0, 10, 100)
# y=x*np.log(x)
# import matplotlib.pyplot as plt
# plt.plot(x, y)
# plt.show()


################Tricks in numpy#######################################
"""Concatenate"""
# a=np.arange(1, 10).reshape(3, 3)
# b=np.arange(21, 30).reshape(3, 3)
# print(a)
# print(b)
# c=np.concatenate((a, b),axis=1)
# print(c)

"""vstack and hstack"""
# a=np.arange(1, 10).reshape(3, 3)
# b=np.arange(21, 30).reshape(3, 3)
# c=np.vstack((a, b))
# print(c)

"""unique"""
# a=np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9])
# print(np.unique(a))

"""argmax"""
# a=np.arange(20,40).reshape(4, 5)
# print(a)
# c=np.argmax(a)
# print(c)

"""np.cumsum"""

# a=np.arange(1, 10).reshape(3, 3)
# print(a)
# print(np.cumsum(a)) #cumulative sum
# print(np.cumsum(a, axis=1)) #cumulative sum along axis=1
# print(np.cumsum(a, axis=0)) #cumulative sum along axis=0
# print(np.cumprod(a)) #cumulative product
# print(np.cumprod(a, axis=1)) #cumulative product along axis=1
# print(np.cumprod(a, axis=0)) #cumulative product along axis=0

"""np.where"""
a=np.arange(1, 10).reshape(3, 3)
print(a)
print(np.where(a>5, "yes", "no")) #if condition is true then yes else no

"""np.any"""
print(np.any(a>5)) #if any value is greater than 5 then true else false

"""np.all"""
print(np.all(a>5)) #if all value is greater than 5 then true else false

"""np.diff"""   
print(np.diff(a)) #difference between adjacent elements

"""percentile"""
print(np.percentile(a, 50)) #50th percentile

"""np.histogram"""
a=np.random.randint(1, 100, 20)
print(np.histogram(a, bins=[0,10,20,30,40,50,60,70,80,90,100])) #histogram

"""np.clip"""