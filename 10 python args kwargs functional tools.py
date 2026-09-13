#1. Write a function describe_call(*args, **kwargs)
def describe_call(*args, **kwargs):
    print(f'args={args}, kwargs={kwargs}')

describe_call() # args=(), kwargs={}
describe_call(1, 2) # args=(1, 2), kwargs={}
describe_call(name='Ani')   # args=(), kwargs={'name': 'Ani'}
describe_call(1, 2, name='Ani', role='Software Engineer')   # args=(1, 2), kwargs={'name': 'Ani', 'role': 'Software Engineer'}

#2. Keyword-only in practice
# def make_user(name, *args, age, active=True):
'''
if we pass *args and then print(args), this will print all the args
but if we pass only * then nothing is collected and cannot print anything
so changed here for testing
'''
def make_user(name, *args, age, active=True):
    print(f'name:{name}, args:{args}, age:{age}, active:{active}')

make_user("Ani", 5, 6, 7, age=10, active=False) # name:Ani, args:(5, 6, 7), age:10, active:False
# make_user("Ani", 10)      # TypeError: make_user() missing 1 required keyword-only argument: 'age'
make_user("Ani", age=10)    # name:Ani, args:(), age:10, active:True
'''
error (args version): make_user() missing 1 required keyword-only argument: 'age'
error (bare * version): make_user_bare() takes 1 positional argument but 2 were given
'''

def make_user_1(name, *args, age, active=True, height):
    print(f'name:{name}, args:{args}, age:{age}, active:{active}, height:{height}')

make_user_1("Ani", 5, 6, 7, age=10, active=False, height=3) # name:Ani, args:(5, 6, 7), age:10, active:False, height:3
make_user("Ani", 5, 6, 7, age=10)   # name:Ani, args:(5, 6, 7), age:10, active:True

#3. Unpacking round-trip
def total(a, b, c):
    return a+b+c

values = [10, 20, 30]
print(total(*values))   # 60
values_dict = {'a':10, 'b':20, 'c':30}
print(total(**values_dict)) # 60

#4. map/filter vs. comprehensions
# using map/filter
arr = [i for i in range(1, 11)] # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
squares = map(lambda x: x**2, arr)
print(list(squares))    # [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

print(f'divisible by 3 are:{list(filter(lambda x: x%3==0, squares))}') # divisible by 3 are:[]
'''
result = filter(lambda x: x%3==0, squares)
print(list(result))

map/filter = lazy iterators, like generators
list(squares) drains it fully - no reset after
filter(squares) right after = squares already empty
filter finds nothing to check -> [] (not "none match")

fix: convert map to list ONCE, reuse that list
squares = list(map(...))
list(filter(..., squares))   # [9, 36, 81]
'''
squares = list(map(lambda x: x**2, arr))
result = filter(lambda x: x%3==0, squares)
print(list(result)) # [9, 36, 81]

# using comprehensions
squares = [x**2 for x in arr]
print(squares)  # [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
result = [x for x in squares if x%3==0] 
print(result)   # [9, 36, 81]
'''
filtering if, goes at the END (after for, no else needed)
decides IN or OUT; drops items that don't match
[x for x in squares if x%3==0]; only items divisible by 3, rest dropped

ternary if/else, goes in the output expr (BEFORE for, else required)
doesn't filter; every item kept, just transformed
[x if x%3==0 else -1 for x in squares]; all items kept, non-divisible ones become -1

mixing the two (if before for, no else) = SyntaxError
'''

#5. reduce, from scratch
from functools import reduce
num = [10, 30, 40, 20, 5, 95, 55, 75]
'''
max = reduce(lambda acc, x: acc>x, num)

num = [10, 30, 40, 20, 5, 95, 55, 75]
step 1: acc=10, x=30 -> 10>30 -> False; acc is now False, not 10 or 30
step 2: acc=False, x=40 -> False>40 ->  False; False behaves like 0 in a comparison, 0>40 is False
step 3: acc=False, x=20 -> False -> False
... every remaining step: False > (anything positive) -> False
result: False
'''
max = reduce(lambda acc, x: acc if acc>x else x, num)
print(max)  # 95

# Using reduce() for 'flatten lists' and 'multiply everything'
'''
flatten a list of lists with reduce:
acc starts as [] (the explicit start value: 3rd arg to reduce)
each step: acc + x -> concatenates the next sublist onto acc
'''
from functools import reduce
nested = [[1, 2], [3, 4], [5]]
flat = reduce(lambda acc, x: acc + x, nested, [])
print(flat)     # [1, 2, 3, 4, 5]

'''
step1: acc=[],        x=[1,2] -> [1,2]
step2: acc=[1,2],     x=[3,4] -> [1,2,3,4]
step3: acc=[1,2,3,4], x=[5]   -> [1,2,3,4,5]
'''

'''
multiply everything together with reduce:
no explicit start; acc begins as the FIRST element itself
each step: acc * x -> running product
'''
nums = [1, 2, 3, 4]
product = reduce(lambda acc, x: acc * x, nums)
print(product)     # 24

'''
step1: acc=1, x=2 -> 2
step2: acc=2, x=3 -> 6
step3: acc=6, x=4 -> 24
'''