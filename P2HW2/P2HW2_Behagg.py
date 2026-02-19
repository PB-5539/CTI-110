#Parker Behagg
#2/19/26
#P2HW2
#program to calculate the lowest, highest, average, and sum of a list of grades in a class

#initialize variables
grades = []
grade = 0
#ask user for grades for module 1-6
grade = float(input("Enter grade for module 1: "))
grades.append(grade)
grade = float(input("Enter grade for module 2: "))
grades.append(grade)
grade = float(input("Enter grade for module 3: "))
grades.append(grade)
grade = float(input("Enter grade for module 4: "))
grades.append(grade)
grade = float(input("Enter grade for module 5: "))
grades.append(grade)
grade = float(input("Enter grade for module 6: "))
grades.append(grade)
#calculate lowest, highest, average, and sum of grades
lowest = min(grades)
highest = max(grades)
average = sum(grades) / len(grades)
total = sum(grades)
#display results
print()
print("----Results----")
print("Lowest grade: " + str(lowest))
print("Highest grade: " + str(highest))
print("Average grade: " + str(f"{average:.2f}"))
print("Total grade: " + str(total))