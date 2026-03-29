#Parker Behagg
#3/24/26
#P4HW1

from_user = ""
yesno = "yes"
score_amount = 0
scores = []
temp_score = 0
while yesno.lower() == "yes":
    score_amount = int(input("How Many Scores to enter: "))
    for i in range(score_amount):
        temp_score = int(input(f"Enter Score {i+1}: "))
        if (temp_score >= 0) and (temp_score <= 100):
            scores.append(temp_score)
        else:
            while not ((temp_score >= 0) and (temp_score <= 100)):
                print("invalid input")
                print("acceptable range: 0 - 100")
                temp_score = int(input(f"Enter Score {i+1} again: "))
            if (temp_score >= 0) and (temp_score <= 100):
                scores.append(temp_score)
    lowest = min(scores)
    average = sum(scores) / len(scores)
    if (average >= 90) and (average <= 100):
        grade = "A"
    elif (average >= 80) and (average <= 89):
        grade = "B"
    elif (average >= 70) and (average <= 79):
        grade = "C"
    elif (average >= 60) and (average <= 69):
        grade = "D"
    elif (average < 60):
        grade = "F"
    print("==============Results==============")
    print(f"{"Lowest Score":<15}{":":<1}{lowest:<5}")
    print(f"{"Raw List Data":<15}{":":<1}{str(scores):<5}")
    print(f"{"Average":<15}{":":<1}{average:<5}")
    print(f"{"Lowest Score":<15}{":":<1}{lowest:<5}")
    print("===================================")
    print()
    yesno = input("would you like to run the program again? ")
    while not ((yesno.lower() in ["y", "yes", "ye"]) or (yesno.lower() in ["n", "no"])):
        if yesno.lower() in ["y", "yes", "ye"]:
            yesno = "yes"
        elif yesno.lower() in ["n", "no"]:
            yesno = "no"
        else: 
            print("invalid input")
    
    
    
    
    