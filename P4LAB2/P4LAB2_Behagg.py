#Parker Behagg
#3/17/26
#P4LAB2
#use loops to diplay a multiplication table from input.


yn = "yes"
while yn.lower() == "yes":
    input_from_user = int(input("enter an integer: "))
    if input_from_user > 0:
        for integer in range(13):
            result = input_from_user*integer
            print(f"{input_from_user} * {integer} = {result}")
    elif input_from_user < 0:
        print("no negative numbers please")
    elif input_from_user == 0:
        print("please enter a number greater than 0")
    yn = input("would you like to run the program again? (yes/no): ")
print()
print("exiting...")
print("InputInterrupt")