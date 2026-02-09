#Parker Behagg 
#2/5/2026
#P1HW1
# simple calculator

operation_type = input("which would you like to calculate, Exponents or Additon? ")

if operation_type == "Addition" or operation_type == "addition":
    print("operation selected: Addition")
    print()
    base_number = int(input("what is the base number (number to add to or subtract from): "))
    add_number = int(input("what is the number to add? (enter '0' to skip)" ))
    sub_number = int(input("what is the number to subtract? (enter '0' to skip)" ))
    result = base_number + add_number - sub_number
    print("base:", base_number, "add:", add_number,"sub:", sub_number, "=", result)
elif operation_type == "Exponents" or operation_type == "exponents" or operation_type == "Exponent" or operation_type == "exponent":
    print("operation selected: Exponent")
    base_number = int(input("what is the base number (number to raise): "))
    exponent_number = int(input("what is the power to raise the base to?"))
    result = pow(base_number, exponent_number)
    print("base:", base_number, "exp:", exponent_number, "=", result)
elif operation_type == "both" or operation_type == "Both":
    print()
    print("----Addition----")
    print()
    base_number = int(input("what is the base number (number to add to or subtract from): "))
    add_number = int(input("what is the number to add? (enter '0' to skip)" ))
    sub_number = int(input("what is the number to subtract? (enter '0' to skip)" ))
    result = base_number + add_number - sub_number
    print("base:", base_number, "add:", add_number,"sub:", sub_number, "=", result)
    print()
    print("----Exponents----")
    print()
    base_number = int(input("what is the base number (number to raise): "))
    exponent_number = int(input("what is the power to raise the base to?"))
    result = pow(base_number, exponent_number)
    print("base:", base_number, "exp:", exponent_number, "=", result)
else:
    print("invalid operation type! Please enter Addition, Exponents, or Both after restarting the program.")
