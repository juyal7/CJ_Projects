##It's a Guess game Project!!!!################
import random
#Enter the highest number of guess game
top_range=input("Type a number: ")
#this will check if entered number is digit or not
if top_range.isdigit():
    top_range=int(top_range)
#it will check if number is postive or not
    if top_range<=0:
        print("please type a number larger than 0 next time")
        quit()
else:
    print("Please enter a number next time ")
    quit()
#Generate random number
random_number= random.randrange(0,top_range)
print(random_number)
#variable to check pass and failed attempts
pass_guesses=0
fail_guess=0
#To take input from user and check guess number with entered
while True:
    user_guess = input("Make a guess: ")
    pass_guesses += 1
    fail_guess += 1
    if user_guess.isdigit():
        user_guess=int(user_guess)
    else:
        print("Please enter a number next time ")
        continue
    if user_guess == random_number:
        print("You win!!!!")
        print("You got it in ", pass_guesses, "guesses" )
        break
    else:
        print("You got it wrong")
        if fail_guess==5:
            print(" And it's ", fail_guess, "guess" )
            break
        elif user_guess > random_number:
            print("You're Number is above ")
        else:
            print("You're number is below ")



        
