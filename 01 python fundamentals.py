#1. Predict the output
def mystery(x, y=[]):
    y.append(x)
    return y

print(mystery(1))
print(mystery(2))
print(mystery(3, []))
print(mystery(4))

'''
[1]
[1, 2]
[3] 
[1, 2, 4]
'''

#2. Write a function
def fizzbuzz(n):
    num = []
    for i in range(1, n+1):
        if i%3==0 and i%5==0:
            num.append("FizzBuzz")
        elif i%3==0:
            num.append("Fizz")
        elif i%5==0:
            num.append("Buzz")
        else:
            num.append(i)
    print(num)

fizzbuzz(20)
# [1, 2, 'Fizz', 4, 'Buzz', 'Fizz', 7, 8, 'Fizz', 'Buzz', 11, 'Fizz', 13, 14, 'FizzBuzz', 16, 17, 'Fizz', 19, 'Buzz']

#3. Explain in your own words
'''
0.1 + 0.2 != 0.3, because of floating point precision
0.1 is not exactly 0.1. it becomes 0.1000000..ab..  
similarly
0.2 is not exactly 0.2, it becomes 0.200000...yz...

because the stored binary value itself is already an approximation
before python ever displays anything — 0.1 + 0.2 and the literal 0.3 each round to a different nearest-representable double 
and comparing two different approximations with == fails

note: it's not that "Python rounds it to 1f precision for readability" as the cause of the mismatch 
display rounding is a separate, cosmetic thing (it's why print(0.1) shows "0.1" instead of a 17-digit number)

for financial systems we will use as follows:
from decimal import Decimal
Decimal("0.1") + Decimal("0.2") == Decimal("0.3") -> true

note: Decimal(0.1) -> Decimal('0.1000000000000000055511151231257827021181583404541015625')
rule: always construct Decimal from a string or an integer, never from a float
'''

#4. Scope puzzle
x = 10
def f():
    print(x)
    x = 20
f()
# UnboundLocalError: local variable 'x' referenced before assignment
