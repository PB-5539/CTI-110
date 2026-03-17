#Parker Behagg
#3/17/26
#P4LAB2
#use loops to diplay a multiplication table from input.


yn = "yes"
while yn.lower() == "yes":
    input_from_user = int(input("enter an integer: "))
    for integer in range(13):
        if integer > 0:
            result = input_from_user*integer
            print(f"{input_from_user} * {integer} = {result}")
    yn = input("you ld you like to run the program again? (yes/no): ")