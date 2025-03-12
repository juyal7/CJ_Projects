# list1=[1,2,3,4,5,7]
# list2=[]

# for i in list1[::-1]:
#     list2.append(i)
    
# print(list2)


#maximum

a=[1,7,4,6,83,9]
# max_value=[]
for i in range(len(a)):
    for j in range(i+1,len(a)):
        if a[i]>a[j]:
            a[i],a[j]=a[j],a[i]
print(a)

c=[1,2,3,4,45,4,6,98]
max_num=0
for i in c:
    if i>max_num:
        max_num=i
print(max_num)
