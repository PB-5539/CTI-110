#Parker Behagg 
#2/5/2026
#P1HW2
# simple travel calculator

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
print("Total Budget: $", budget)
print("Estimated Gas Cost: $", gas)
print("Estimated Accomodation Cost: $", accomodation)
print("Estimated Food Cost: $", food)
print("Total Estimated Expenses: $", total_expenses)
print("Remaining Budget after Expenses: $", remaining_budget)