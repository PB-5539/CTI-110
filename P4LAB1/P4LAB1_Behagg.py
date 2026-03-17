#Parker Behagg
#3/17/26
#P4LAB1
#drawing using loops and turtle


import turtle as tl

window = tl.Screen()
tl.bgcolor("Light Blue")
tl.color("Black","Green")
for i in range(5):
    tl.forward(50)
    tl.left(90)
    tl.forward(50)
tl.forward(50)
tl.begin_fill()
for i in range(1):
    for i in range(2):
        tl.left(45)
        tl.forward(70)
        tl.left(45)
    tl.right(90)
tl.back(100)
tl.end_fill()
tl.forward(100)

print("DONE!!!")

secret = input("press enter to exit (or secret for a suprise!)")
if secret.lower() == "secret":
    print("yippee!")
    tl.reset()
    for i in range(9):
        tl.forward(100)
        tl.left(40)
    for i in range(9):
        tl.forward(100)
        tl.left(60)
        tl.forward(185)
        tl.back(185)
        tl.right(20)

    

    input("press enter to exit")
else:
    print("exiting...")