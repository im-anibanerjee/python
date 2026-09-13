#1. Write your own logging decorator
from functools import wraps
def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        args_params = [repr(i) for i in args]  
        kwargs_params = [f'{key}={value}' for key, value in kwargs.items()]
        # kwargs_params = [f"{k}={v!r}" for k, v in kwargs.items()] 
        '''
        repr(a) vs str(a):
        str()  -> human-readable form, no quotes around strings
        repr()  -> precise/unambiguous form, close to how you'd retype it
        
        same for numbers: str(2) == repr(2) == '2'
        differ for strings: str("hi") -> hi   |   repr("hi") -> 'hi' (quotes included)
        repr shows what KIND of thing it was, not just how it looks
        so add("2","3") logs as add('2', '3') with repr, not add(2, 3) like the real numeric call

        f"{v!r}" :
        !r = conversion flag inside an f-string
        tells Python: use repr(v) here instead of the default str(v)
        {v!r} is just shorthand for {repr(v)}

        [f"{k}={v!r}" for k, v in kwargs.items()] :
        kwargs.items() -> list of (key, value) pairs, e.g. [('x', 5), ('name', 'ani')]
        for k, v in ... -> unpacks each pair: k='x', v=5   then   k='name', v='ani'
        f"{k}={v!r}" -> builds "x=5"   then   "name='ani'" (quotes show it's a string)
        the [...] collects both into one list: ['x=5', "name='ani'"]
        '''
        all_params = ", ".join(args_params + kwargs_params)
        # print(all_params)  # 2, 3; 10, 15
        print(f'calling {func.__name__}({all_params})')
        result = func(*args, **kwargs)
        return result
    return wrapper

@log_calls
def add(x, y):
    return x+y

@log_calls
def minus(x, y):
    return abs(x-y)

print(add(2,3))         # calling add(2, 3) \n 5
print(minus(10, 15))    # calling minus(10, 15) \n 5

#2. Prove functools.wraps matters
from functools import wraps
def shout(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

@shout
def greetings(str):
    '''greets hi'''
    print(f"Hi, {str}")
greetings('Ani')    # Hi, Ani
print(greetings.__name__)   # wrapper (without @wraps(func)); greetings (with @wraps(func))
print(greetings.__doc__)    # None (without @wraps(func)); greets hi (with @wraps(func))

#4. Stacking order
def bold(func):
    def wrapper(*args, **kwargs):
        '''
        result = func(*args, **kwargs)
        return f'<b>{result}</b>'
        '''
        return f'<b>{func(*args, **kwargs)}</b>'
    return wrapper

def italic(func):
    def wrapper(*args, **kwargs):
        '''
        result = func(*args, **kwargs)
        return f'<b>{result}</b>'
        '''
        return f'<i>{func(*args, **kwargs)}</i>'
    return wrapper

@italic
@bold
def greetings(str):
    '''greets hi'''
    return f"Hi, {str}"
print(greetings("Ani")) # <i><b>Hi, Ani</b></i>

#5. Class-based decorator
import time
class Timer:
    def __init__(self, func):
        self.func = func
        self.timer = []
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1

        start = time.perf_counter()
        result = self.func(*args, **kwargs)
        elapsed = time.perf_counter() - start

        args_params = [repr(i) for i in args]
        kwargs_params = [f'{key}={value}' for key, value in kwargs.items()]
        all_params = ", ".join(args_params + kwargs_params)
        print(f'call: {self.count}, method: {self.func.__name__}({all_params})')

        self.timer.append(elapsed)
        if len(self.timer)==3:
            print(f'elapsed time of last 3 calls: {self.timer}')

        return result

@Timer
def greetings(str):
    '''greets hi'''
    print (f"Hi, {str}")

greetings("Ani")    # Hi, Ani \n call: 1, method: greetings('Ani')
greetings("Ani_1")  # Hi, Ani_1 \n call: 2, method: greetings('Ani_1')
greetings("Ani_2")
'''
Hi, Ani_2
call: 3, method: greetings('Ani_2')
elapsed time of last 3 calls: [0.00011099999999999999, 5.540000000000406e-05, 2.4099999999999122e-05]
'''
