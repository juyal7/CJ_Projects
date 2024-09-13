#even or odd
# def check_even_odd(n):
#     if n%2==0:
#         print("This number is even")
#     else:
#         print("This number is odd")
# check_even_odd(6)
# check_even_odd(5)

#posive or negative

# def check_postive_negative(n):
#     if n>0:
#         print("This number is postive")
#     elif n==0:
#         print("This number is zero")
#     else:
#         print("This number is negative")
# check_postive_negative(3)
# check_postive_negative(-4)
# check_postive_negative(0)

#Prime Number
# def prime_number(n):
#     if n<=1:
#         return False
#     for i in range(2,int((n/2))+1):
#         if n%i==0:
#             return False
#     return True

# num=int(input("please enter the number = "))
# if prime_number(num):
#     print("number is prime")
# else:
#     print("number is not a prime")



# def prime_number():
#     num= int(input("please enter the number="))
#     if num>1:
#         for i in range(2,int(num/2)-1):
#             if num%i==0:
#                 print("number is not a prime")
#                 break
#         else:
#             print("number is prime number")

# prime_number()


# febinocci_series

# num=int(input("please enter ther number="))
# a,b=0,1
# sum=0
# if num<=0:
#     print("please enter the number greater than 0")
# else:
#     for i in range(0,num):
#         print(sum, end=" ")
#         a=b
#         b=sum
#         sum=a+b

# recurssion

# def recursion(n):
#     num_1
#     if n==0:
#         return 0
#     elif (n==1):
#         return 1
#     else:
#         num_1 = recursion(n-1) + recursion(n-2)
#         return (num_1)
# num=int(input(("Please enter the number=")))
# recursion(num)
# print(f"fabonic for {num} is {recursion(num)}")


# num= int(input("Enter the number= "))
# if num <= 1:
# 	print(f"Please enter number greater than {num}")
# else:
# 	for i in range(2,int(num/2)+1):
# 		if num%2==0:
# 			print(f"{num} is not a prime number")
# 			break
# 	else:
# 		print(f"{num} is a prime number")


# num=int(input("Enter the number= "))
# if num<=0:
#     print("Please enter the positive number")
# else:
#     first_number=0
#     second_number=1
#     sum=0
#     for i in range(0,num):
#         print(f"{sum}",end=" ")
#         first_number=second_number
#         second_number=sum
#         sum=first_number+second_number


###Write a program to check if the given number is palindrome or not
# num=int(input("Enter the number= "))
# temp=num
# reverse=0

# while temp>0:
#     reminder=temp%10
#     reverse=(reverse*10)+reminder
#     temp=temp//10

# if num==reverse:
#     print("number is pailindrome")
# else:
    # print("number is not pailindrome")


# letter=input("Please enter the string=")
# reverse_1=letter[::-1]
# print(reverse_1)

# if reverse_1==letter:
#     print("this string is pailindrome")
# else:
#     print("this string is not pailindrome")

# num=int(input("Enter the number= "))
# for i in range(0,num):
#     for j in range(i,num):
#         print(" ",end=' ')
#     for j in range(i+1):
#         print("*",end=' ')
#     for j in range(i+1):
#         print("*",end=' ')
#     for j in range(i,num):
#         print(" ",end=' ')
#     print()


num=int(input("Please enter the number="))

factorial=1

for i in range(1,num+1):
    factorial=factorial*i

print(factorial)


# letter = input("Pleaae enter the number=")
# letter_list=letter[::-1]
# print(letter_list)


################################################
#fabonic series

# num= int(input("please enter the number="))
# if num<0:
#     print("Pleae enter positive number")
# else:
#     first_number=0
#     second_number=1
#     sum=0
#     for i in range(1,num+1):
#         print(sum, end=" ")
#         first_number=second_number
#         second_number=sum
#         sum=first_number+second_number

#prime number
# num= int(input("please enter the number="))
# if num<=1:
#     print(f"Pleae enter number greater than {num}")
# else:
#     for i in range(2,int(num/2)+1):
#         if num%i==0:
#             print(f"{num} is not a prime number")
#             break
#         print(f"{num} Number is a prime number")



        
# class MyClass:
#     agr1=5
#     agr2=4
#     sum=0
#     @classmethod
#     def class_method(cls):
#         sum=cls.agr1+cls.agr2
#         print(f"This is a class method {sum}")
    
#     @staticmethod
#     def static_method():
#         print("This is a boy")
#         print(f"This is a class method {}")


# obj1=MyClass()
# obj1.class_method()


# def str_to_int(s):
#     num=0
#     n=len(s)

#     for i in s:
#         num=num*10 + (ord(i)-48)
#     print(num)

# if __name__== '__main__': 
#     s='-123'
#     str_to_int(s)


# list=[x for x in range(0,50,5)]
# print(list)

# print((lambda x,y : x+y)(5,7))


# defining a decorator
def hello_decorator(func):

    # inner1 is a Wrapper function in 
    # which the argument is called
    
    # inner function can access the outer local
    # functions like in this case "func"
    def inner1():
        print("Hello, this is before function execution")

        # calling the actual function now
        # inside the wrapper function.
        func()

        print("This is after function execution")
        
    return inner1

@hello_decorator
# defining a function, to be called inside wrapper
def function_to_be_used():
    print("This is inside the function !!")


# passing 'function_to_be_used' inside the
# decorator to control its behaviour
# function_to_be_used = hello_decorator(function_to_be_used)


# calling the function
function_to_be_used()