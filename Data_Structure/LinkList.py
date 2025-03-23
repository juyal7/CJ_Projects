class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    
    #Empty link list
    def __init__(self):
        self.head = None
        self.n=0
        
    def __len__(self):
        return self.n

    def insert_head(self,value):
        
        new_node=Node(value)
        
        new_node.next=self.head
        print(new_node.next)
        print(self.head)
        self.head=new_node
        
        self.n=self.n+1
    
    def __str__(self):
        curr=self.head
        result=''
        while curr!=None:
            result=result+str(curr.data)+'->'
            curr=curr.next
        return result[:-2]
 
    """Insert from tail(append)"""
    def insert_tail(self, value):
        new_node=Node(value)
        #if last node is head node
        if self.head==None:
            self.head=new_node
            self.n=self.n+1
            return
        #if last node is not head node
        curr=self.head
        while curr.next!=None:
            curr=curr.next
        curr.next=new_node
        self.n=self.n+1
        
    """insert in middle"""

    def insert_after(self, after, value):
        new_node=Node(value)
        curr=self.head
        while curr!=None:
            if curr.data==after:
                break
            curr=curr.next
        if curr!=None:
            new_node.next=curr.next
            curr.next=new_node
            self.n=self.n+1
        else:
            return 'Item not found'

    def insert_head(self, value):
        new_node=Node(value)
        new_node.next=self.head
        self.head=new_node
        self.n=self.n+1

    """head"""    
    def delete_head(self):
        if self.head==None:
            return 'Empty LinkedList'
        self.head=self.head.next
        self.n=self.n-1

    """Pop"""
    def delete_tail(self):
        if self.head==None:
            return 'Empty LinkedList'
        curr=self.head
        while curr.next.next!=None:
            curr=curr.next
        curr.next=None
        self.n=self.n-1
          
    """Remove"""
    def remove(self, value):
        if self.head==None:
            return 'Empty LinkedList'
        
        curr=self.head
        while curr.next!=None:
            if curr.next.data==value:
                break
            curr=curr.next
        if curr.next==None:
            return 'Item not found'
        else:
            curr.next=curr.next.next
            self.n=self.n-1

    def clear(self):
        self.head=None
        self.n=0

    def search(self,value):
        curr=self.head
        pos=0
        
        while curr!=None:
            if curr.data==value:
                return pos
            curr=curr.next
            pos=pos+1
            
        return "Item not found"
                
    def reverse(self):
        prev_node=None
        curr_node=self.head
        
        while curr_node!=None:
            next_node=curr_node.next
            curr_node.next=prev_node
            prev_node=curr_node
            curr_node=next_node
        
        self.head=prev_node
            
        

L=LinkedList()
L.insert_head(1)
L.insert_head(2)
# L.insert_after(1,2)
# L.insert_tail(3)
# L.insert_tail(4)
# L.insert_tail(5)
# L.reverse()
print(L)
