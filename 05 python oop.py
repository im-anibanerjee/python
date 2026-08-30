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
            raise ValueError(f'insufficient funds, current balance: {self.balance}, trying to withdraw: {amount}')
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

account.withdraw(5000)
print(account)
'''
raise ValueError(f'insufficient funds, current balance: {self.balance}, trying to withdraw: {amount}')
ValueError: insufficient funds, current balance: 2000, trying to withdraw: 5000
'''