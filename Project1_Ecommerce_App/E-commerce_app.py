import uuid #Importing uuid to create Unit id
from termcolor import colored
import colorama
colorama.init()

# from itertools import product

#users class  
class users():
     #Type=Dictionary, Storing all admin Ids.
     all_admin_users={} 
     #Type:-Dictionary, Storing all customers Ids
     all_customer_users={}
     # Type:-Dictionary, Storing all Products in E-Commerce website
     product_category={}
     # Type:-protected class attribute, Storing unique admin passcode for accessing all admin rights.
     _default_admin_id="admin123"

#Login Class inheriting User class
class login(users): 
    
    #Constructor takObjectin paremeter user_type while new object of the class initiated
    def __init__(self,user_type):
        #Input from user for asking existing or new user
        login_type=int(input(colored("""Please select from the following
                             1-Existing user
                             2-New User \n""",'yellow')))
        #Logic to select admin or customer and Existing or New User
        if user_type==1:
            if login_type==1:
               self.login_admin()
            else:
               self.New_user_admin()
        else:
            if user_type==1:
               self.login_customer()
            else:
                self.New_user_customer()
     
    #The method is taking inputs from the customer/admin and authenticating them
    def login_admin(self):
            self.admin_id=input(colored
                                ("Please enter your login id=", "green"))
            self.user_password=input(colored("please enter your password=",'blue'))
            return self.Authentication(self.admin_id,self.user_password)
            
    #Method creating new admin credentials 
    def New_user_admin(self):
                admin_seceret_id=input(colored("Please enter admin_seceret_passcode=",'magenta'))
                if admin_seceret_id==login._default_admin_id:
                    admin_id=input("Please enter admin id=")
                    user_password=input("please enter admin password=")
                    login.all_admin_users[admin_id]=user_password
                    print("Successfull created admin id")
                    
                else:
                    print("Sorry, You are not autorised to create account as admin")
  
    #Method Using for loging customer and creating new id
    def login_customer(self,):
            self.admin_id=input(colored("Please enter your login id(Customer)=","green"))
            self.user_password=input(colored("please enter Customer password=","green"))
            if self.Authentication(self.admin_id,self.user_password):
                 self.session_id = str(uuid.uuid4())
                 print(self.session_id)
                 
    #Method creating new customer credentials 
    def New_user_customer(self):
                    Customer_id=input("Please enter customer id=")
                    Customer_password=input("please enter admin password=")
                    login.all_customer_users[Customer_id]=Customer_password
                    print("Successfull created customer id")

    #Authenticating
    def Authentication(self,user_name,password):
        self.user_name=user_name
        self.password=password
        if self.user_name in login.all_admin_users:
            if login.all_admin_users[self.user_name]==self.password:
                print(colored("Authentication Passed",'green'))
                return True
            else:
                print(colored("Wrong password",'red'))
                return False
        else:
             print(colored("Wrong user id"),'red')
             return False 
             
    
        print("Welcome to the Demo Marketplace")
                     
#Product Class inheriting Login class
class Product(login): 
     #Cart for storing items added to cart by customer
     cart={} 
     
     #Constructor used for Displaying multiple options in e-commerce Website
     def __init__(self):
          while True:
            print("""Please select the following options
                  #####Note-->Options 2,3 are only available for admin""")
            print("1. View all categories")
            print("2. Add new category")
            print("3. Remove category")
            print("4. Add item to cart")
            print("5. View cart")
            print("6. Remove item from cart")
            print("7. Checkout")
            print("8. Exit")
            choice=int(input("Enter your choice:"))
            if choice==1:
                print(users.product_category)
            elif choice==2:
                self.add_new_category()
            elif choice==3:
                self.remove_category()
            elif choice==4:
                self.add_item_cart()
            elif choice==5:
                print(Product.cart)
            elif choice==6:
                self.remove_item_cart()    
            elif choice==7:
                self.checkout()
            elif choice==8:
                break
            else:
                print("Invalid choice. Please try again.")
                  
     #Method used by admin for new category to e-commerce website
     def add_new_category(self):
          print("For adding a New Category, please enter admin id and password")
          if self.login_admin():
               while True:
                    main_category = input("Enter the main category name: ").strip().lower()
                    if main_category and main_category not in self.product_category:
                         break
                    print("Invalid category name or category already exists. Please try again.")

               new_category = {}

               while True:
                    add_subcategory = input("Do you want to add a subcategory? (yes/no): ").lower()
                    if add_subcategory != 'yes':
                         break

                    while True:
                         subcategory = input("Enter subcategory name: ").strip().lower()
                         if subcategory and subcategory not in new_category:
                              break
                         print("Invalid subcategory name or subcategory already exists. Please try again.")

                    items = {}
                    while True:
                         item_name = input("Enter item name (or press enter to finish): ").strip().lower()
                         if not item_name:
                              break
                         try:
                              item_price = float(input(f"Enter price for {item_name}: "))
                              # items.append({"name": item_name, "price": item_price})
                              items[item_name]=item_price
                         except ValueError:
                              print("Invalid price. Please enter a number.")

                    new_category[subcategory] = items

               print("\nNew category summary:")
               print(f"Main category: {main_category}")
               for sub, items in new_category.items():
                    print(f"  Subcategory: {sub}")
                    for name,price in items.items():
                         # print(f"    - {item['name']}: ${item['price']:.2f}")
                          print(str(name)+': '  + str(price))
                         

               confirm = input("\nDo you want to add this category? (yes/no): ").lower()
               if confirm == 'yes':
                    self.product_category[main_category] = new_category
                    print(f"Added new category: {main_category}")
               else:
                    print(colored("Category addition cancelled."),"red")

          else:
               print(colored("Authentication failed. Unable to add new category."),'red')
     
     #Method used by admin for removing category to e-commerce website
     def remove_category(self):
          print("For removing a category, please enter admin id and password")
          if self.login_admin():
               print("Please select from the following list:", list(login.product_category.keys()))
               selected_Category = input("Please select from above categories=")
               if selected_Category in login.product_category:
                    del login.product_category[selected_Category]
                    print("Category removed successfully")
               else:
                    print("Category not found")
            
     #Method used by Customer for adding items to the shoping cart
     def add_item_cart(self):
          while True:
               select = input("Do you want to add items yes/no=").lower()
               if select == "no":
                    break
               print("Please select the category from:", list(login.product_category.keys()))
               selected_Category = input("Please select from above categories=")
               
               if selected_Category in login.product_category:
                    print("Please select from the following list:")
                    print(list(login.product_category[selected_Category].keys()))
                    selected_subcategory = input("Please select from above subcategories=")
                    print("Please select from the following list:")
                    print(login.product_category[selected_Category][selected_subcategory])
                    selected_item = input("Please select from above items=")
                    # quantity = int(input(f"Enter quantity for {selected_item}: "))
                    # Product.cart.insert(selected_item)
                    Product.cart[selected_Category+"_"+selected_subcategory+"_"+selected_item]=login.product_category[selected_Category][selected_subcategory][selected_item]
    
    #Method used by Customer for removing items to the shoping cart
     def remove_item_cart(self):
          print("Please select what you want to remove",self.cart)
          remove_item=input("Please select item to remove=")
          if remove_item in self.cart:
               self.cart.pop(remove_item)
               print("########Item removed from cart###########")
     
     #Method used for payment checkout
     def checkout(self):
          if not Product.cart:
               print("Your cart is empty. Nothing to checkout.")
               return

          print("\n===== Checkout =====")
          print("Items in your cart:")
          total_amount = 0
          for item, price in Product.cart.items():
               print(f"{item}: ${price:.2f}")
               total_amount += price
          print(f"\nTotal amount: ${total_amount:.2f}")

          # Choose payment method
          while True:
               payment_method = input("\nChoose payment method (1. Credit Card, 2. PayPal, 3. Cash on Delivery): ")
               if payment_method in ['1', '2', '3']:
                    break
               print("Invalid choice. Please try again.")

          # Process payment (this is a simplified version)
          print("\nProcessing payment...")
          if payment_method == '1':
               card_number = input("Enter your credit card number: ")
               # In a real application, you would integrate with a payment gateway here
               print(f"Payment of ${total_amount:.2f} processed successfully with credit card ending in {card_number[-4:]}.")
          elif payment_method == '2':
               email = input("Enter your PayPal email: ")
               print(f"Payment of ${total_amount:.2f} processed successfully with PayPal account {email}.")
          else:
               print(f"Order placed successfully. You will pay ${total_amount:.2f} upon delivery.")

          # Generate order confirmation
          order_id = str(uuid.uuid4())[:8]  # Generate a unique order ID
          print(f"\nOrder Confirmation - Order ID: {order_id}")
          print("Thank you for your purchase!")

          # Clear the cart after successful checkout
          self.cart.clear()

          # In a real application, you would save the order details to a database here

          return order_id

#main fucntion using above classes 
def main():
     while True:
          print(colored("Welcome to the Demo Marketplace",'yellow'))
          user_type=int(input("""please select type of user 
                                   1-Admin
                                   2-Customer \n """))   
          if user_type==1 or user_type==2: 
               if login(user_type):
                    Product()
          else:
               print(colored("Invalid choice","red"))
               break

#calling main function
if __name__ == "__main__":
     main()