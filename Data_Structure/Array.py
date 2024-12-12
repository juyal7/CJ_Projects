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
        return "["+result[:-1]+"]"

    """Get item"""
    def __getitem__(self, index):
        if 0<=index<self.n:
            return self.A[index]
        else:
            return "IndexError - Index out of range"

    """Set item"""
    def __setitem__(self, index, value):
        if 0<=index<self.n:
            self.A[index]=value
        else:
            return "IndexError - Index out of range"

    """Delete item"""
    def __delitem__(self, index):
        if 0<=index<self.n:
            for i in range(index, self.n-1):
                self.A[i]=self.A[i+1]
            self.n-=1
        else:
            return "IndexError - Index out of range"
        if self.n==self.size//4:
            self.__resize(self.size//2)
            return "Resized"
    """Clear"""
    def clear(self):
        self.n=0
        self.size=1
        return "Cleared"""
    
    """Find"""
    def find(self, element):
        for i in range(self.n):
            if self.A[i]==element:
                return i
        return "Element not found"""

    """Insert"""
    def insert(self, index, element):
        if 0<=index<self.n:
            if self.n==self.size:
                self.__resize(self.size*2)
            for i in range(self.n, index, -1):
                self.A[i]=self.A[i-1]
            self.A[index]=element
            self.n+=1
        else:
            return "IndexError - Index out of range"    
    """Remove"""
    def remove(self, element):
        index=self.find(element)
        if type(index)==int:
            self.__delitem__(index)
        else:
            return index
    """Pop"""
    def pop(self, index=-1):
        if 0<=index<self.n:
            element=self.A[index]
            self.__delitem__(index)
            return element

L=my_class()
L.append(1)
L.append(2)
L.append(3)
L.append(4)
print


#####
########
###