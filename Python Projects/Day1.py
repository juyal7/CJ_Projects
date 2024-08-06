# ### Largest number in list############
# a=0
# list1 = [3,7,2,9,45,78,13,6]
# for i in list1:
#     if i>a:
#         a=i
#     print(a)
# print(a)

###########Largest among the list#####
list1=[]
num = int(input("please enter the total numbers= "))
for i in range(1,num+1):
    num2=int(input("please enter " + str(i) + " numer = "))
    list1.append(num2)
print("The Laregest number is", max(list1))
