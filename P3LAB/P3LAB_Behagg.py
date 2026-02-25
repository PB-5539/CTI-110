#Parker Behagg
#P3LAB
#2/25/26
#a program that takes a money amount and calculates the change in coins efficiently

#initialize variables
amount = float(0.00)
dollars = float(0.00)
quarters = float(0.00)
dimes = float(0.00)
nickels = float(0.00)
pennies = float(0.00)

#prompt user
amount = float(input("Enter money as Float: "))




#calculate Change
dollars = amount // 1
amount = amount - dollars
quarters = amount // 0.25
amount = amount - (quarters*0.25)
dimes = amount // 0.1
amount = amount - (dimes*0.1)
nickels = amount // 0.05
amount = amount - (nickels*0.05)
pennies = amount // 0.01

#decide what outputs to print
if amount == 0:
    print("no change")
if dollars > 0:
    print(f"Dollars: {dollars}")
if (amount > 0) and (amount < 0.01):
    print("Less than one cent")
if quarters > 0:
    print(f"Quarters: {quarters}")
if dimes > 0:
    print(f"Dimes: {dimes}")
if nickels > 0:
    print(f"Nickels: {nickels}")
if pennies > 0:
    print(f"Pennies: {pennies}")