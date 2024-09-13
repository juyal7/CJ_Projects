class calculator1:
    def add(self,a,b):
        self.a=a
        self.b=b
        return a+b
    def subtract(self,a,b):
        if a>b:
            return a-b
        else:
            print(f"-{b-a}")
    def multi(self,a,b):
        return a*b
    def div(self,a,b):
        return a/b

calc1=calculator1()
print(calc1.add(5,7))
calc1.subtract(5,7)



a=input("please enter the number = ")
flag =False

if a>1:
    for a in 
