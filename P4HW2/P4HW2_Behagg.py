#Parker Behagg
#3/27/26
#P4HW2
name = ""
complete_pay = 0
employees = {}
total_pay = 0
while name.lower() != "done":
    #recieve input from user
    name = input("enter employee name or 'done' to stop: ")
    if name.lower() !="done":
        hours = float(input("enter hours worked: "))
        pay = float(input("enter employee pay rate: "))

        #calculate regular pay, overtime hours, overtime pay, and total pay
        if hours > 40:
            overtime_hours = hours - 40
            regular_pay = 40 * pay
            overtime_pay = overtime_hours * (pay * 1.5)
            total_pay = regular_pay + overtime_pay #i forgot to add this line in the submission
        else:
            overtime_hours = 0
            regular_pay = hours * pay
            overtime_pay = 0
            total_pay = regular_pay + overtime_pay
        temp_list = [hours, pay, overtime_hours, overtime_pay, regular_pay, total_pay]
        employees[name] = temp_list
        complete_pay += total_pay
        print("--------------------------------------------------------------------summary---------------------------------------------------------")
        print("employee name: ", name)
        print()
        print(f"{'Hours Worked':<20} {'Pay Rate':<20} {'Overtime Hours':<20} {'Overtime Pay':<20} {'Regular Pay':<20} {'Total Pay':<20}")
        print("------------------------------------------------------------------------------------------------------------------------------------")
        print(f"{hours:<20.2f} ${pay:<20.2f} {overtime_hours:<20.2f} ${overtime_pay:<20.2f} ${regular_pay:<20.2f} ${total_pay:<20.2f}")
print(f"Total Pay for All Employees: ${complete_pay:<20.2f}")