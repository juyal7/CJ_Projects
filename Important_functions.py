# print("hello everyone", end=",")
# print("my name is cj")
# print(dir(print))

#Rnage Function"

# range1= range(10)
# print(set(range1))


#Map function
#  try:
#     string=["apple","mango", "banana","grapes"]
#     list=[1,2,3,4,5,6,7]
#     Func1=map(lambda x:x+1,list)
#     print(list(Func1))
# except:

list1=[1,2,3,4,4,5]
tuple1=(1,2,3,4,4,5)
set1={1,2,3,4,4,5}
dic={1:1,2:2,3:3,4:4,4:4,5:5}
# print(list1)
# # print(tuple1)
# print(set1)
# # print(dic)

# def prim_Number(num):
#     if num == 1:    
#         print(f"{num} is not a prime number")
#     else:   
#         for i in range(2,num):  
#             if num % i == 0:    
#                 print(f"{num} is not a prime number")
#                 break   
#         else:   
#             print(f"{num} is a prime number" )
# prim_Number(8)

# def decreasing_pattern(n):
#     for i in range(n):
#         for j in range(i+1):
#             print("*", end="")
#         print()
# decreasing_pattern(6)

# def right_pattern(n):
#     for i in range(n):
#         for j in range(i,n):
#             print(' ',end="")
#         for j in range(i+1):
#             print("*", end="")
#         print()
# right_pattern(6)



list1=[1,2,9,4,4,5]

# list1.append(6)
# list1.insert(3,8)
# list1.reverse()
# list1.remove(9)
# list1.pop()

tuple1=(1,2,3,4,4,5,1,1)

# print(tuple1.count(1))
# print(tuple1.index(4))


set1={1,2,3,4,4,5}
# set1.add(9)
# set1.remove(3)
# set1.pop()
# print(set1[0])
# print(set1)

# import math
# print(math.floor(5/2))
# print(math.ceil(5/2))


# y=[x for x in range(10) if x%3==0]
# print(y)



# dic={1:1,2:2,3:3,4:4,4:4,5:5}
# y = (dic.values())
# print(y)

# name =("Sushanth",)
# print(name)
# print(type(name))
# print(5/2)
# print(5%2)
# print(5//2)

# sum=eval(input("please enter expression="))
# print(sum)
# print(type(eval))
# print(dir(eval))

# from sys import argv
# first_name=argv[0]
# last_name=argv[1]
# middle=argv[2]
# print(f"my name is {first_name}")
# print(f"my name is {last_name}")
# print(f"my name is {middle}")

# a=0
# while a<5:
#     print(f"CJ{a}")
#     if a==3:
#         pass
#     a=a+1

# for i in range(6):
#     for j in range(i+1):
#         print(" " ,end="")
#     for j in range(i,6):
#         print("*" ,end="")
#     for j in range(i,6):
#         print("*" ,end="")
#     for j in range(i+1):
#         print(" " ,end="")
#     print()
# else:
#     print("CJ")

list=tuple(['a','b','c','d','e'])
# list1=''.join(list)
# print(list1)

# def addition(a,b):
#     return a+b

# sum=addition

# print(sum(2,4))
tuple1 = (1, 2, 3)
tuple2 = (1,8,5,2,3)
dec1 = [1,8,5,2,3]
# print(tuple1 is tuple2)
# tuple3=sorted(tuple2)
# print(tuple3)
# print(type(tuple3))
# tuple3.append(6)
# print(id(tuple3))
# print(id(tuple2))
# print(id(dec1))
# print(id(sorted(dec1)))


# class maths:
#     def __str__(self):
#        print(f"Area and perimetr of a rectange is")
#     def __init__(self,length,width):
#         self.length=length
#         self.width=width
#     def area_perimeter(self):
#         area=self.length*self.width
#         perimeter=2*(self.length+self.width)
#         return(area,perimeter)
#     def __del__(self):
#         print("object destroyed")

# r1=maths(5,7)
# r2=r1.area_perimeter()
# print(r2)
# del r2

# list_1=[x for x in range(5)]
# print(list_1)

# def add(x, y, z = 0): 
#     return x + y+z

# print(add(1,3))
# print(add(1,3,7))


##########################################################################################

#Polymorphism with class

# class India:
#     def capital(self):
#         print("capital of india is delhi")
#     def language(self):
#         print("official langaguage of india is hindi")
#     def flag(self):
#         print("national flag of india is tri-colour")
# class US:
#     def capital(self):
#         print("capital of US is WDC")
#     def language(self):
#         print("official langaguage of US is ENGLISH")
#     def flag(self):
#         print("national flag of US is unkown")

# indian_person=India()
# USA_Person=US()

# for country in (indian_person, USA_Person):
#     country.capital()
#     country.language()
#     country.flag()


#Polymorphism with Inheritance: 
'''This process of re-implementing a method in the child class is known as Method Overriding.'''

# class bird():
#     def intro(self):
#         print("This is a bird")
#     def flight(self):
#         print("some can fly and some can't")
# class hen(bird):
#     def flight(self):
#         print("I can't fly")
# class sparrow(bird):
#     def flight(self):
#         print("I can fly")

# bird_0=bird()
# bird_0.flight()
# bird_1=hen()
# bird_1.flight()
# bird_2=sparrow()
# bird_2.flight()

#*args and **kwargs in Python
# def myFunc(arg1,*argv):
#     print(f"first argument is {arg1}")
#     for i in argv:
#         print(f"next arg are {i}")

# myFunc("my","name","is","cj")


#Python zip()
# list_1 = ['a','b','c','d']
# list2=[1,2,3,4]
# for i,(name,age) in enumerate(zip(list_1,list2)):
#     print(i,name,age)
    
# tuple1 = (1, 2, 3)
# tuple2 = ('a', 'b', 'c')
# zipped = zip(tuple1, tuple2)
# result=list(zipped)
# print(result)

### class variable and instance variable
# class myname():
#     x=0   #class variable
#     def __init__(self,a,b):
#         self.a=a
#         self.b=b
#         myname.x=myname.x+1
#     def add(self):
#         return self.a+self.b  
# obj1=myname(5,4)
# # obj2=myname(3,2)
# print(obj1.add())
# # y=obj2.add()
# print(myname.x)


####Private members####
class base():
    def __init__(self):
        self.a= "my name"
        self.__b="can't access it"
        print(self.a)
        print(self.__b)
class child(base):
    def __init__(self):
        self.c="i am child"
        print(self.c)
        # base.__init__(self)
        print(base.a)
    
obj1=child()
# obj2=base()


