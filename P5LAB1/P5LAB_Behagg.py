#Parker Behagg
#P5LAB
#4/14/26

import random

def calc_change(amount):
    #prevents floating point data storage errors
    amount = round(amount * 100, 2)
    amount = int(amount)

    #initialize variables
    dollars = int(0.00)
    quarters = int(0.00)
    dimes = int(0.00)
    nickels = int(0.00)
    pennies = int(0.00)

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

    return {"dollars": dollars, "quarters": quarters, "dimes": dimes, "nickels": nickels, "pennies": pennies}

def main():
    amount_owed = round(random.uniform(0.01, 100.00), 2)
    print(f"you owe ${amount_owed}")
    payment = float(input("enter payment amount: "))

    while payment < amount_owed:
        print("payment is insufficient, please enter a valid amount")
        print(f"you owe ${amount_owed}")
        payment = float(input("re-enter payment amount: "))

    change = payment - amount_owed
    coins = calc_change(change)

    print(f"your change is ${change:.2f}")
    for key, value in coins.items():
        print(f"{key:<10}: {value:<5}")
main()