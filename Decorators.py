# import time

# try:
#     def calculate_time(func):
#         def wrapper(a,b):
#             start = time.time()
#             func(a,b)
#             print("this is a wapper function")
#             end=time.time()
#             print(f"total time is {end-start}")
#         return wrapper
# except SyntaxError as e:
#     print("invalid syntax")
# except TypeError as e:
#     print("typeError")
# except SyntaxError as e:
#     print("invalid syntax")

# finally:
#     print("i need to close everything")


# @calculate_time
# def add(a,b):
#     time.sleep(5)
#     print(a+b)

# add(5,6)


# channge function behviour without changing actual function



def decorator_fun(func):
    def change_it(a,b):
        if a<b:
            a,b=b,a
        return func(a,b)
    return change_it

@decorator_fun
def division(a,b):
    print(a/b)


division(10,2)
division(2,10)
