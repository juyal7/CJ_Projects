def sort(list1):
    for i in range(len(list1)-1,0,-1):
        for j in range(i):
            if list1[j+1]>list1[j]:
                tmp=list1[j]
                list1[j]=list1[j+1]
                list1[j+1]=tmp

list1=[6,8,16,20,9,3,4,5,19,35,24]

sort(list1)
print(list1)


# lis1=(list1.sort())
# print(list1)