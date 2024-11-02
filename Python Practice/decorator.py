# def decor(func):
#     def inner(a,b):
#         return func(a,b)*2
#     return inner

# @decor
# def fun1(x,y):
#     return x+y

# # new_func=decor(fun1(3,2))
# # print(new_func())

# print(fun1(3, 2))

"""Multiple decorator on same function"""

# def dec1(fun):
#     def inner():
#         return fun().upper()
#     return inner

# def dec2(fun):
#     def inner():
#         return fun().split()
#     return inner
# @dec2
# @dec1
# def myname():
#     first_name=input("Please enter your first name:")
#     last_name=input("Please enter your last name:")
#     return first_name+" "+last_name

# # output=dec2(dec1(myname))
# # print(output())
# print(myname())


"""Same decorator on multiple function"""

# def smart_dic(func):
#     def inner(*args):
#         try:
#             return func(*args)
#         except ZeroDivisionError:
#             return "Please do not divide by zero"
#     return inner

# @smart_dic
# def div1(a, b):
#     return a/b

# @smart_dic
# def div2(a, b,c):
#     return a/b/c

# print(div1(2,4))
# print(div1(0, 4))
# print(div1(4,0))
# print(div2(2, 4, 5))
# div2(2, 4, 2)

"""Class decorators"""

def check_string(fun):
    def inner(*arg):
        for i in arg:
            if type(i)==str:
                return "Please enter only numbers"
        return fun(*arg)
    return inner

@check_string
def add(*args):
    return sum(args)


print(add(1, 2, 3, 4, 5))