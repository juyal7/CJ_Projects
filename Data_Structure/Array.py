import ctypes

class my_class:
    def __init__(self):
        self.size=1
        self.n=0
        self.A=self.__make_array(self.size)
    """Array"""
        
    def __make_array(self,size):
        return (size*ctypes.py_object)()
    
    """Length"""
    def __len__(self):
        return self.n
    
    """Append"""
    def append(self, element):
        if self.n==self.size:
            self.__resize(self.size*2)
        self.A[self.n]=element
        self.n+=1

    """Resize"""
    def __resize(self,new_size):
        B=self.__make_array(new_size)
        self.size=new_size
        for i in range(self.n):
            B[i]=self.A[i]
        self.A=B
    """Print"""
    def __str__(self):
        result=""
        for i in range(self.n):
            result+=str(self.A[i])+","
        return "[+result[:-1]+]"

    """Get item"""

L=my_class()
L.append(1)
L.append(2)
L.append(3)
L.append(4)
print(L)