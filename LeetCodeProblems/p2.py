"""You are given two  non-empty linked lists, representing two non-negative integers. Each digit is   stored  in reverse order, and each node can only store one  digit.

Please add two numbers and return a linked list representing the sum in the same form.

You can assume that neither number will begin with 0, except the number 0."""

list1=[2,4,3]
list2=[5,6,4]
class twonumberadd():
    def addTwoNumbers(self,list1,list2)->list:
        list1.reverse()
        list2.reverse()
        list3=[]
        carry=0
        for i, j in zip(list1,list2):
                sum=i+j+carry
                if sum>9:
                    carry=sum//10
                    sum=sum%10
                else:
                    carry=0
                list3.append(sum)
    def reverseit(self, list3):
        list3.reverse()
        return list3
        

obj1=twonumberadd()
a=obj1.addTwoNumbers(list1,list2)
b=obj1.reverseit(a)

