#Parker Behagg 
#2/5/2026
#P2HW1
# simple travel calculator, now with formatting

print("please fill out the following travel information to the best of your ability.")
budget = float(input("What is your total budget for the trip (in USD)? "))
destination = input("What is your travel destination? ")
gas = float(input("What is the estimated cost of gas for the trip (in USD)? "))
accomodation = float(input("What is the estimated cost of accomodation for the trip (in USD)? "))
food = float(input("What is the estimated cost of food for the trip (in USD)? "))
total_expenses = gas + accomodation + food
remaining_budget = budget - total_expenses


print()
print("----Travel Summary----")
print("Destination:", destination)
print("Total Budget: $" + f"{budget:,.2f}")
print("Estimated Gas Cost: $" + f"{gas:,.2f}")
print("Estimated Accomodation Cost: $" + f"{accomodation:,.2f}")
print("Estimated Food Cost: $" + f"{food:,.2f}")
print("Total Estimated Expenses: $" + f"{total_expenses:,.2f}")
print("Remaining Budget after Expenses: $" + f"{remaining_budget:,.2f}")