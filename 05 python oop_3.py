#5. Property
class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance 

    def __repr__(self):
         return f"BankAccount('owner':{self.owner}, 'balance':{self.balance})"

    @property   # get()
    def funds(self):
        return self.balance

    @funds.setter   #set()
    def funds(self, value):
        if value<0:
            raise ValueError('value cannot be -ve')
        else:
            self.balance = value

    def withdraw(self, amount):
        if amount>self.balance:
            raise ValueError(f'insufficient funds; current balance: {self.balance}, trying to withdraw: {amount}')
        else:
            self.balance = self.balance - amount
            print(f'amount withdrawn: {amount}, current balance: {self.balance}')

account = BankAccount("Ani", 200)
print(account)
# BankAccount('owner':Ani, 'balance':200)
# <__main__.BankAccount object at 0x00000280E2112F40>; without __repr__()
print(account.balance)
# 200; access public variable balance

print(account.funds)
# 200; using the property's get() method

account.funds = 5000
print(account)
# BankAccount('owner':Ani, 'balance':5000); using the property's set() method

account.withdraw(400)
# amount withdrawn: 400, current balance: 4600

'''
account.funds = -5000
# raise ValueError('value cannot be -ve')
# ValueError: value cannot be -ve
using the property's set() method
'''

'''
set() guard is 
    * to assign account's balance 
    * validation check (against -ve) before assigning balance
withdraw() guard is
    * to wothdraw amount from account's balance
    * validation check (against hifgher amount) before withdrawing
'''

#9. Dataclass, done right
from dataclasses import dataclass, field
@dataclass
class Cart:
    owner: str
    item: list = field(default_factory=list)

    '''
    item: list = field(default_factory=[])
    when Python needs to build the default (any time you don't pass item explicitly), 
    it tries to call default_factory() — i.e. []() — which raises TypeError: 'list' object is not callable. 
    you want to hand it the list constructor itself,
    '''
    '''
    item: list = field(default_factory=list)
    owner: str
    this format will raise error
    every field without a default must come before every field with one
    because the auto-generated __init__ can't have a required positional parameter show up after an optional one. 
    hence the fix: owner first, item second.
    '''

    def __post_init__(self):
        if not self.owner:
            raise ValueError(f'owner cannot be empty; owner: {self.owner}')

cart1 = Cart("Ani", ["eggs", "rice"])
print(cart1)
# Cart(owner='Ani', item=['eggs', 'rice'])

cart2 = Cart("", ['eggs'])
# ValueError: owner cannot be empty; owner: 

'''
cart2 =  Cart(["eggs", "rice"])
no error from __post_init__ because
    self.owner is now ["eggs", "rice"], a non-empty list, truthy
    'if not self.owner' evaluates to False
    so the check never fires, no ValueError raised
    item falls back to default [] since not supplied

    owner must be genuinely empty, but has no default
    so it must be passed explicitly as empty string

no type error despite owner:str and passing a list, because
    'owner: str' is a hint, not enforcement
    python stays dynamically typed even in a dataclass, annotation is just documentation
    nothing at runtime checks the match

    @dataclass reads annotations only to know which fields exist
    (for generated __init__, __repr__, __eq__)
    not to check the actual type
    it stores whatever you pass, any type
'''
