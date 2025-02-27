"""
row = 5

for i in range(1, row+1):
    for j in range(1, i+1):
        print(j, end=' ')  
    print("")
"""""

"""
a = input("Enter a number: ")
sum = 0
for i in range(1, int(a)+1):
    sum += i
print(sum)
"""""

"""""""""""""""
mult = 12

a = int(input("Enter a number to show multiplication table: "))

for i in range(1, mult+1):
    print(f"{a} x {i} = {a*i}")

"""

""""
numbers = [12, 75, 150, 180, 145, 525, 50]

for i in range(len(numbers)):
    if numbers[i] > 500:
        break
    elif numbers[i] % 5 == 0 and numbers[i] < 150:
        print(numbers[i])

"""


""""
a = 75869
count = 0

while a != 0:
    a = a // 10
    count += 1
print(count)

"""
""""
row = 5
k = 5

for i in range(0, row+1):
    for j in range(k-i, 0, -1):
        print(j, end=' ')
    print()
"""

""""
n = 5

for i in range(0, n+1):
    for j in range(n-i, 0, -1):
        print(j, end=' ')
    print()

"""
"""""
list1 = [10, 20, 30, 40, 50]
i = 0
for i in range(len(list1)):
    print(list1[-(i+1)], end=' ')

"""