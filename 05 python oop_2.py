#4. Rewrite as a dataclass
from dataclasses import dataclass
@dataclass
class BankAccount:
    owner: str
    balance: int

    def withdraw(self, amount):
        if amount>self.balance:
            raise ValueError(f'insufficient funds; current balance: {self.balance}, trying to withdraw: {amount}')
        else:
            self.balance = self.balance - amount
            print(f'amount withdrawn: {amount}, current balance: {self.balance}')

account = BankAccount("Ani", 1000)
print(account)
# BankAccount(owner='Ani', balance=1000)
# since dataclass so uses __repr__ by default for print(); no need to write explicitly
account.withdraw(100)
# amount withdrawn: 100, current balance: 900

#6. __eq__ and __hash__
@dataclass
class Transaction:
    category: str
    amount: int

    def __hash__(self):
        '''
        pass
        # TypeError: __hash__ method should return an integer
        '''

        '''
        return hash((self.category, self.amount))
        # {Transaction(category='pizza', amount=5000), Transaction(category='pasta', amount=200)}
        '''
        return 1


t1 = Transaction("pasta", 200)
t2 = Transaction("pasta", 200)
t3 = Transaction("pizza", 5000)

print(t1==t2)
# since dataclass so uses __eq__ by defuault for 't1==t2'; no need to write explicitly
s = {t1, t2, t3}
print(s)
# {Transaction(category='pasta', amount=200), Transaction(category='pizza', amount=5000)}

'''
without the __hash__() written above, s={t1, t2} was giving error
# TypeError: unhashable type: 'Transaction'
'''

#8. Abstract base class
from abc import ABC, abstractmethod
class Shape(ABC):
    @abstractmethod
    def area(self):
        ...
@dataclass
class Circle(Shape):
    radius: int = 10

    def area(self):
        print(f'area of circle: {3.141559 * self.radius**2}')

@dataclass
class Rectangle(Shape):
    length: int
    width: int

    def area(self):
        print(f'area of rectangle: {self.length * self.width}')

class Square(Shape):
    def __init__(self, side):
        self.side = side

    '''
    def __repr__(self):
        return f'side: {self.side}'

    print(sq)
    # side: 10
    '''
      
    '''
    def area(self):
        pass

    print(sq.area)
    # None
    # even when we are giving pass, it indicates that abstract method 'area()' has been implemented
    '''
'''
s = Shape()
# TypeError: Can't instantiate abstract class Shape with abstract method area
'''
c = Circle()
c.area()
# area of circle: 314.1559

r = Rectangle(5, 10)
r.area()
# area of rectangle: 50

sq = Square(10)
# TypeError: Can't instantiate abstract class Square with abstract method area