#Parker Behagg 
#2/5/2026
#P1HW1
# simple calculator

#----define the calculator as a function to allow re-running without restarting the file----
def calculator():
 #----promtp the user for the type of calculation they want to perform----
    operation_type = input("which would you like to calculate, Exponents or Additon? ")
 #----use if statements to determine which type of calculation the user wants to perform----
    if operation_type.lower() == "addition":                                                                            #addition and subtraction
        print("operation selected: Addition")
        print()
        base_number = float(input("what is the base number (number to add to or subtract from): "))
        add_number = float(input("what is the number to add? (enter '0' to skip)" ))
        sub_number = float(input("what is the number to subtract? (enter '0' to skip)" ))
        result = base_number + add_number - sub_number
        print("base:", base_number, "add:", add_number,"sub:", sub_number, "=", result)
        repeat_calculator()
    elif operation_type.lower() == "exponents" or operation_type.lower() == "exponent":                                 #exponnents
        print("operation selected: Exponent")
        base_number = float(input("what is the base number (number to raise): "))
        exponent_number = float(input("what is the power to raise the base to: "))
        result = pow(base_number, exponent_number)
        print("base:", base_number, "exp:", exponent_number, "=", result, "Integer form:", int(result))
        repeat_calculator()
    elif operation_type.lower() == "both":                                                                              #calculate both starting with addition and then exponents
        print("operation selected: Both")
        print()
        print("----Addition----")
        print()
        base_number = float(input("what is the base number (number to add to or subtract from): "))
        add_number = float(input("what is the number to add? (enter '0' to skip) " ))
        sub_number = float(input("what is the number to subtract? (enter '0' to skip) " ))
        result = base_number + add_number - sub_number
        print("base:", base_number, "add:", add_number,"sub:", sub_number, "=", result)
        print()
        print("----Exponents----")
        print()
        base_number = float(input("what is the base number (number to raise): "))
        exponent_number = float(input("what is the power to raise the base to: "))
        result = pow(base_number, exponent_number)
        print("base:", base_number, "exp:", exponent_number, "=", result, "Integer form:", int(result))
        repeat_calculator()
    elif operation_type == "Exit" or operation_type == "exit":                                                          #exit the calculator
        print("calculator closed.")
    else:                                                                                                               #invalid input handling
        print("invalid operation type!")
        calculator()    

#----define a function to restart the calculator----
def repeat_calculator():
    again = input("would you like to use the calculator again? (y/n) ")
    if again.lower() == "y":
        print()
        print("Restarting...")
        print()
        print()
        print()
        calculator()
    elif again.lower() == "n":
        print("calculator closed.")
    else:
        print("invalid response!")
        repeat_calculator()

#----run the calculator----
calculator()
