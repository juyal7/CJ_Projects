
'''What is the  class type of my_code
    we can create own class and create an object with my_code
 '''

class pycharm():
    def execute(self):
        print("compile and execute")

class jupiter():
    def execute(self):
        print("I can compile execute and debug")
    def resolve(self):
        print("I can resolve")

my_code_1=jupiter()
# my_code_1=pycharm()
class laptop():
    def run_code(self,my_code):
        my_code.execute()

lap1=laptop()
lap1.run_code(my_code_1)

