class User:
    def __init__(self):
        self.choice = input("Do you want to enroll (yes/no)? ")
        if self.choice.lower() == "yes":
            self.course = int(input("""Please select a course you want to enroll in:
                              1-Maths
                              2-Science
                              3-History
                              4-Computer Science
                              """))
            for i in range(5):
                self.__email = input("Please enter the email_id: ")
                if "@" in self.__email:
                    print("====Your entry is created===")
                    self.__password = input("Please set the password: ")
                    return
                else:
                    print("===Please enter a valid email===")
                    if i == 4:
                        print("Maximum tries reached")
                        break
        else:
            print("Thanks for visiting us")

    def validation(self):
        self.entered_password = input("Please enter the password: ")
        return self.__password==self.entered_password

# class Learner(User):
#     def new_enrollment_course(self):
#         if self.course==1:
#             print("Enrollment successful for Maths ")
#         elif self.course==2:
#              print("Enrollment successful Science")
#         elif self.course==3:
#              print("Enrollment successful History ")
#         elif self.course==4:
#              print("Enrollment successful Computer Science")
#         else:
#             print("Invalid course")

#     def drop_course(self):
#         self.drop_decision=input("Do you want to drop from course=")
#         if self.drop_decision=="yes":
#             self.drop_course_id=int(input("""Please select a course you want to enroll in:
#                               1-Maths
#                               2-Science
#                               3-History
#                               4-Computer Science
#                               """))
#             return self.drop_course_id


# class Instructor(User):
#     def add_course(self):
#         pass

#     def remove_course(self):
#         pass

class Course:
    pass

class Enrollment:
    pass
# obj1 = Learner()
# obj1.new_enrollment_course()
# obj1.drop_course()


obj1=Course()
print(id(obj1))
print(dir(obj1))