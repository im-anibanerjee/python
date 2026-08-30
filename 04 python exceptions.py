#1. safe_divide(a, b)
def safe_divide(a, b):
    try:
        return a/b
    except ZeroDivisionError:
        print('cannot divide by 0')
        return None
    finally:
        print('final block ran after try/except')

result = safe_divide(6, 6)
print(result)
'''
final block ran after try/except
1.0
'''
result = safe_divide(6, 0)
print(result)
'''
cannot divide by 0
final block ran after try/except
None
'''

'''
note: if you want to run the tr-except block as a script and not inside the function
    def safe_divide(a, b):
        return a/b
    try:
        result = safe_divide(6, 0)
    except ZeroDivisionError:
        print("cannot divide by 0")
        result = None
    print(result)
    
    cannot divide by 0
    None
'''

def safe_divide(a, b):
    try:
        return a/b
    except TypeError:
        print('values are not of required type int/float/long')
        return None
    finally:
        print('final block after try/except')

result = safe_divide("6", "3")
print(result)
'''
values are not of required type int/float/long
final block after try/except
None
'''

def safe_divide(a, b):
    try:
        return a/b
    except (ZeroDivisionError, TypeError) as e:
        print(f'bad data: {e}')
        print(str(e))

safe_divide(6,0)
'''
bad data: division by zero
division by zero
'''
safe_divide("6", "3")
'''
bad data: unsupported operand type(s) for /: 'str' and 'str'
unsupported operand type(s) for /: 'str' and 'str'
'''

#2. Custom exception, applied to your own code
class InsufficientBalanceError(Exception):
    '''raised when withdrawing more than availale balance'''
    pass

class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance

    def __repr__(self):
        return f"BankAccount('owner':{self.owner}, 'balance':{self.balance})"

    def deposit(self, amount):
        self.balance = self.balance + amount

    def withdraw(self, amount):
        if amount>self.balance:
            raise InsufficientBalanceError(
                f'insufficient funds, current balance: {self.balance}, trying to withdraw: {amount}'
                )
        else:
            self.balance = self.balance - amount
            print(f'amount withdrawn: {amount}, available balance: {self.balance}')

account = BankAccount("Ani", 2000)
print(account)
# BankAccount('owner':Ani, 'balance':2000)

account.deposit(1000)
print(account)
# BankAccount('owner':Ani, 'balance':3000)

account.withdraw(1000)
# amount withdrawn: 1000, available balance: 2000
print(account)
# BankAccount('owner':Ani, 'balance':2000)

# account.withdraw(5000)
# print(account)
'''
raise InsufficientBalanceError(
__main__.InsufficientBalanceError: insufficient funds, current balance: 2000, trying to withdraw: 5000
)
'''

#3. Trace the execution
def process(n):
    try:
        result = 10 / n
    except ZeroDivisionError:
        print("A: caught zero division")
    else:
        print(f"B: got {result}")
    finally:
        print("C: cleanup")

process(2)
print("---")
process(0)
'''
B: got 5.0
C: cleanup
---
A: caught zero division
C: cleanup
'''

#4. 
'''
a bare except like:
    except:
        print("something went wrong")
catches catches literally everything including KeyboardInterrupt (Ctrl+C), SystemExit
and every possible bug in the code - a typo that raises NameError, a logic error raising TypeError 
all get silently swallowed and reported as the same vague "something went wrong" 
we lose the ability to tell a user-input mistake apart from a real bug in the program

a pass exception like:
    except:
        pass
does catches the exception, but it doesnot display what was the exception for
it simply lets the code to run silently (code doesnot crash, since pass) even though an exception was caught

'''