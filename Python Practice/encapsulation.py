# class point():
#     def __init__(self,x,y):
#         self.x = x
#         self.y = y
#         print("point created")
#     def __strt__(self):
#         return f"({self.x},{self.y})"
    
#     def EuclidiN_distance(self, other):
#         return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
    
#     def distance_from_origin(self):
#         return self.EuclidiN_distance(point(0,0))
    

# class Line:
#     def __init__(self, A, B, C):
#         self.A = A
#         self.B = B
#         self.C = C
        
#     def __str__(self):
#         return f"{self.a}x + {self.b}y + {self.c} =0"
    
#     def point_on_line(line, point):
#         if line.a * point.x + line.b * point.y + line.c == 0:
#             return "lies on line"
#         else:
#             return "does not lie on line"
        
#     def shortest_distance(line, point):
#         return abs(line.a * point.x + line.b * point.y + line.c) / (line.a**2 + line.b**2)**0.5
    
#     def perpendicular(line, point):
#         return -line.a / line.b
    
#     def slope(line):
#         return -line.a / line.b
    
# point1=point(1,2)
# point2=point(3, 4)


class Person:
    def __init___(self,name,gender):
        self.name=name
        self.gender=gender
        
def greet(person):
    print("hi my name is", person.name , "and I am a", person.gender)
    p1=Person('CJ', 'male')
    return p1

p=Person('x', 'y')
x=greet(p)
print(x.name, x.gender)
    