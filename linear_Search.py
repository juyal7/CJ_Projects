import time 
def calculate_time(func):
    def wrapper(argv,*argv1):
        start = time.time()
        func(argv,*argv1)
        print("this is a wapper function")
        end=time.time()
        print(f"total time is {end-start}")
    return wrapper


# list=[1,4,5,6,7,8,9,3]

# num=int(input("Please enter the number you want to search="))
# @calculate_time
# def search_me(a):
#     for i in range(len(list)):
#         if list[i]==num:
#             print(f"I am at {i} postion" )
#             break
#     else:
#         print("I am not in list")


# search_me(num)