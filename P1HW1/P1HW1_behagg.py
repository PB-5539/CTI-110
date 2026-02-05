# simple calculator

operation_type = input("which would you like to calculate, Exponents or Additon? ")

if operation_type == "Addition" or operation_type == "addition":
    print("operation selected: Addition")
    print()
    base_number = int(input("what is the base number (number to add to or subtract from): "))
    add_number = int(input("what is the number to add? (enter '0' to skip)" ))
    sub_number = int(input("what is the number to subtract? (enter '0' to skip)" ))
    print("base:", base_number, "add:", add_number,"sub:", sub_number)
elif operation_type == "Exponents" or operation_type == "exponents" or operation_type == "Exponent" or operation_type == "exponent":
    print("operation selected: Exponent")
    base_number = int(input("what is the base number (number to raise): "))
    exponent_number = int(input("what is the power to raise the base to?"))
    print("base:", base_number, "exp:", exponent_number)