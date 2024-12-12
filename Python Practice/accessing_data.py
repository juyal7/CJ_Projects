
"""Accessing dictionaries"""
# a = {"a":1,"b":2,"c":3,"d":4}



def accessing_values():
    for i in a.values():
        return i



def accessing_key():
    for i in a:
        print(i)
        
def accessing_both():
    for key,value in a.items():
        print(f"{key}:{value}")


def using_map():
    for i in map(a.get,a):
        print(i)

def using_zip():
    for i , j in zip(a.keys(),a.values()):
        print(f"{i} is {j}")   
# using_zip
# using_map()

# accessing_values()
# accessing_key()
# accessing_both()


b=[1,2,3,4,5,6]
c=[10,20,30,40,50,60]

# i=0
# while i<len(b):
#     print(b[i])
#     i=i+1

# for i, j in enumerate(b):
#     print(i,j)

# [print(i+j) for i, j in enumerate(b)]

# d=[d for i in range(10)]
# print(d)
# def sum_1(x,y):
#     return x+y
   


# d=list(map(sum_1,b,c))

# print(d)


# x=[1,2,3]
# y=[5,6,7]
# z=(lambda x,y:x+y)

# print(list(z))


a = {"a":1,"b":2,"c":3,"d":4}

print(type(a.keys()))


