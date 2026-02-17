#Parker Behagg 
#2/5/2026
#P1LAB1
#Use the math library to calculate the diameter, circumference, and area of a circle based on user input for the radius.

import math
radius = 0
diameter = 0
circumference = 0
area = 0

radius = float(input("Enter the radius of the circle: "))

diameter = 2 * radius
circumference = 2 * math.pi * radius
area = math.pi * radius ** 2
print("Diameter:", diameter)
print("Circumference:", circumference)
print("Area:", area)