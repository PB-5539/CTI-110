#Parker Behagg 
#2/5/2026
#P1LAB1
#Use the math library to calculate the diameter, circumference, and area of a circle based on user input for the radius.

import math
radius = 0
diameter = float(0)
circumference = float(0)
area = float(0)
print()
radius = input("Enter the radius of the circle: ")
if radius == "exit":
    print("Exiting the program.")
else:
    radius = float(radius)
    diameter = 2 * radius
    circumference = 2 * math.pi * radius
    area = math.pi * radius ** 2
    print()
    print("----Results----")
    print()
    print(f"Diameter: {diameter:.1f}")
    print()
    print(f"Circumference: {circumference:.2f}")
    print()
    print(f"Area: {area:.3f}")
    print()
