#Parker Behagg
#P3HW2
#3/12/26

#recieve input from user
name = input("enter employee name: ")
hours = float(input("enter hours worked: "))
pay = float(input("enter employee pay rate: "))

#calculate regular pay, overtime hours, overtime pay, and total pay
if hours > 40:
    overtime_hours = hours - 40
    regular_pay = 40 * pay
    overtime_pay = overtime_hours * (pay * 1.5)
else:
    overtime_hours = 0
    regular_pay = hours * pay
    overtime_pay = 0


print("--------------------------------------------------------------------summary---------------------------------------------------------")
print("employee name: ", name)
print()
print(f"{'Hours Worked':<20} {'Pay Rate':<20} {'Overtime Hours':<20} {'Overtime Pay':<20} {'Regular Pay':<20} {'Total Pay':<20}")
print("------------------------------------------------------------------------------------------------------------------------------------")
print(f"{hours:<20.2f} ${pay:<20.2f} {overtime_hours:<20.2f} ${overtime_pay:<20.2f} ${regular_pay:<20.2f} ${regular_pay + overtime_pay:<20.2f}")