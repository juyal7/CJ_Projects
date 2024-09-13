class calculator():
    def __init__(self,a,b):
        self.a=a
        self.b=b

    def add(self):
        sum=self.a + self.b
        print(sum)

    def __add__(self,other):
        a=self.a+ other.a
        b=self.b+ other.b
        return calculator(a,b)
    
obj1=calculator(4,6)
obj2=calculator(5,10)


obj=obj1+obj2
print((obj))

