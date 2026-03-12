#Parker Behagg
#P3LAB
#2/25/26
#a program that takes a money amount and calculates the change in coins efficiently

#initialize variables
amount = float(0.00)
dollars = int(0.00)
quarters = int(0.00)
dimes = int(0.00)
nickels = int(0.00)
pennies = int(0.00)

#prompt user
amount = float(input("Enter money as Float: "))

#prevents floating point data storage errors
amount = round(amount * 100, 2)
amount = int(amount)

#calculate Change
dollars = amount // 100
amount = amount - (dollars*100)
quarters = amount // 25
amount = amount - (quarters*25)
dimes = amount // 10
amount = amount - (dimes*10)
nickels = amount // 5
amount = amount - (nickels*5)
pennies = amount // 1

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