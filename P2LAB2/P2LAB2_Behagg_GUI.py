import tkinter as tk

#----define variables----
dict_car = {"camaro": 18.21, "prius": 52.36, "model s": 110.00, "silverado": 26.00}
car = ""
mpg = 0.0
miles = 0.0
gallons = 0.0

#----setup GUI----
root = tk.Tk()
root.geometry("400x300")
root.title("MPG Calculator")

#----define functions----

#calculator funtion
def calculate_mpg():
    global car, mpg, miles, gallons
    car = entry_car.get()
    if car.lower() in dict_car:
        mpg = dict_car[car.lower()]
        label_mpg.config(text=f"The miles per gallon for the {car} is: {mpg:.2f}")
    else:
        label_mpg.config(text=f"Sorry, the miles per gallon for the {car} is not available.")
        return
    
    miles = entry_miles.get()
    try:
        miles = float(miles)
        gallons = miles / mpg
        label_gallons.config(text=f"You will need {gallons:.2f} gallons of fuel to drive {miles:.2f} miles in the {car}.")
    except ValueError:
        label_gallons.config(text="Please enter a valid number for miles.")

#----create Widgets----
label_car = tk.Label(root, text="Enter the car model:")
label_car.pack(pady=5)

entry_car = tk.Entry(root)
entry_car.pack(pady=5)

label_miles = tk.Label(root, text="Enter the number of miles you want to drive:")
label_miles.pack(pady=5)

entry_miles = tk.Entry(root)
entry_miles.pack(pady=5)

button_calculate = tk.Button(root, text="Calculate MPG", command=calculate_mpg)
button_calculate.pack(pady=10)

label_mpg = tk.Label(root, text="")
label_mpg.pack(pady=5)

label_gallons = tk.Label(root, text="")
label_gallons.pack(pady=5)

#----start the GUI loop----
root.mainloop()