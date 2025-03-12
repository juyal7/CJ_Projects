Phase-End Project: Creating a Shopping App Using Python

Problem Scenario: You have to develop a shopping application or e-commerce application 
which has login and public login features on the Python platform. 
The applications that have been developed should also include 
categories, such as 3–4 for footwear, clothing, electronics, etc. 
It should be possible to add and update categories in the application. 
Additionally, it must contain a feature that allows you to add or remove items from your cart.
 Finally, the program needs to support a variety of payment options, including UPI and debit cards. 
 This should be only backend implementation, and UX/UI and database connectivity are not required.


Guidelines:
•	A welcome message should initially be displayed in the e-commerce application, such as "Welcome to the Demo Marketplace".
•	User login and admin login should be created once the code for the welcome message has been written. For the creation of demo login and admin login, demo databases for those should be created for the user and admin verification, and session id creation.
•	After databases are created, create admin and user logins. It is necessary to construct a sample product catalog with three to four product categories, such as Boots, Coats, Jackets, and Caps. The product id, name, category id, and price should all be present for each item in the dummy database of the catalog. Both users and administrators can view the catalog.
•	User login rights include the ability to view cart contents, add items to carts, and remove items from carts. The user should be able to add items or delete items in the cart using session id, product id, and quantity.
•	Next, the program should provide demo payment checkout options, like Net banking, PayPal, UPI, etc. After selecting the payment option, a checkout message like, "Your order is successfully placed" or "You will be shortly redirected to the portal for Unified Payment Interface to make a payment of Rs. 2000", etc., should be displayed. 
•	Additionally, the admin can only log in using his credentials, and if the admin attempts to log in using another set of credentials, an error notice must appear.
•	Admin should not be able to interfere with any of the functions that the user can perform, as discussed above. An error should appear if the admin tries to carry out those tasks.
•	Furthermore, using the previously selected attributes, the admin should be able to add new products to the catalog. Additionally, the program needs to make it possible for an existing product to be modified using an admin session id.
•	The admin should then have the ability to remove any existing products from the already-generated catalog.
•	Lastly, understanding the dynamic demands of the market, the admin should be able to add a new category of product and delete the prevailing category of product from the catalog. 
•	Users should not be able to take advantage of any of the admin's rights, as described above.
