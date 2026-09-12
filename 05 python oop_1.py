#1. Build a BankAccount class 
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
            raise ValueError(f'insufficient funds; current balance: {self.balance}, trying to withdraw: {amount}')
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

'''
account.withdraw(5000)
print(account)
# raise ValueError(f'insufficient funds, current balance: {self.balance}, trying to withdraw: {amount}')
# ValueError: insufficient funds, current balance: 2000, trying to withdraw: 5000
'''

#2. Inheritance. Create a SavingsAccount(BankAccount)
class SavingsAccount(BankAccount):
    def __init__(self, owner, balance, interest_rate):
        super().__init__(owner, balance)
        self.interest_rate = interest_rate

    '''
    def __repr__(self):
            return f"SavingsAccount('owner':{self.owner}, 'balance':{self.balance})"
    
    # print(saccount)
    # SavingsAccount('owner':Ani, 'balance':10000)
    '''

    def apply_interest(self):
        self.balance = self.balance + (self.balance * self.interest_rate)
        '''
        print(self.balance)
        # 12000
        '''

saccount = SavingsAccount("Ani", 2000, 5)
saccount.apply_interest()
print(saccount)
# BankAccount('owner':Ani, 'balance':12000)

#3. __eq__ vs default equality
class Transaction:
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

    def __repr__(self):
        return f"Transaction(category: {self.category}, amount: {self.amount})"

    def __eq__(self, other):
        return self.category==other.category and self.amount==other.amount

t1 = Transaction("pasta", 200)
print(t1)
# Transaction(category: pasta, amount: 200)
t2 = Transaction("pasta", 200)
print(t2)
# Transaction(category: pasta, amount: 200)
t3 = Transaction("pizza", 300)
print(t3)
# Transaction(category: pizza, amount: 300)

print(t1==t2) # True
print(t1==t3) # False
print(t1 is t2) # False
# without __eq__(), t1==t2 would also return False as 't1 is t2'

#7. MRO
class A:
    def greet(self):
        return 'A'

class B(A):
    def greet(self):
        return 'B'

class C(A):
    def greet(self):
        return 'C'

class D(C, B):
    def greet(self):
        return 'D'

class E(B, C):
    def greet(self):
        pass

class F(B, C):
    pass

d = D()
print(d.greet())    # D
print(D.__mro__)    # (<class '__main__.D'>, <class '__main__.C'>, <class '__main__.B'>, <class '__main__.A'>, <class 'object'>)

# get A, B, C
print(A.greet(d))   # A
print(B.greet(d))   # B
print(C.greet(d))   # C

e = E()
print(e.greet())    # None
print(E.__mro__)    # (<class '__main__.E'>, <class '__main__.B'>, <class '__main__.C'>, <class '__main__.A'>, <class 'object'>)

f = F()
print(f.greet())    # B
print(F.__mro__)    # (<class '__main__.F'>, <class '__main__.B'>, <class '__main__.C'>, <class '__main__.A'>, <class 'object'>)