#Parker Behagg 
#2/24/2026
#P2HW1
# simple travel calculator, now with alignment and formatting!

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
print(f"{"Destination:":<35} {destination}")
print(f"{"Total Budget:":<35} ${budget:.2f}")
print(f"{"Estimated Gas Cost:":<35} ${gas:.2f}")
print(f"{"Estimated Accomodation Cost:":<35} ${accomodation:.2f}")
print(f"{"Estimated Food Cost:":<35} ${food:.2f}")
print(f"{"Total Estimated Expenses:":<35} ${total_expenses:.2f}")
print()
print("----Budget Analysis----")
print(f"{"Budget Status:":<35} {'Within Budget' if remaining_budget >= 0 else 'Over Budget'}")
print(f"{"Remaining Budget:":<35} ${remaining_budget:.2f}")