# import pandas as pd
dec1={
    "name":["A","B","C"],
    "country":["d","e","f"],
    "gender":["m","f","m"]
    }
# df=pd.DataFrame(dec1)

# print(df)
# list1=[1,2,3,4]
# x=5
# y=x
# y=8
# print(id(x))
# print(id(y))
# print(id(dec1))

# str1="python"

# print("yp" in str1)


# b=[]
# a=[1,2,3]
# # b=a
# b=a.copy()
# a[0]=7
# print(a)
# print(b)


# with open("Test.txt","w") as file:
#     file.write("a/")
#     file.write("b/")
#     file.write("c")

# with open()
# list2=[]
# list1=[5,6,7]
# for i in list1:
#     list2.append(i**2)
# for i in range(1,11):
#     for j in range(1,11):
#         print(i*j,end="\t")
#     print()

# password="welcome"
# max_attempt=3
# for i in range(max_attempt):
#     user_password=input("please enter password=")
#     if user_password==password:
#         print("access it")
#         break

# import math 
# num = 25 
# result = math.sqrt(625) / num 
# print(result)

# print(bool(14), bool(), bool(1+2), bool(0))

# for x in [0, 1, 2]: 
#     for y in [0, 1, 2, 3, 4, 5]: 
#         print('yes')

# x = 10 
# y = 5 
# result = x // y + x % y 
# print(result)


# class A:
#     def __init__(self):
#         self.var1=100

#     def display1(self,var1):
#         self.var1=var1
#         print("class A:",self.var1)

# class B(A):
#     def display2(self,var1):
#         print("class B:",self.var1)


# obj1=B()
# print(obj1.var1)
# obj1.display1(200)

# class Phone:
#     def __init__(self,price,brand,camera):
#         print("inside super class")
#         self.__price=price
#         self.brand=brand
#         self.camera=camera
# class Smartphone(Phone):
#     def __init__(self,price,brand,camera,os,ram):
#         super().__init__(price,brand,camera)
#         self.os=os
#         self.ram=ram
#         print("Inside smartphone constructor")

# s=Smartphone(20000,"Apple","50MP","IOS","12")

#Two pointer o(n^2) to o(n)
# a= "abcdcba"
# def is_pandrome():
#     start=0
#     end=len(a)-1

#     while start<end:
#         if a[start]!=a[end]:
#             print("no")
#         start+=1
#         end-=1
    
#     print("yes")
 

# list1=[1,2,3,4,5]
# list2=["a","b","c","d","e"]
# print(zip(list1,list2))

# for i,j in zip(list1, list2):
#     print(f"{i}:{j}")

# list3=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

# even1=filter(lambda x: x%2==0,list3)
# print(list(even1))


# def multiple_all(list1):
#     list1.append(8)
#     print(list1)
# list2=[1,2,3,4,5]
# multiple_all(list2[:])
# print(list2)


# def greeting(name,age,greet="hell0"):
#     print(f"{greet} {name} {age}")

# greeting("CJ",29)

# print(dir(lambda))

# help(sum)

# even_odd=lambda x : "is even" if x%2==0 else f"f{x} is odd"
# print(even_odd)


# def outer_factorial(n)->int:
#     if not isinstance(n,int):
#         raise TypeError("Sorry number must be interger")
#     if n<0:
#         raise TypeError("Please eneter non-zero number")
#     def inner_factorial(n):
#         if n<=1:
#             return 1
#         else:
#             return n*inner_factorial(n-1)
#     return inner_factorial(n)
    
# # a=outer_factorial(4)
# print(outer_factorial(-6))



# from collections import Counter 

# print(Counter(["a","a","c","b","b","b"]))
# print(type(Counter()))


# def parent(num):
#     def first_child():
#         print("Hi, I'm Elias")

#     def second_child():
#         print("Call me Ester")

#     if num == 1:
#         return first_child()
#     else:
#         return second_child
    
# a=parent(2)
# b=parent(1)
# print(a)


# product_category={"Electronics":{"LG":["Mobile","watch","laptop"],"Apple":["iphone","MACbook","iwatch"]},
#                 "Clothing":{"zara":["a","b","c"],"H&M":["d","e","f"],}, 
#                 "Books":{"Fictional":["5","6","7"],"non_fictional":["1","2","3"]}}

# def selection():
#     cart=[]
#     select=input(print("Do you want to add items yes/no=")).lower()
#     while True:
#                if select == "no":
#                     break   
#                print(("Please select the catogery from \n",product_category.keys()))
#                selected_Category=input("Please select from above categories=")
#                if selected_Category in product_category.keys():
#                     print("Please select from the following list")
#                     print(product_category[selected_Category].keys())
#                     selected_subcategory=input("Please select from above subcategories=")
#                     if selected_subcategory in product_category[selected_Category].keys():
#                          print("Please select from the following list")
#                          print(product_category[selected_Category][selected_subcategory])
#                          selected_item=input("Please select from above items=")
#                          if selected_item in product_category[selected_Category][selected_subcategory]:
#                               cart.append(selected_item)
#                               select=input(print("Do you want to add items yes/no=")).lower()       
#     return cart()

# a=selection()

# def add_new_category(self):
#     print("For adding a New Category, please enter admin id and password")
#     if self.login_admin():
#         while True:
#             main_category = input("Enter the main category name: ").strip()
#             if main_category and main_category not in self.product_category:
#                 break
#             print("Invalid category name or category already exists. Please try again.")

#         new_category = {}

#         while True:
#             add_subcategory = input("Do you want to add a subcategory? (yes/no): ").lower()
#             if add_subcategory != 'yes':
#                 break

#             while True:
#                 subcategory = input("Enter subcategory name: ").strip()
#                 if subcategory and subcategory not in new_category:
#                     break
#                 print("Invalid subcategory name or subcategory already exists. Please try again.")

#             items = []
#             while True:
#                 item_name = input("Enter item name (or press enter to finish): ").strip()
#                 if not item_name:
#                     break
#                 try:
#                     item_price = float(input(f"Enter price for {item_name}: "))
#                     items.append({"name": item_name, "price": item_price})
#                 except ValueError:
#                     print("Invalid price. Please enter a number.")

#             new_category[subcategory] = items

#         print("\nNew category summary:")
#         print(f"Main category: {main_category}")
#         for sub, items in new_category.items():
#             print(f"  Subcategory: {sub}")
#             for item in items:
#                 print(f"    - {item['name']}: ${item['price']:.2f}")

#         confirm = input("\nDo you want to add this category? (yes/no): ").lower()
#         if confirm == 'yes':
#             self.product_category[main_category] = new_category
#             print(f"Added new category: {main_category}")
#         else:
#             print("Category addition cancelled.")

#     else:
#         print("Authentication failed. Unable to add new category.")



# class login():
#      pass
# class product():
#      pass
# class app(Login):
#      a="abc"
#      b="def"
#      obj=product()
#      def checkout():
# 
# cart={"a":1,"b":2,"c":3}
# remove_item=input("Enter item to remove=")
# cart.pop(remove_item)
# print(cart)

# str1="a"
# str2="b"
# str3="c"
# str4=(str1+"_"+str2+"_"+str3)
# print(str4)

# from termcolor import colored
# import colorama
# colorama.init()

# print(colored(str4,'red'))
# print(colored("Welcome to the Demo Marketplace","yellow"))


# def outer(func):
#     def inner(a,b):
#         return func(a,b) +1 
#     return inner
    
# @outer    
# def add(a,b):
#     c=a+b
#     return c

# print(add(2,3))


# import pdb ;pdb.set_trace
# import logging
# logging.basicConfig(filename='app.log', filemode="w", level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
# def factorial(n):
#     if n==0 or n==1:
#         logging.debug("This is a debug message")
#         return 1
#     else:
#         logging.debug("This is a debug message")
#         return n*factorial(n-1)
    

# # import pdb ;pdb.set_trace()
# a=factorial(-5)

# print(a)


# logging.info("This is an info message")
# logging.warning("This is a warning message")
# logging.error("This is an error message")
# logging.critical("This is a critical message")


# class car():
# 	_num_of_wheels=4
    
# 	def __init__(self,make,model,year):
# 		self.make=make
# 		self.model=model
# 		self.year=year

# 	def start_engine(self):
# 		return f"the engine of {self.make},{self.model} starts"

# 	# @staticmethod	
# 	def car_category(speed):
# 		if speed>300:
# 			return "sport"
# 		elif speed >120:
# 			return "sedan"
# 		else:
# 			return "compact"

# 	@classmethod
# 	def change_wheel_count(cls,count):
# 		cls._num_of_wheels=count
   
# obj1=car("Toyota", "Camry", 2022)
# # print(obj1.start_engine())
# # print(car.car_category(250))
# obj1.change_wheel_count(6)
# # print(car._num_of_wheels)
# print(car._num_of_wheels)



# import numpy as np
# import matplotlib.pyplot as plt

# # Create time points (using more points for smoother curves)
# t = np.linspace(0, 2*np.pi, 1000)

# # Create different frequency sine waves
# f1 = np.sin(3*t)       # 1 Hz
# f2 = np.sin(6*t)      # 2 Hz
# f3 = np.sin(9*t)      # 4 Hz

# # Create the plot
# plt.figure(figsize=(10, 6))  # Set figure size

# # Plot each sine wave with different colors and labels
# plt.plot(t, f1, 'b-', label='1 Hz')
# plt.plot(t, f2, 'r-', label='2 Hz')
# plt.plot(t, f3, 'g-', label='4 Hz')

# # Customize the plot
# plt.title('Sine Waves with Different Frequencies')
# plt.xlabel('Time')
# plt.ylabel('Amplitude')
# plt.grid(True)
# plt.legend()

# # Display the plot
# plt.show()


# class xyz():
#     def __init__(self, a, b):
#         self.a=a
#         self.b=b
#     def __iter__(self):
#         return self
#     def __next__(self):
#         if self.a>self.b:
#             raise StopIteration
#         current=self.a
#         if current%2==0:
#             self.a+=2
#             return current
#         else:
#             self.a+=1
#             return current


list1=[51,6,7,8,91]

list1[0],list1[1]=list1[1],list1[0]
# list1.sort()

print(list1)

# def __sort__(self):
#     for i in range(len(list1)-1):
#         for j in range(len(list1)-1):
#             if list1[j]>list1[j+1]:
#                 list1[j], list1[j+1]=list1[j+1], list1[j]
#                 print(list1)
            