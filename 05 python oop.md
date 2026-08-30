# Topic 4 — Object-Oriented Programming: Classes, Inheritance & Dunder Methods

*Phase 1, Intermediate group — item 1 of 6. This is a bigger topic than the last three, so take it in two sittings if you need to. Type every example, then do the practice questions.*

---

## 1. Why classes at all

A class bundles **data** (attributes) and **behavior** (methods) that belong together into one thing. You've been using classes this whole time without writing your own — a `list` is a class, `"hello"` is an instance of the `str` class. Now you write the blueprint yourself.

```python
class Transaction:
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

    def is_large(self):
        return self.amount > 1000
```

- `class Transaction:` — defines the blueprint. `PascalCase` naming, unlike `snake_case` functions/variables.
- `__init__` — the constructor. Runs automatically when you create an instance. Sets up the object's starting state.
- `self` — refers to *this specific instance*. Every instance method takes `self` as its first parameter, but you never pass it explicitly — Python does that for you.
- `self.category = category` — attaches `category` as an **attribute** on this instance.

```python
t = Transaction("food", 200)
t.category          # "food"
t.amount             # 200
t.is_large()         # False
```

## 2. `self` — the thing that actually confuses people

`self` is just "the instance this method was called on." When you write `t.is_large()`, Python is really doing `Transaction.is_large(t)` behind the scenes — `t` gets passed automatically as `self`. This is why every instance method's signature starts with `self`, and why you never write it in the call itself.

```python
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1     # modifies THIS instance's count

a = Counter()
b = Counter()
a.increment()
a.increment()
print(a.count, b.count)     # 2 0 — separate objects, separate state
```

Each instance has its own copy of instance attributes — `a` and `b` don't share `count`, because each `Counter()` call runs `__init__` fresh and creates a new `self`.

## 3. Instance attributes vs class attributes

```python
class Employee:
    company = "CES"              # CLASS attribute — shared by ALL instances

    def __init__(self, name):
        self.name = name          # INSTANCE attribute — unique per instance

e1 = Employee("Ani")
e2 = Employee("Priya")
print(e1.company, e2.company)     # CES CES — same value, shared

Employee.company = "NewCo"        # change it on the CLASS
print(e1.company, e2.company)     # NewCo NewCo — both see it, because they share it

e1.company = "JustMine"           # this creates a NEW instance attribute on e1 only, doesn't touch the class
print(e1.company, e2.company)     # JustMine NewCo — now they've diverged
```

This is a real interview trap when the class attribute is something *mutable*, like a list — very similar in spirit to the mutable default argument bug from Topic 1:

```python
class Bad:
    items = []              # DANGER — shared mutable class attribute

    def add(self, item):
        self.items.append(item)

a, b = Bad(), Bad()
a.add("x")
print(b.items)               # ['x'] — surprise! b sees a's item, because items is SHARED
```

Fix: initialize mutable attributes inside `__init__`, not as class attributes, so each instance gets its own:

```python
class Good:
    def __init__(self):
        self.items = []      # each instance gets its OWN list
```

## 4. Instance methods vs `@classmethod` vs `@staticmethod`

```python
class Transaction:
    tax_rate = 0.18

    def __init__(self, amount):
        self.amount = amount

    def total_with_tax(self):                # instance method — needs self, works on THIS instance's data
        return self.amount * (1 + self.tax_rate)

    @classmethod
    def from_dict(cls, data):                  # classmethod — receives the CLASS, not an instance
        return cls(data["amount"])              # common use: alternative constructors

    @staticmethod
    def is_valid_amount(amount):                 # staticmethod — receives NEITHER self NOR cls
        return amount > 0                          # doesn't touch instance or class state at all — just lives here for organization
```

| | receives | typical use |
|---|---|---|
| instance method | `self` | operates on one instance's data — the default, most common case |
| `@classmethod` | `cls` (the class itself) | alternative constructors (`from_dict`, `from_json`), or anything that needs the class but not a specific instance |
| `@staticmethod` | neither | a utility function that's *related* to the class conceptually but doesn't need instance or class data |

```python
t = Transaction.from_dict({"amount": 500})    # calling the classmethod ON THE CLASS
Transaction.is_valid_amount(-5)                # False — calling the staticmethod, also on the class
```

## 5. Inheritance

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return f"{self.name} makes a sound"

class Dog(Animal):                       # Dog INHERITS from Animal
    def speak(self):                      # OVERRIDES the parent's speak()
        return f"{self.name} barks"

class Cat(Animal):
    pass                                  # inherits speak() AS-IS, no override needed

d = Dog("Rex")
c = Cat("Whiskers")
print(d.speak())     # "Rex barks"
print(c.speak())     # "Whiskers makes a sound" — used the parent's version
```

`super()` lets a child call the parent's version of a method — usually inside `__init__`, so you don't have to repeat the parent's setup logic:

```python
class Employee:
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

class Manager(Employee):
    def __init__(self, name, salary, team_size):
        super().__init__(name, salary)      # let Employee's __init__ handle name/salary
        self.team_size = team_size           # Manager adds its own extra attribute

m = Manager("Ani", 90000, 5)
print(m.name, m.salary, m.team_size)          # Ani 90000 5
```

Without `super().__init__(...)`, you'd have to rewrite `self.name = name; self.salary = salary` inside `Manager` too — `super()` avoids that duplication.

### Why this matters beyond syntax

Inheritance models an **"is-a" relationship**: a `Manager` *is an* `Employee`, a `Dog` *is an* `Animal`. If the relationship is really "has-a" instead (a `Car` *has an* `Engine`, it isn't a kind of `Engine`), you want **composition** — storing an instance of one class as an attribute of another — not inheritance. Reaching for inheritance when composition fits better is a genuinely common design mistake interviewers probe for with "how would you design X" questions.

## 6. Dunder methods — customizing how your objects behave

"Dunder" = **d**ouble **under**score, like `__init__`. These let your objects work with Python's built-in syntax (`print()`, `==`, `len()`, `+`) instead of only ever calling explicit methods.

```python
class Transaction:
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

    def __repr__(self):
        return f"Transaction(category={self.category!r}, amount={self.amount})"

    def __eq__(self, other):
        return self.category == other.category and self.amount == other.amount

t1 = Transaction("food", 200)
t2 = Transaction("food", 200)

print(t1)             # Transaction(category='food', amount=200) — uses __repr__
t1 == t2               # True — uses YOUR __eq__, not identity
t1 is t2                # False — still different objects in memory
```

Without `__repr__`, printing an object gives you the same ugly `<__main__.Transaction object at 0x...>` you saw with `csv.DictReader` — now you know exactly why that happens, and how to fix it for your own classes.

Without `__eq__`, `==` falls back to identity comparison (same as `is`) — two `Transaction` objects with identical data would compare as *not equal*, because Python has no idea `category` and `amount` are what "equal" should mean for your class until you tell it.

### `__str__` vs `__repr__` — the actual difference, since it's a very common interview question

- `__repr__` — meant for **developers/debugging**. Should ideally look like valid Python code that could recreate the object. Used by `print()` as a fallback, and always used when you inspect a value directly in a REPL or show an object inside a list/dict.
- `__str__` — meant for **end users**. A readable, human-facing description. If you define both, `print(obj)` uses `__str__`; if you only define `__repr__`, `print(obj)` falls back to it.

```python
class Transaction:
    def __repr__(self):
        return f"Transaction('{self.category}', {self.amount})"

    def __str__(self):
        return f"{self.category}: ₹{self.amount}"

t = Transaction("food", 200)
print(t)          # food: ₹200          — uses __str__
print([t])         # [Transaction('food', 200)]   — a list of objects always shows __repr__, even if __str__ exists
```

That last line is the detail people miss: containers (lists, dicts) always show `__repr__` for their contents, never `__str__`, even outside of `print()`.

Other common dunders, briefly — you'll use these as you go rather than memorize them cold:

```python
def __len__(self): return len(self.items)        # lets len(obj) work
def __add__(self, other): return ...               # lets obj1 + obj2 work
def __lt__(self, other): return self.amount < other.amount   # lets obj1 < obj2 work, and sorted() use it
```

## 7. `@dataclass` — less boilerplate for data-holding classes

A huge fraction of classes you write are just "bags of related fields" — and writing `__init__`, `__repr__`, and `__eq__` by hand for every one gets repetitive fast. `@dataclass` (from the `dataclasses` module, stdlib) generates all of that for you:

```python
from dataclasses import dataclass

@dataclass
class Transaction:
    category: str
    amount: float
    is_recurring: bool = False       # default value, same rules as function defaults

t1 = Transaction("food", 200)
t2 = Transaction("food", 200)

print(t1)            # Transaction(category='food', amount=200, is_recurring=False)  — __repr__ for free
t1 == t2               # True  — __eq__ for free, compares all fields
```

Compare that to the hand-written version above — same behavior, far less code. The type annotations (`category: str`) aren't enforced at runtime (remember, Python doesn't enforce types), but they document intent and let tools like `mypy` (Topic 6, Advanced group) catch mistakes. Reach for `@dataclass` by default for simple data-holding classes; write a full manual class when you need custom behavior beyond just holding fields (validation in `__init__`, custom methods that do real logic, inheritance from a non-dataclass base).

---

## 8. Encapsulation — Python doesn't have "private," it has conventions

Java/C++ enforce `private`/`protected` at compile time. Python doesn't — everything is technically accessible from outside a class. Instead it uses **naming conventions** that signal intent:

```python
class Account:
    def __init__(self, balance):
        self.balance = balance          # public — free to use from anywhere
        self._internal_flag = True      # _single underscore — "internal, please don't touch" (convention only, nothing stops you)
        self.__secret = "abc"           # __double underscore — triggers name mangling
```

- `balance` — public, no signal at all.
- `_internal_flag` — a single leading underscore is a *convention*, not enforcement. It tells other developers (and your IDE) "this is an implementation detail, don't rely on it from outside," but Python does nothing to stop `acct._internal_flag` from working.
- `__secret` — a **double** leading underscore does something real: Python renames it internally to `_Account__secret` ("name mangling"). This exists to avoid accidental attribute clashes when subclassing, not for security.

```python
a = Account(100)
print(a._Account__secret)   # "abc" — still accessible, just not under the name you wrote
```

Name mangling is a real interview question ("why would `self.__x` inside a method not be accessible as `obj.__x`?") — now you know: it isn't hidden, it's renamed.

## 9. `@property` — computed and validated attributes

A `property` lets you write code that *looks* like plain attribute access (`account.balance`) but actually runs a method underneath — letting you validate on write, compute on read, or later change a stored attribute into a computed one without breaking any code that uses it.

```python
class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner
        self._balance = balance          # stored with a leading underscore — "the real value lives here"

    @property
    def balance(self):                    # the GETTER — called on `account.balance` (no parens!)
        return self._balance

    @balance.setter
    def balance(self, value):              # the SETTER — called on `account.balance = value`
        if value < 0:
            raise ValueError("balance cannot be negative")
        self._balance = value

a = BankAccount("Ani", 500)
print(a.balance)        # 500 — calls the getter, looks like plain attribute access
a.balance = 700          # calls the setter — validated
a.balance = -50           # raises ValueError — the setter caught it
```

This is exactly how you'd retroactively add validation to a class whose attributes were previously plain and unguarded, without forcing every caller to switch from `account.balance` to `account.get_balance()`. That backward-compatibility angle is the actual reason `@property` exists and is asked about.

## 10. `__eq__` and `__hash__` — a pairing that trips people up

By default, every object is hashable — Python hashes it based on its `id()`, so two different objects are never equal and never hash the same. The moment you define `__eq__` yourself, Python assumes you also want to redefine what "equal" means for hashing, and — since it can't safely guess how — it sets `__hash__` to `None` for you, making your instances **unhashable**.

```python
class Transaction:
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

    def __eq__(self, other):
        return self.category == other.category and self.amount == other.amount

t1 = Transaction("food", 200)
t2 = Transaction("food", 200)
t1 == t2                  # True

s = {t1, t2}               # TypeError: unhashable type: 'Transaction'
```

The rule that makes this necessary: **objects that are equal must have equal hashes** (a set/dict relies on this to know two "equal" items belong in the same bucket). Since your `__eq__` says `t1 == t2`, Python can't keep the default identity-based `__hash__` around — `id(t1) != id(t2)`, so their old hashes would differ, breaking sets and dicts silently. You have to explicitly opt back in:

```python
class Transaction:
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

    def __eq__(self, other):
        return self.category == other.category and self.amount == other.amount

    def __hash__(self):
        return hash((self.category, self.amount))    # hash of a tuple of the same fields __eq__ uses

s = {t1, t2}     # now works — one item, since t1 == t2
```

`@dataclass` handles this for you: by default `eq=True` (generates `__eq__`) but that also sets `__hash__` to `None`, same trap — unless you pass `frozen=True`, in which case the dataclass reasons "this object can't change after creation, so hashing it is safe" and generates a real `__hash__` automatically.

## 11. Multiple inheritance & MRO (Method Resolution Order)

Python allows a class to inherit from more than one parent:

```python
class A:
    def greet(self):
        return "A"

class B(A):
    def greet(self):
        return "B"

class C(A):
    def greet(self):
        return "C"

class D(B, C):
    pass

d = D()
print(d.greet())        # "B" — not "A", even though D doesn't define greet() itself
```

This is the classic **diamond problem** — `D` inherits from both `B` and `C`, which both inherit from `A`. When `D` doesn't define `greet()`, which parent's version does it use? Python answers this with the **MRO (Method Resolution Order)** — a fixed, predictable search order computed with an algorithm called **C3 linearization**. You can see it directly:

```python
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
```

Python searches left to right through that tuple and stops at the first class that defines the method — `D` doesn't have it, `B` does, so `B`'s wins. `super()` isn't "go to my direct parent" either — it means "go to the next class in the MRO," which matters once multiple inheritance is involved.

In practice: multiple inheritance is asked about constantly in interviews but used sparingly in real code, because deep diamond hierarchies get hard to reason about. When you do want to combine independent bits of behavior, **mixins** (§17 below) are the more common, more disciplined pattern.

## 12. Abstract Base Classes — enforcing "subclasses must implement this"

Inheritance alone can't force a subclass to override a method — `Cat(Animal)` from §5 was free to just not define `speak()` and silently inherit the parent's. Sometimes you want the opposite guarantee: "this method has no sensible default, every subclass MUST provide its own." That's what `abc` (Abstract Base Classes) is for:

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        ...                       # no implementation — subclasses are FORCED to provide one

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14159 * self.radius ** 2

s = Shape()          # TypeError: Can't instantiate abstract class Shape with abstract method area
c = Circle(5)          # fine — Circle implemented area()
```

If a subclass forgets to implement `area()`, instantiating *that* subclass also raises `TypeError` — Python checks at instantiation time, not just at definition time. This is how you build a real "contract" or "interface"-style guarantee in Python — relevant later when you look at how frameworks like Django and FastAPI define base classes you're expected to extend.

## 13. `__slots__` — trading flexibility for memory

By default, every instance carries its own `__dict__` to hold its attributes — flexible (you can add a new attribute to any instance at any time), but each instance's `__dict__` has real memory overhead. `__slots__` tells Python "this class will only ever have exactly these attributes," and Python allocates fixed slots instead of a dict:

```python
class Point:
    __slots__ = ("x", "y")     # ONLY these two attributes are allowed, ever

    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
p.z = 3          # AttributeError — z isn't in __slots__, and there's no __dict__ to fall back on
```

You'd reach for this only when memory actually matters — e.g. creating millions of small objects (rows in an ETL pipeline, for instance, which is directly relevant to work later in your plan). For everyday classes, don't bother — it's an optimization with real tradeoffs (no dynamic attributes, and it complicates multiple inheritance), not a default habit.

## 14. `__new__` vs `__init__` — creation vs initialization

`__init__` doesn't actually *create* the object — it initializes one that already exists. The actual creation happens in `__new__`, which runs first and returns the new (empty) instance; `__init__` then receives that instance as `self` and fills it in. You'll almost never override `__new__` — it's worth knowing it exists mainly because it explains *why* things like immutable-type subclassing or the singleton pattern work:

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)     # only ever create ONE actual instance
        return cls._instance

a = Singleton()
b = Singleton()
print(a is b)     # True — same object, __new__ handed back the existing one instead of making a new one
```

## 15. More operator overloading, and `functools.total_ordering`

You saw `__lt__` briefly in §6. Defining comparisons by hand for a class you want to be fully sortable/comparable (`<`, `<=`, `>`, `>=`) normally means writing four methods. `functools.total_ordering` fills in the rest from just two:

```python
from functools import total_ordering

@total_ordering
class Transaction:
    def __init__(self, amount):
        self.amount = amount

    def __eq__(self, other):
        return self.amount == other.amount

    def __lt__(self, other):
        return self.amount < other.amount

# total_ordering derives __le__, __gt__, __ge__ automatically from just __eq__ and __lt__
```

## 16. Duck typing vs formal interfaces

Python's usual philosophy is **duck typing**: "if it walks like a duck and quacks like a duck, treat it as a duck" — you don't check an object's type before using it, you just call the method you need, and if the object has it, it works. This is *why* Python doesn't force you to declare interfaces the way Java does:

```python
def process(item):
    return item.area()          # works on ANY object with an .area() method — no type check, no shared base class required
```

ABCs (§12) are Python's *formal*, opt-in version of an interface when you want the safety net enforced. `typing.Protocol` (you'll meet this properly in the type-hints doc later, Advanced group) is a newer middle ground — it lets you describe "any object with this shape" for static type checkers like `mypy`, without requiring actual inheritance. Know that Python supports all three levels — implicit duck typing, explicit ABCs, and structural `Protocol` typing — and picks looser guarantees by default, which is a real philosophical difference from Java/C# that interviewers sometimes probe with "how does Python handle interfaces?"

## 17. Mixins — small, single-purpose classes meant to be combined

A mixin is a class that's never meant to stand alone — it exists purely to be combined with other classes via multiple inheritance, adding one specific capability:

```python
class JSONExportMixin:
    def to_json(self):
        import json
        return json.dumps(self.__dict__)

class Transaction(JSONExportMixin):
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

t = Transaction("food", 200)
print(t.to_json())     # '{"category": "food", "amount": 200}'
```

`JSONExportMixin` on its own is useless — instantiating it does nothing meaningful. Its whole job is to be mixed into other classes to grant them `.to_json()` "for free." This is the disciplined, common alternative to the deep diamond hierarchies from §11 — instead of one class inheriting complex behavior from a tangled tree, you compose several small, focused mixins.

## 18. `@dataclass`, the rest of it

Three more pieces worth knowing:

```python
from dataclasses import dataclass, field

@dataclass
class Cart:
    items: list = field(default_factory=list)    # NOT items: list = [] — that would raise ValueError at class definition, because dataclass actively blocks the Topic 1 mutable-default-argument trap
    owner: str = "unknown"

    def __post_init__(self):                         # runs automatically right after the generated __init__
        if not self.owner:
            raise ValueError("owner cannot be empty")

@dataclass(frozen=True, order=True)                    # frozen = immutable (and hashable, see §10); order = generates __lt__/__le__/etc. by comparing fields in declared order
class Money:
    amount: float
    currency: str = "INR"
```

- `field(default_factory=list)` — the dataclass-safe way to give a mutable default; writing `items: list = []` directly raises `ValueError: mutable default <class 'list'> for field items is not allowed` — `@dataclass` catches the exact bug from Topic 1 for you, at class-definition time, instead of letting it silently corrupt shared state later.
- `__post_init__` — runs right after the auto-generated `__init__`, the place to put validation or derived fields that the field list alone can't express.
- `frozen=True` — makes instances immutable after creation (`m.amount = 5` raises `FrozenInstanceError`) and, as covered in §10, makes them safely hashable as a side effect.
- `order=True` — generates `__lt__`, `__le__`, `__gt__`, `__ge__` by comparing fields in the order they're declared, so instances become sortable for free.

---

## Practice questions — Part 1

1. **Build a `BankAccount` class** with `owner` (str) and `balance` (float, default `0`). Add methods `deposit(amount)` and `withdraw(amount)` — `withdraw` should raise a `ValueError` (Topic 1!) if the withdrawal would take the balance negative. Add a `__repr__` so printing an account looks like `BankAccount(owner='Ani', balance=500)`.

2. **Inheritance.** Create a `SavingsAccount(BankAccount)` that adds an `interest_rate` and a method `apply_interest()` that increases the balance by `balance * interest_rate`. Use `super().__init__()` — don't repeat the parent's field assignments.

3. **`__eq__` vs default equality.** Create two separate (non-dataclass) `Transaction` objects with identical `category` and `amount`, *without* writing `__eq__`. Confirm `t1 == t2` is `False`. Then add `__eq__` and confirm it becomes `True`. Explain in your own words, in one or two lines, *why* Python needs to be told what equality means for your own classes when it already knows for ints and strings.

4. **Rewrite as a dataclass.** Take your `BankAccount` from Q1 and rewrite it using `@dataclass` instead. You'll find `withdraw`'s validation logic doesn't fit neatly into a dataclass's auto-generated `__init__` — figure out how to still raise the `ValueError` on an invalid withdrawal (hint: the validation doesn't have to live in `__init__` at all; it can live in the `withdraw` method itself, same as before — `@dataclass` only replaces the boilerplate, not every method you write).

## Practice questions — Part 2 (the deep-dive additions)

5. **Property.** Take your `BankAccount` from Q1 and convert `balance` into a `@property` with a setter that raises `ValueError` on a direct negative assignment (`account.balance = -50`), separate from the validation already inside `withdraw`. In a line or two: why might you want both — the setter guard *and* `withdraw`'s own check?

6. **`__eq__` and `__hash__`.** Using your `Transaction` class from Q3 (the version with `__eq__` defined, no `__hash__`), try putting `t1` and `t2` into a `set` — confirm it raises `TypeError`. Then add a correct `__hash__` and confirm the set now works and collapses to one item. In one line: why does defining `__eq__` alone break hashing?

7. **MRO.** Build the diamond from §11 yourself — classes `A`, `B(A)`, `C(A)`, `D(B, C)`, each with its own `greet()` returning its own letter. Predict `D().greet()` and `D.__mro__` *before* running it, then verify.

8. **Abstract base class.** Define an abstract `Shape(ABC)` with an abstract `area()`. Create `Circle` and `Rectangle` subclasses that implement it. Confirm `Shape()` directly raises `TypeError`, and that a subclass which forgets to implement `area()` also raises `TypeError` on instantiation, not just a silent pass.

9. **Dataclass, done right.** Write a `Cart` dataclass with a mutable `items: list` field using `field(default_factory=list)` (not `= []`), and a `__post_init__` that raises `ValueError` if `owner` is an empty string. Show what happens if you try `items: list = []` directly instead.

---

*Same as always — write real code, paste it when done, I'll check it. This one's bigger, so take your time — Part 1 and Part 2 can be two separate sittings if you want, just tell me which you're submitting. Say "next" when you're fully through both parts and I'll build the doc for venvs & package management.*
