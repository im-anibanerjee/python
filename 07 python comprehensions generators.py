#1. Predict, then verify
def gen():
    print("start")
    x = yield 1
    print(f"received: {x}")
    yield 2

g = gen()
print(next(g))  # start; (next line) 1
print(next(g))  # received: None; (next line) 2
'''
next(g) runs the generator until it hits a yield
anything printed along the way happens automatically, as a side effect
it stops only at yield, and hands back that value

like a person reading a script out loud
they freeze the instant they hit "yield"
resume only when tapped again with next()
whatever they say while reading is automatic, not asked for separately
the only thing print(next(g)) shows is the note handed at the freeze point
'''

#2. Exhaustion bug, on purpose
def squares_up_to(n):
    for i in range(1, n+1):
        yield i**2

s = squares_up_to(5)
print(next(s))  # 1
print(list(s))  # [4, 9, 16, 25]
print(list(s))  # []

#3. Memory comparison
list_sq = [i**2 for i in range(100000)]
print(list_sq[0])   # 0

gen_sq = (i**2 for i in range(100000))
print(next(gen_sq)) # 0

import sys
print(sys.getsizeof(list_sq))   # 800984
print(sys.getsizeof(gen_sq))    # 112

# 4. Build your own iterator
class EvenNumbers:
    def __init__(self, limit):
        self.current = 0
        self.limit = limit

    def __iter__(self):
        return self

    def __next__(self):
        # no checking, simply +2; basic way
        if self.current>=self.limit:
            raise StopIteration      
        value = self.current
        self.current = self.current + 2
        return value
    '''
        this part is checking exclusively if even or odd and then return
        while self.current<self.limit:
            value = self.current
            self.current = self.current + 1
            if value%2==0:
                return value
        raise StopIteration
    '''

for n in EvenNumbers(10):
    print(n)    # 0, 2, 4, 6, 8; all in next-line (one after the other)

#5. yield from
def flatten(arr):
    for i in arr:
        if isinstance(i, list):
            yield from i
        else:
            yield i

print(next(flatten([1, [2, 3], 4, [5]])))   # 1
print (list(flatten([1, [2, 3], 4, [5]])))  # [1, 2, 3, 4, 5]

'''
def yield_sublist(sub):          # a generator function, not a plain list
    for x in sub:
        yield x

def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from yield_sublist(item)    # delegating to a GENERATOR this time, not a list directly
        else:
            yield item

print(list(flatten([1, [2, 3], 4, [5]])))   # [1, 2, 3, 4, 5] - identical result
'''

'''
print(list(next(flatten([1, [2, 3], 4, [5]]))))
# TypeError: 'int' object is not iterable
'''

'''
print(list(flatten))
# TypeError: 'function' object is not iterable
'''