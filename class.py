



# class student():
#     def check_pass_fail(self):
#         if self.marks>=40:
#             return True
#         else:
#             return False
#     def __init__(self,name,marks):
#         self.name=name
#         self.marks =marks


# student1=student("Harry",85)
# student2=student("jerry",30)
# did_pass=student1.check_pass_fail()
# print(did_pass)
# did_pass=student2.check_pass_fail()
# print(did_pass)


#Two complex number addition

# class complex():
#     def __init__(self,real,imag):
#         self.real=real
#         self.imag=imag
#     def add(self,num):
#         real=self.real+num.real
#         imag=self.imag+num.real
#         result=complex(real,imag)
#         return result
    
# n1=complex(5,7)
# n2=complex(-4,4)
# result=n1.add(n2)
# print("real=",result.real)
# print("imag=",result.imag)
    
# class triangle():
#     def __init__(self,a,b,c):
#         self.a=a
#         self.b=b
#         self.c=c
#     def parimeter(self):
#         perimeter=(self.a+self.b+self.c)/3
#         print(perimeter)

# t1=triangle(3,4,5) 
# t1_perimeter=t1.parimeter() 
# t2=triangle(10,14,15) 
# t2_perimeter=t2.parimeter() 
# print(dir(t1))

# class polygoan():
#     def __init__(self,sides):
#         self.sides =sides
#     def perimeter(self):
#         perimeter=sum(self.sides)/3
#         print(f"perimeter of the polygoan is={perimeter}")
#     def display_message(self):
#         print("This is a polygoan")

# class triangle(polygoan):
#     def display_message(self):
#         print("This is a triangle")
#         # polygoan.display_message(self)
#         super().display_message()

# class Rectangle(polygoan):
#     def display_message(self):
#         print("This is a Rectangle")

# t1=triangle([3,4,5])
# Perimeter_of_traingle= t1.perimeter()
# t1.display_message()
    


# quantity =3
# itemno =567
# price =49.95
# print("I want {2} pieces of item {0} for {1} dollars.".format(quantity,itemno,price))

# set1 = {1,2,3,4,5,6,7,8,9,0}
# set2 = {4,5,6,7}
# print(set2.issubset(set1)) 

# dictionary = {"a":1, "b":2, "c":3}
# print(dir(dictionary))
# a=dictionary.pop("a")
# print(a)
# print (dictionary)

# y=int(input("Please enter the total number="))
# square_dict = {x**2 for x in range(10)}
# print(square_dict)

# def even_number(n):
# 	for x in range(n):
# 		if x%2==0:
# 	   		print(x)
# even_number(20)

# Python program to print Fibonacci Series

#Using For LOOP
# num = 10
# n1, n2 = 0, 1
# print(n1, n2, end=" ")
# for i in range(2, num):
#     n3 = n1 + n2
#     n1 = n2
#     n2 = n3
#     print(n3, end=" ")

#Using Recursive Function  

# def fib_ser(i):
#     if i<=1:
#         return i
#     else:
#         return (fib_ser(i-1)+fib_ser(i-2))
# num=10    
# for i in range(num):
# 	print(fib_ser(i),end=" ")
        
#Exception Handling
# class ValueTooHighError(Exception):
#  def __init__(self, message):
#  	self.message = message
# # Use case of the custom exception
# def check_value(x):
#   if x > 100:
#     raise ValueTooHighError("Value is too high.")
#   else:
#     print("Value is within the limit.")
          
# try:
#  	check_value(200)
# except ValueTooHighError as e:
#  	print(e.message)
	