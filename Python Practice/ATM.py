class Atm:
    def __init__(self):
        self.pin = ""
        self.balance = 0
        self.menu()
 
    def menu(self):
        print("Menu")
        user_input=input("""
        1. Enter 1 to create pin:-
        2. Enter 2 to change pin:-
        3. Enter 3 to check balance:-
        4. Enter 4 to withdraw:-
        5. Enter 5 to exit
        """)
        if user_input=="1":
            self.create_pin()
        elif user_input=="2":
            self.change_pin()
        elif user_input=="3":
            self.check_balance()    
        elif user_input=="4":
            self.withdraw()
        else:
            exit() 
                   
    def create_pin(self):
        user_pin=input("Enter your pin:-")
        self.pin=user_pin
        user_balance=int(input("Enter balance:-"))
        self.balance=user_balance 
        print("Pin set successfully")
        self.menu()      
    
    def change_pin(self):
        old_pin=input("Enter old pin:-")
        if old_pin==self.pin:
            new_pin=input("Enter new pin:-")
            self.pin=new_pin
            print("Pin changed successfully:-")
            self.menu()
        else:
            print("Wrong pin")
            self.menu()
    
    def check_balance(self):
        input_pin=input("Enter your pin:-")
        if input_pin==self.pin:
            print("Your balance is:-",self.balance)
            self.menu()
        else:
            print("Wrong pin")
            self.menu()
    
    def withdraw(self):
        amount=int(input("Enter amount:-"))
        input_pin=input("Enter your pin:-")
        if input_pin==self.pin:
            if amount<=self.balance:
                self.balance=self.balance-amount
                print("Withdrawal successful")
                print("Your remaining balance is:-", self.balance)
                self.menu()
            else:
                print("Insufficient balance")
                self.menu() 
        else:
            print("Wrong pin")
            self.menu()    
    
    def exit(self):
        pass
      
obj=Atm()