#Parker Behagg
#2/19/2026
#P2LAB2
#Use a dictionary to store the miles per gallon for different car models.

#----initialize variables and Dictionaries----
dict_car = {"camaro": 18.21, "prius": 52.36, "model s": 110.00, "silverado": 26.00}
car = ""
mpg = 0.0
miles = 0.0
gallons = 0.0

#----main program----
print()
#Prompt the user to enter a car model and check if it's in the dictionary. If it is, display the miles per gallon. If not, display an error message.
car = input("Enter the car model (or 'exit' to quit): ")
if car.lower() == "exit":
    print("Exiting the program.")
elif car.lower() in dict_car:
    mpg = dict_car[car.lower()]
    print()
    print(f"The miles per gallon for the {car} is: {mpg:.2f}")
else:    
    print()
    print(f"Sorry, the miles per gallon for the {car} is not available.")

#Prompt the user to enter the number of miles they want to drive and calculate how many gallons of fuel they will need based on the miles per gallon for the car model they entered.
miles = input("Enter the number of miles you want to drive: ")
if miles.lower() == "exit":
    print("Exiting the program.")
else:    
    miles = float(miles)
    gallons = miles / mpg
    print()
    print(f"You will need {gallons:.2f} gallons of fuel to drive {miles:.2f} miles in the {car}.")
