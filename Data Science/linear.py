# v1=[2,6]
# v2=[4,5]
# v3=[8,1]
# import math
# def dot_product(vector1,vector2):
#     result=0
#     for i in range(len(vector1)):
#         result+=vector1[i]*vector2[i]
#     return result
# def magnitude(vector):
#     result=0
#     for i in vector:
#         result+=i**2
#     return math.sqrt(result)
 
# print(dot_product(v1,v2)/magnitude(v2))
# print(dot_product(v1, v3)/magnitude(v3))
# print(dot_product(v2, v3)/magnitude(v3))
# print(dot_product(v2, v1)/magnitude(v1))

# import numpy as np
# np.linalg.norm(v1)

import numpy as np
a1=np.arange(1,10).reshape(3,3)
b1=np.arange(21, 30).reshape(3, 3)
c1=np.dot(a1, a1)
print(c1)