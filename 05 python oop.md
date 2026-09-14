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

### Running this for real, and proving `t.is_large()` really is `Transaction.is_large(t)` in disguise

**Real, verified output:**

```python
t = Transaction("food", 200)
print(t.category)
print(t.amount)
print(t.is_large())
print("Transaction.is_large(t):", Transaction.is_large(t))
```

```
food
200
False
Transaction.is_large(t): False
```

The last line is the important one — it proves §2's claim ahead of schedule: calling the method through the *class* and manually passing `t` as the first argument gives the exact same result as calling it through the *instance* (`t.is_large()`). That's not a coincidence; it's literally what `t.is_large()` does under the hood, which §2 explains in full.

**Flow diagram — what `class Transaction:` and `t = Transaction("food", 200)` actually build:**

```
class Transaction:            ← defines a BLUEPRINT, stored once, at module level
    def __init__(self, ...): ...
    def is_large(self): ...

    ┌─────────────────────────┐
    │  Transaction (the class) │
    │  - __init__              │
    │  - is_large               │
    └─────────────────────────┘

t = Transaction("food", 200)
    Step 1: Python creates a new, empty object
    Step 2: calls __init__(that_new_object, "food", 200)
            → self = that_new_object
            → self.category = "food"   (attaches data to THIS object)
            → self.amount = 200
    Step 3: the name "t" is bound to that now-filled-in object

    ┌─────────────────┐              ┌─────────────────────────┐
    │  t (an instance)  │   "is a"     │  Transaction (the class) │
    │  category: "food" │─────────────▶│  - __init__               │
    │  amount: 200       │             │  - is_large                │
    └─────────────────┘              └─────────────────────────┘
```

The instance (`t`) only ever stores its own *data* (`category`, `amount`); it does not carry its own private copy of the *methods* — `is_large` lives once on the class, and every instance shares that same method code, looking it up on the class when called. This distinction — data lives per-instance, behavior lives on the class and is shared — is the foundation for everything else in this doc, especially §3's instance-vs-class-attribute distinction.

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

### Running this for real, with proof `a` and `b` are genuinely separate objects

**Real, verified output:**

```python
a = Counter()
b = Counter()
a.increment()
a.increment()
print(a.count, b.count)
print("a is b:", a is b)
print("id(a):", id(a), "id(b):", id(b))
```

```
2 0
a is b: False
id(a): 139770289336912 id(b): 139770289339088
```

**Flow diagram — why `a.increment()` never touches `b.count`:**

```
a = Counter()                    b = Counter()
    __init__ runs with               __init__ runs SEPARATELY with
    self = a's new object            self = b's new object
    → a.count = 0                    → b.count = 0

    ┌──────────────┐                 ┌──────────────┐
    │  a: count=0   │                 │  b: count=0   │   ← two distinct
    └──────────────┘                 └──────────────┘      objects, distinct
                                                              memory addresses

a.increment()
    Python translates this to:  Counter.increment(a)
    → inside the method, self IS a (the exact object a points to)
    → self.count += 1  means  a.count += 1
    → b is never mentioned, never touched, anywhere in this call

    ┌──────────────┐                 ┌──────────────┐
    │  a: count=1   │                 │  b: count=0   │
    └──────────────┘                 └──────────────┘

a.increment()  (again)

    ┌──────────────┐                 ┌──────────────┐
    │  a: count=2   │                 │  b: count=0   │   ← matches the
    └──────────────┘                 └──────────────┘      printed "2 0"
```

The one sentence to internalize: **`self` is not a keyword or a special magic value — it's an ordinary parameter that happens to always receive "whichever object the method was called on," because Python fills it in automatically at the call site.** Nothing stops you from calling the unbound method form directly (`Counter.increment(a)`) and passing your own object explicitly — that's exactly what `a.increment()` compiles down to.

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

### Running the whole progression for real, and watching each instance's `__dict__` directly

**Real, verified output:**

```python
e1 = Employee("Ani")
e2 = Employee("Priya")
print(e1.company, e2.company)

Employee.company = "NewCo"
print(e1.company, e2.company)

e1.company = "JustMine"
print(e1.company, e2.company)
print(Employee.company)
print(e1.__dict__)
print(e2.__dict__)
```

```
CES CES
NewCo NewCo
JustMine NewCo
NewCo
{'name': 'Ani', 'company': 'JustMine'}
{'name': 'Priya'}
```

**Flow diagram — attribute lookup, and exactly why `e1.company` finds three different values across the three prints:**

```
When Python evaluates  e1.company , it looks in TWO places, in this
strict order, and stops at the first match:

    1. e1's OWN instance __dict__ (its personal attribute storage)
    2. if not found there, fall back to Employee's class __dict__

Print 1: e1.company, e2.company  ->  "CES CES"

    e1.__dict__ = {'name': 'Ani'}       — no "company" key here yet
    e2.__dict__ = {'name': 'Priya'}     — no "company" key here yet
    → both fall through to step 2, find Employee.company = "CES"
    → both report the SAME class-level value

Employee.company = "NewCo"    ← this changes the CLASS's own dict,
                                 not either instance's dict at all

Print 2: e1.company, e2.company  ->  "NewCo NewCo"

    Neither instance dict has "company" — both STILL fall through to
    the class, which now holds "NewCo" — both instances "see" the
    change together, because they were never storing their own copy,
    just repeatedly asking the shared class.

e1.company = "JustMine"   ← THIS is different: e1.company = ... is an
                             ASSIGNMENT through an instance, which ALWAYS
                             writes into that instance's OWN __dict__,
                             creating a new instance attribute — it does
                             NOT reach through to modify the class.

    e1.__dict__ is now {'name': 'Ani', 'company': 'JustMine'}
    e2.__dict__ is still {'name': 'Priya'}   ← untouched

Print 3: e1.company, e2.company  ->  "JustMine NewCo"

    e1.company: found DIRECTLY in e1's own __dict__ now -> "JustMine"
              (step 2 — the class fallback — is never even reached)
    e2.company: still nothing in e2's own dict -> falls through to
              the class -> "NewCo"
```

This is the real mechanism worth taking away: **reading an attribute checks the instance first, then falls back to the class; but writing an attribute through an instance (`e1.company = ...`) always creates or updates that instance's own copy, never the class's.** The only way to actually change the *shared* class attribute is `Employee.company = ...`, addressing the class directly — which is exactly what makes the mutable-class-attribute trap below so easy to fall into by accident.

### Running the mutable-class-attribute trap for real, with proof it's shared

**Real, verified output:**

```python
class Bad:
    items = []

    def add(self, item):
        self.items.append(item)

a, b = Bad(), Bad()
a.add("x")
print(b.items)
print("a.items is b.items:", a.items is b.items)
```

```
['x']
a.items is b.items: True
```

**Why this is a different trap from `e1.company = "JustMine"` above, even though both involve a class attribute — the critical distinction is *assignment* vs. *mutation*:**

```
self.items.append(item)     ← this is NOT the same shape as
                               self.company = "JustMine"

e1.company = "JustMine"    →  ASSIGNMENT — rebinds e1's own "company"
                               name to point at a new object. This
                               creates an INSTANCE attribute, shadowing
                               the class one, exactly as traced above.

self.items.append(item)    →  first, Python reads self.items — finds
                               NOTHING in the instance's own dict, so
                               it falls through to the class and finds
                               the ONE shared [] list. Then .append(item)
                               MUTATES that shared list object directly,
                               in place — no new instance attribute is
                               ever created, because there was never an
                               assignment to self.items at all, only a
                               method call on whatever self.items
                               resolved to.
```

This is exactly the same "shared box, multiple sticky notes, someone reaches in and mutates it" pattern from the mutable-default-argument bug in the fundamentals doc, and from `b = a; b.append(4)` in the collections doc — the only thing new here is *where* the shared reference comes from (a class attribute, looked up through the instance-then-class fallback chain, instead of a second variable name or a stored function default).

**Verifying the fix for real:**

```python
class Good:
    def __init__(self):
        self.items = []

g1, g2 = Good(), Good()
g1.items.append("x")
print(g2.items)
print("g1.items is g2.items:", g1.items is g2.items)
```

```
[]
g1.items is g2.items: False
```

Because `self.items = []` runs *inside* `__init__`, it executes fresh, once per instance, every time `Good()` is called — each instance gets **assigned** its own brand-new empty list at construction time, rather than all instances sharing one list defined once on the class body. `g1.items is g2.items` being `False` is the direct, measurable proof that the fix worked.

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

*(§19 at the end of this doc walks through this same distinction in much more depth — full worked examples of each kind alone, then combined, plus the decision rule for which to reach for.)*

### Running this for real

**Real, verified output** — note the doc's inline example never actually printed anything, so here's the same code run through `print()`, plus what `print(t)` looks like *without* a `__repr__` defined yet (a preview of exactly the problem §6 solves):

```python
t = Transaction.from_dict({"amount": 500})
print(t, t.amount, t.total_with_tax())
print(Transaction.is_valid_amount(-5))
print(Transaction.is_valid_amount(5))
print(type(t))
```

```
<__main__.Transaction object at 0x7fe71a12c090> 500 590.0
False
True
<class '__main__.Transaction'>
```

That first, ugly `<__main__.Transaction object at 0x7fe71a12c090>` is worth pausing on now, even though `__repr__` isn't formally covered until §6 — it's the exact "default printing is ugly" problem the doc references there, and you're seeing it happen live: with no `__repr__` defined, `print(t)` falls back to Python's built-in default representation, which just reports the class name and the object's raw memory address.

**Flow diagram — the mechanical difference in what gets passed automatically for each of the three call styles:**

```
t = Transaction.from_dict({"amount": 500})

    from_dict is decorated with @classmethod, so calling it through
    the CLASS automatically supplies the class itself as the first
    argument:
        Transaction.from_dict({"amount": 500})
                    │
                    └─► cls = Transaction,  data = {"amount": 500}

    Inside: return cls(data["amount"])
              = Transaction(500)     ← builds and returns a real instance

Transaction.is_valid_amount(-5)

    is_valid_amount is decorated with @staticmethod — calling it
    supplies NOTHING extra automatically, not even the class:
        Transaction.is_valid_amount(-5)
                    │
                    └─► amount = -5   (that's the ENTIRE argument list)

t.total_with_tax()

    total_with_tax is a plain instance method — calling it through an
    INSTANCE supplies that instance as self automatically:
        t.total_with_tax()
          │
          └─► self = t   (self.amount is t's own amount, 500)
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

### Running both examples for real

**Real, verified output:**

```
Rex barks
Whiskers makes a sound
Ani 90000 5
```

**Flow diagram — why `Cat("Whiskers").speak()` finds a method it never defined:**

```
class Animal:
    def speak(self): ...

class Cat(Animal):
    pass                     ← Cat's OWN method list is completely empty

c = Cat("Whiskers")
c.speak()

    Step 1: does Cat itself define "speak"?  NO — Cat's class body is
            just "pass", nothing was ever added to it.
    Step 2: Python walks UP the inheritance chain to Cat's parent,
            Animal — does Animal define "speak"?  YES.
    Step 3: run Animal's speak(), with self = c (the Cat instance)
            → f"{self.name} makes a sound"  →  "Whiskers makes a sound"

class Dog(Animal):
    def speak(self): ...     ← Dog DOES define its own "speak"

d = Dog("Rex")
d.speak()

    Step 1: does Dog itself define "speak"?  YES.
            → uses Dog's own version immediately, NEVER even looks
              at Animal's speak() at all — Dog's version fully
              REPLACES (overrides) the inherited one for Dog instances.
```

This attribute/method lookup walking up the chain is exactly the same mechanism as §3's instance-then-class fallback for attributes — just extended one more level, from "instance, then its class" to "instance, then its class, then that class's parent, then *its* parent," and so on, all the way up to `object` at the root. It's one single, consistent rule applied repeatedly, not a different rule for methods vs. attributes.

**Flow diagram — `super().__init__(name, salary)`, traced call by call:**

```
m = Manager("Ani", 90000, 5)

    Step 1: Python creates a new, empty Manager instance
    Step 2: calls Manager.__init__(that_instance, "Ani", 90000, 5)
              self = that_instance, name="Ani", salary=90000, team_size=5

    Step 3: inside Manager.__init__, the FIRST line is:
              super().__init__(name, salary)

            super() here resolves to "the next class up from Manager
            in its inheritance chain" — which is Employee. This calls
            Employee.__init__(self, "Ani", 90000) — note it's the SAME
            self (the Manager instance being built), just running the
            PARENT class's setup code against it.

              → self.name = "Ani"      (written onto the Manager instance)
              → self.salary = 90000    (written onto the Manager instance)

    Step 4: control returns to Manager.__init__, which continues with
            its own remaining line:
              self.team_size = 5       (written onto the SAME instance)

    End result: ONE Manager instance, with THREE attributes, two of
    which were set by borrowed code from Employee, one by Manager's
    own code — self was never swapped out, only the CODE being run
    against it changed.
```

The practical payoff, stated plainly: without `super().__init__(name, salary)`, `Manager.__init__` would have to duplicate `self.name = name` and `self.salary = salary` itself — and if `Employee.__init__` later grew a third field (say, `hire_date`), every subclass that had copy-pasted the old logic would silently miss it, while every subclass using `super()` would pick it up automatically, for free.

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

### Running this for real

**Real, verified output:**

```
Transaction(category='food', amount=200)
True
False
```

This matches §4's "preview" exactly — that ugly default `<__main__.Transaction object at 0x...>` you saw two sections ago is precisely what disappears once `__repr__` is defined, replaced with the readable string you write yourself.

**Flow diagram — how `print(t1)` and `t1 == t2` reach your custom methods, mechanically:**

```
print(t1)
    print() doesn't know anything about Transaction specifically —
    internally, it calls str(t1), which (with no __str__ defined,
    covered next) falls back to repr(t1), which calls YOUR
    __repr__(self) method, with self = t1.
    → returns "Transaction(category='food', amount=200)"
    → that's what print() displays

t1 == t2
    The == operator doesn't do identity comparison by default for
    YOUR classes once you've defined __eq__ — writing "t1 == t2" is
    sugar for calling t1.__eq__(t2), i.e. YOUR __eq__(self=t1, other=t2).
    → self.category == other.category  ->  "food" == "food"  ->  True
    → self.amount == other.amount      ->  200 == 200          ->  True
    → both True  ->  __eq__ returns True

t1 is t2
    is NEVER calls any dunder method at all — it only ever compares
    raw memory identity (id(t1) == id(t2)), completely bypassing
    whatever __eq__ you wrote. This is WHY t1 is t2 stays False even
    though t1 == t2 is True: they're two genuinely different objects
    in memory that your __eq__ has decided should be treated as
    equal in VALUE.
```

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

### Running the `__str__`/`__repr__` split for real

**Real, verified output:**

```
food: ₹200
[Transaction('food', 200)]
```

**Flow diagram — why `print(t)` and `print([t])` reach different dunder methods for the SAME object:**

```
t = Transaction(...)         ← one object, has BOTH __str__ and __repr__

print(t)
    print() converts its argument with str() — since Transaction
    defines __str__ directly, that's what gets called, no fallback
    needed.
    → __str__ runs  →  "food: ₹200"

print([t])
    The argument here isn't t — it's a LIST CONTAINING t: [t].
    print() calls str([t]) — but building the string representation
    of a LIST is the list's own job, not Transaction's, and Python's
    built-in list.__str__ has a fixed rule: represent every ELEMENT
    inside it using repr(), never str(), regardless of what the
    element's own __str__ does.
    → for the one element t, repr(t) runs  →  "Transaction('food', 200)"
    → wrapped in the list's own brackets   →  "[Transaction('food', 200)]"
```

The underlying reason containers always use `repr()` for their contents is consistency and unambiguity: a container needs a representation that, as much as possible, looks like valid Python and clearly delimits where one element ends and the next begins (imagine a list of strings printed with `str()` instead of `repr()` — you'd lose the quotes and be unable to tell where one string stopped and the next started). `__repr__`'s whole design goal — "look like code that could rebuild this object" — is exactly what makes it safe for that job; `__str__`'s goal — "look nice for a human reading output" — is not.

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

### Running this for real, and seeing exactly what got generated

**Real, verified output:**

```python
t1 = Transaction("food", 200)
t2 = Transaction("food", 200)
print(t1)
print(t1 == t2)
print(t1 is t2)
print(t1.__dict__)
```

```
Transaction(category='food', amount=200, is_recurring=False)
True
False
{'category': 'food', 'amount': 200, 'is_recurring': False}
```

**What `@dataclass` is actually doing, mechanically, at class-definition time — it's worth demystifying this rather than treating it as magic:** when Python processes `@dataclass` on top of the class, it reads the type-annotated lines (`category: str`, `amount: float`, `is_recurring: bool = False`) as a *field list*, and then — before your code ever runs — it generates and attaches real Python methods onto the class: an `__init__` that assigns each field from its matching constructor argument (equivalent to the `self.category = category` lines you'd write by hand), an `__eq__` that compares every field between two instances (equivalent to the `and`-chained comparison from §6), and a `__repr__` that formats every field name and value (equivalent to the f-string you'd write by hand). This is precisely why `t1.__dict__` above shows exactly the same shape you'd get from hand-writing `__init__` yourself — `@dataclass` isn't a different way of storing data, it's a code generator that writes the boilerplate you'd otherwise type out, at the moment the class is defined, once, not on every instantiation.

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

### Running this for real, and seeing name mangling directly in the instance's own `__dict__`

**Real, verified output:**

```python
a = Account(100)
print(a._Account__secret)
print(a.__dict__)
try:
    print(a.__secret)
except AttributeError as e:
    print("AttributeError:", e)
```

```
abc
{'balance': 100, '_internal_flag': True, '_Account__secret': 'abc'}
AttributeError: 'Account' object has no attribute '__secret'
```

**Flow diagram — exactly when the mangling happens, and why `a.__secret` genuinely fails:**

```
class Account:
    def __init__(self, balance):
        ...
        self.__secret = "abc"

The RENAMING happens at CLASS-DEFINITION time, by the Python compiler
itself, purely as a text-level transformation — any attribute name
written inside a class body starting with two leading underscores
(and NOT ending with two or more trailing underscores) is silently
rewritten to _ClassName__name, everywhere it's used inside that class:

    self.__secret = "abc"     becomes, effectively    self._Account__secret = "abc"

So by the time __init__ actually RUNS, there is no "__secret" attribute
ever created at all — only "_Account__secret" ever gets written into
a.__dict__, which is exactly what the printed dict above shows.

a.__secret   -> Python looks for an attribute literally named
                "__secret" in a's __dict__ (and the class chain) —
                but that name was never written anywhere; only the
                MANGLED name exists. Lookup fails -> AttributeError.

a._Account__secret  -> this IS the actual name that was stored ->
                found immediately -> "abc"
```

The stated purpose — "avoid accidental attribute clashes when subclassing" — is worth a concrete mental example: if a base class and a subclass both independently pick `self.__cache` for two *unrelated* purposes, without mangling they'd silently collide and overwrite each other's data. With mangling, the base class's version becomes `_Base__cache` and the subclass's becomes `_Sub__cache` — two different names, no collision — even though both pieces of code innocently wrote `self.__cache`.

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

### Running this for real, all three lines including the error

**Real, verified output:**

```python
a = BankAccount("Ani", 500)
print(a.balance)
a.balance = 700
print(a.balance)
try:
    a.balance = -50
except ValueError as e:
    print("ValueError:", e)
print(a.balance)
print(a.__dict__)
```

```
500
700
ValueError: balance cannot be negative
700
{'owner': 'Ani', '_balance': 700}
```

Notice `a.balance` is still `700` after the failed `-50` assignment, not some half-updated state — the setter raised *before* ever touching `self._balance`, so the attempted invalid write had zero effect. Also notice `a.__dict__` never contains a key literally called `"balance"` at all — only `"_balance"` — confirming that `balance` isn't a stored attribute in the usual sense, it's a computed pass-through.

**Flow diagram — what `@property` and `@balance.setter` actually attach to the class, and how `a.balance` (no parens) triggers a method call:**

```
@property
def balance(self):
    return self._balance

    This doesn't just define a normal method — @property wraps it in
    a special descriptor object and attaches it to the CLASS under the
    name "balance". A descriptor is an object that intercepts attribute
    access via its own __get__/__set__ machinery (the full mechanics
    are advanced and outside this doc's scope — what matters here is
    the observable behavior).

a.balance          ← NO parentheses — looks exactly like accessing a
                      plain stored attribute, e.g. a.owner

    Python sees "balance" is a property descriptor on the class (not
    a plain value), so instead of just returning a stored value, it
    calls the property's GETTER FUNCTION automatically:
        balance(self=a)  →  returns self._balance  →  500
    The caller never writes balance() — the () is invisible, hidden
    inside the property mechanism.

a.balance = 700     ← looks exactly like a plain attribute assignment

    Because "balance" is a property with a SETTER attached
    (@balance.setter), Python routes this assignment through the
    setter function instead of just overwriting a.__dict__["balance"]:
        balance(self=a, value=700)
            → 700 < 0? no → self._balance = 700   (THIS is a real,
              plain attribute write — to _balance, not balance)

a.balance = -50

        balance(self=a, value=-50)
            → -50 < 0? YES → raise ValueError(...)
            → self._balance is NEVER reached or modified
```

This is the concrete mechanism behind "letting you validate on write... without forcing every caller to switch" — from the *outside*, `a.balance = 700` looks identical whether `balance` is a plain attribute or a property; the validation logic is entirely invisible to callers except when it actually rejects a bad value, which is exactly the backward-compatibility property the doc calls out.

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

### Running both versions for real, including the failure and the fix

**Real, verified output:**

```python
t1 = Transaction("food", 200)
t2 = Transaction("food", 200)
print(t1 == t2)
try:
    s = {t1, t2}
except TypeError as e:
    print("TypeError:", e)
```

```
True
TypeError: unhashable type: 'Transaction'
```

And the fixed version, with `__hash__` defined:

```python
t1 = Transaction2("food", 200)
t2 = Transaction2("food", 200)
s = {t1, t2}
print(len(s))
print(hash(t1) == hash(t2))
```

```
1
True
```

**Flow diagram — why the set construction fails first, and why adding `__hash__` fixes it, tracing exactly what a `set` needs before it can even use `==`:**

```
s = {t1, t2}

    A set is built on a hash table (same underlying structure as
    dict, from the collections doc). To insert an item, Python's
    FIRST step, before anything else, is:
        bucket = hash(item) % (number of buckets)

    With __eq__ defined but no __hash__:
        Python set __hash__ = None on the class automatically (this
        is a deliberate safety measure — described below), so
        hash(t1) itself raises TypeError immediately, before the set
        even gets to the point of comparing t1 and t2 with ==.
        → TypeError: unhashable type: 'Transaction'

    With BOTH __eq__ AND __hash__ defined:
        hash(t1) = hash(("food", 200))    ← a real integer, works fine
        hash(t2) = hash(("food", 200))    ← SAME tuple contents ->
                                              SAME hash value
        Since hash(t1) == hash(t2), the set checks the SAME bucket for
        both — finds t1 already there when inserting t2, then falls
        back to == to confirm: t1 == t2 is True (your __eq__) -> t2
        is treated as "already present," not added again.
        → final set has length 1, not 2.
```

**Why Python sets `__hash__ = None` automatically the moment you define `__eq__`, rather than just leaving the old identity-based hash in place — this is the part that actually explains the "trips people up" framing:** if Python left the *old* `__hash__` (based on `id()`) in place while you overrode `__eq__` to compare by value, you'd get a genuinely broken, silently corrupting data structure: `t1` and `t2` would compare equal (`t1 == t2` → `True`) but hash *differently* (`hash(t1) != hash(t2)`, since they're different objects in memory) — meaning a set could store both `t1` and `t2` as if they were distinct (different hash buckets), while `t1 in {t2}` might report `False` even though `t1 == t2` is `True`, or vice versa depending on which bucket got checked. That violates the "equal objects must hash equal" rule sets and dicts depend on to function correctly at all, and would produce bugs that are extremely hard to track down (a set silently containing what looks like a "duplicate"). Rather than allow that, Python takes the conservative, safe route: the instant you customize `__eq__`, it disables hashing entirely (`__hash__ = None`) until *you* explicitly tell it, via your own `__hash__`, how the new equality rule should translate into a hash.

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

### Running this for real

**Real, verified output:**

```
B
(<class '__main__.D'>, <class '__main__.B'>, <class '__main__.C'>, <class '__main__.A'>, <class 'object'>)
```

Matches the doc's claim exactly.

**Flow diagram — the diamond shape itself, and the search order drawn as a line rather than a tree:**

```
        A
       ╱ ╲
      B   C
       ╲ ╱
        D

d.greet()   — D itself defines nothing, so Python walks the MRO tuple
              left to right and stops at the FIRST class that has a
              "greet" method:

    D.__mro__ = (D, B, C, A, object)
                 │  │
                 │  └─ B HAS a greet() → STOP HERE, use it → "B"
                 └─ D does not have greet() → keep going

              (C and A are never even checked, because the search
               already succeeded at B — this is exactly the same
               "stop at the first match" rule as §5's single-parent
               method lookup, just walking a longer, computed list
               instead of a straight line of ancestors.)
```

**Why the MRO puts `B` before `C`, specifically — this is the part that actually needs the C3-linearization algorithm, not just "search depth-first":** the short, practical version (full C3 linearization is genuinely subtle and not something you need to hand-compute in an interview) is that Python respects two things simultaneously: the order you wrote the parents in `class D(B, C):` — `B` was listed first, so it's preferred — and the constraint that a class must always appear *before* its own ancestors in the final order (`A` must come after both `B` and `C`, since both are `A`'s children). `(D, B, C, A, object)` is the one ordering that satisfies both rules at once. The practical takeaway for interviews: you don't need to hand-compute C3 from scratch, but you should be able to say confidently that **the parent listed first in the class definition is checked first**, and that `D.__mro__` will always tell you the real, authoritative order if you're ever unsure.

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

### Running all three cases for real — abstract class, valid subclass, and a subclass that forgot to implement

**Real, verified output:**

```python
try:
    s = Shape()
except TypeError as e:
    print("TypeError:", e)

c = Circle(5)
print(c.area())

class BrokenShape(Shape):
    pass

try:
    bs = BrokenShape()
except TypeError as e:
    print("TypeError:", e)
```

```
TypeError: Can't instantiate abstract class Shape with abstract method area
78.53975
TypeError: Can't instantiate abstract class BrokenShape with abstract method area
```

That third line is worth pointing at directly: `BrokenShape` never even mentions `area` — it just inherits from `Shape` and does nothing else (`pass`) — and instantiating it fails with the *exact same class of error* as trying to instantiate `Shape` directly. This confirms the doc's key claim precisely: the enforcement isn't "you can't instantiate `Shape` specifically," it's "you can't instantiate *anything*, anywhere in the hierarchy, that still has an unimplemented `@abstractmethod`."

**Flow diagram — how `ABC` + `@abstractmethod` enforce this, mechanically, at the moment of instantiation (not at class-definition time):**

```
class Shape(ABC):
    @abstractmethod
    def area(self): ...

    Inheriting from ABC opts a class into using a special metaclass
    (ABCMeta) that tracks which method names were marked
    @abstractmethod anywhere in the class's own body — here, "area".

class Circle(Shape):
    def area(self): ...      ← DOES override "area"

class BrokenShape(Shape):
    pass                      ← does NOT override "area"

Instantiation-time check, for ANY class in this hierarchy:

    Shape()
        → still has "area" listed as abstract, UNIMPLEMENTED
        → TypeError, refuses to create the object at all

    Circle(5)
        → Circle's own class body DOES define "area" — it's been
          "filled in," no longer counts as abstract for Circle
        → allowed to instantiate normally

    BrokenShape()
        → BrokenShape's class body is empty (`pass`) — it never
          overrode "area" — the abstract requirement inherited from
          Shape is STILL unfulfilled
        → TypeError, exactly like Shape() itself
```

The phrase "Python checks at instantiation time, not just at definition time" is the detail worth remembering cold for interviews: `class BrokenShape(Shape): pass` is perfectly legal to *define* — no error happens when Python reads that class body. The check only fires the moment someone actually tries to build an instance (`BrokenShape()`), which is what makes ABCs a genuine runtime safety net rather than just a documentation convention.

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

### Running this for real, including proof there's genuinely no `__dict__` at all

**Real, verified output:**

```python
p = Point(1, 2)
print(p.x, p.y)
try:
    p.z = 3
except AttributeError as e:
    print("AttributeError:", e)
try:
    print(p.__dict__)
except AttributeError as e:
    print("AttributeError (no __dict__):", e)
```

```
1 2
AttributeError: 'Point' object has no attribute 'z'
AttributeError (no __dict__): 'Point' object has no attribute '__dict__'
```

That last line is the deeper point the doc is making, made concrete: it's not that `__slots__` *blocks* new attributes as some kind of validation check on top of a normal instance — a `__slots__` instance genuinely **has no `__dict__` object at all** to begin with (confirmed directly: `p.__dict__` itself raises `AttributeError`, the same error category as any other missing attribute). Every other class you've written this whole doc has silently had a `__dict__` created for every instance automatically — that's *where* `e1.__dict__`, `a.__dict__`, `t1.__dict__` in every earlier section actually lived. `__slots__` is Python opting out of creating that dict at all, replacing it with a small number of fixed, pre-allocated storage slots — which is exactly where the memory savings come from: no per-instance dictionary object (with its own hash table overhead) needs to exist, just a fixed, small, C-level array sized exactly to the declared slots.

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

### Running this for real, with proof it's the literal same object

**Real, verified output:**

```python
a = Singleton()
b = Singleton()
print(a is b)
print(id(a), id(b))
```

```
True
139923154794576 139923154794576
```

**Flow diagram — why `Singleton()` called a second time doesn't build a second object, tracing the actual creation sequence for both calls:**

```
Normally, calling Cls(...) does TWO things in order:
    1. Cls.__new__(cls, ...)   → creates and returns a fresh, empty object
    2. Cls.__init__(obj, ...) → fills that object in (this is the part
                                  you've been overriding this entire doc)

a = Singleton()   (first call)
    __new__(cls=Singleton) runs:
        cls._instance is None?  YES (nothing built yet)
        → cls._instance = super().__new__(cls)   ← genuinely allocates
                                                     ONE new object here
        → return cls._instance   (this new object)
    Singleton has no custom __init__, so the default (does nothing
    extra) runs against it.
    a now points at this one real object.

b = Singleton()   (second call)
    __new__(cls=Singleton) runs AGAIN:
        cls._instance is None?  NO — it was set on the class itself
                                  during the FIRST call, and classes
                                  persist across calls
        → skip creating a new object entirely
        → return cls._instance   (the SAME object built the first time)
    b now points at that SAME existing object — no new allocation
    happened at all on this second call.
```

This is the concrete answer to "why override `__new__` instead of just controlling things in `__init__`": `__init__` always runs *after* an object already exists — it can fill in or validate an object's data, but it fundamentally cannot prevent a new object from being created in the first place, or hand back a *different, already-existing* object instead. `__new__` is the only hook that runs early enough to make that decision — which is exactly the trick the singleton pattern needs.

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

### Running this for real, proving all four comparisons actually work from just two hand-written methods

**Real, verified output:**

```python
t1 = Transaction(100)
t2 = Transaction(200)
print(t1 < t2)
print(t1 <= t2)
print(t1 > t2)
print(t1 >= t2)
print(t1 == t2)
print([t.amount for t in sorted([t2, t1])])
```

```
True
True
False
False
False
[100, 200]
```

Only `__eq__` and `__lt__` were written by hand — `<=`, `>`, and `>=` all produced correct answers anyway, and `sorted()` (which relies on `<` internally) worked too, with zero extra code.

**Flow diagram — how `functools.total_ordering` derives the missing three comparisons purely from logic, without ever touching `self.amount` directly:**

```
Given ONLY __eq__ (a == b) and __lt__ (a < b), every other ordering
comparison can be expressed in terms of just those two, using pure
boolean logic — no knowledge of WHAT is being compared is needed:

    a <= b   is exactly   (a < b) or (a == b)
    a >  b   is exactly   not (a < b) and not (a == b)     [equivalently: b < a]
    a >= b   is exactly   not (a < b)                       [equivalently: not(a<b)]

@total_ordering reads this off the class at decoration time (it sees
__eq__ and __lt__ are both present) and ATTACHES new __le__, __gt__,
__ge__ methods to the class that implement exactly this logic,
calling your __eq__/__lt__ internally rather than reimplementing
comparison from scratch.
```

This is why it works for *any* class, regardless of what it's comparing — `total_ordering` never looks at `self.amount` at all; it only ever calls the two methods you provided and combines their `True`/`False` results with boolean logic. That's also exactly why you still need to provide a correct, meaningful `__eq__` and `__lt__` yourself — `total_ordering` can't invent what "equal" or "less than" should mean for your class, it can only mechanically fill in the rest once you've defined those two building blocks.

## 16. Duck typing vs formal interfaces

Python's usual philosophy is **duck typing**: "if it walks like a duck and quacks like a duck, treat it as a duck" — you don't check an object's type before using it, you just call the method you need, and if the object has it, it works. This is *why* Python doesn't force you to declare interfaces the way Java does:

```python
def process(item):
    return item.area()          # works on ANY object with an .area() method — no type check, no shared base class required
```

ABCs (§12) are Python's *formal*, opt-in version of an interface when you want the safety net enforced. `typing.Protocol` (you'll meet this properly in the type-hints doc later, Advanced group) is a newer middle ground — it lets you describe "any object with this shape" for static type checkers like `mypy`, without requiring actual inheritance. Know that Python supports all three levels — implicit duck typing, explicit ABCs, and structural `Protocol` typing — and picks looser guarantees by default, which is a real philosophical difference from Java/C# that interviewers sometimes probe with "how does Python handle interfaces?"

### Running this for real, with two totally unrelated classes that both "happen" to have `.area()`, plus the failure case

**Real, verified output:**

```python
class Circle:
    def __init__(self, r):
        self.r = r
    def area(self):
        return 3.14159 * self.r ** 2

class Square:
    def __init__(self, side):
        self.side = side
    def area(self):
        return self.side ** 2

def process(item):
    return item.area()

print(process(Circle(2)))
print(process(Square(3)))

class NoArea:
    pass

try:
    process(NoArea())
except AttributeError as e:
    print("AttributeError:", e)
```

```
12.56636
9
AttributeError: 'NoArea' object has no attribute 'area'
```

**Why this "just works" without `Circle` and `Square` sharing any common base class — traced against what `process()` actually does:**

```
process(item)   simply executes:   item.area()

    It never asks "is item a Circle? a Square? does item inherit
    from some Shape base class?" — none of that. It just tries to
    look up an attribute called "area" on whatever object was
    passed in, and call it.

    process(Circle(2))   → Circle instance has .area()  → runs it → 12.56636
    process(Square(3))   → Square instance ALSO has .area() (a
                             COMPLETELY unrelated class, no shared
                             ancestor except object) → runs it → 9
    process(NoArea())    → NoArea instance has NO .area() at all →
                             the attribute lookup itself fails →
                             AttributeError, the same kind of error
                             you'd get from any missing attribute
```

This is the literal mechanism behind "if it walks like a duck": `process()` places zero requirements on *what kind* of object it receives, only on *what that object can do* when asked — and Python only discovers whether that's true at the exact moment `.area()` is actually called, not before. Contrast this with §12's `ABC` approach, which raises `TypeError` proactively, *before* any method is even called, the instant you try to instantiate a class that hasn't fulfilled the contract — duck typing defers that check as late as possible (and only for the specific method actually used), while ABCs enforce it as early as possible (at instantiation, for every abstract method, whether or not it ends up being called). That's the real, practical difference between "loose by default" and "opt-in strict," not just a vocabulary distinction.

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

### Running this for real

**Real, verified output:**

```python
t = Transaction("food", 200)
print(t.to_json())
print(Transaction.__mro__)
```

```
{"category": "food", "amount": 200}
(<class '__main__.Transaction'>, <class '__main__.JSONExportMixin'>, <class 'object'>)
```

**Flow diagram — how `to_json()` finds `self.__dict__` when it's defined on a completely different, generic class:**

```
class JSONExportMixin:
    def to_json(self):
        return json.dumps(self.__dict__)     ← "self" here is WHATEVER
                                                 object this method
                                                 eventually gets called
                                                 on — JSONExportMixin
                                                 has no idea in advance
                                                 what fields self will
                                                 actually have

class Transaction(JSONExportMixin):
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

t = Transaction("food", 200)
t.to_json()

    Step 1: Python looks for "to_json" starting on Transaction itself
            → not found there
    Step 2: walks up the MRO (same lookup mechanism as §5, §11) →
            finds it on JSONExportMixin
    Step 3: calls JSONExportMixin.to_json(self=t)
            → inside: self.__dict__  →  t's OWN dict, which is
              {"category": "food", "amount": 200} — the mixin
              never hardcoded these field names anywhere; it just
              asks whatever self turns out to be for its dict
    → json.dumps(...) serializes that dict to a JSON string
```

The reason this mixin is genuinely reusable across *any* class, without modification, is exactly that it never references any Transaction-specific field name — it only uses `self.__dict__`, which every plain Python object has (§13's `__slots__` classes being the deliberate exception). Mix it into a completely different class with completely different fields and `.to_json()` would still work, unmodified — which is the entire point of a mixin: one small, generic capability, safely combinable with many unrelated classes.

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

### Running every one of these claims for real

**Real, verified output** — `field(default_factory=list)` producing independent lists per instance, `__post_init__` firing on invalid input, the `items: list = []` form actually raising the documented `ValueError`, and `frozen=True`/`order=True` both behaving as claimed:

```python
c1 = Cart(owner="Ani")
c1.items.append("apple")
c2 = Cart(owner="Priya")
print(c1.items, c2.items)
print(c1.items is c2.items)

try:
    Cart(owner="")
except ValueError as e:
    print("ValueError:", e)

# equivalent to writing "items: list = []" directly in a @dataclass:
try:
    exec("""
from dataclasses import dataclass
@dataclass
class BadCart:
    items: list = []
""")
except ValueError as e:
    print("ValueError (mutable default):", e)

m1 = Money(100)
m2 = Money(200)
print(m1 < m2)
try:
    m1.amount = 5
except Exception as e:
    print(f"{type(e).__name__}:", e)
print(hash(m1))
```

```
['apple'] []
False
ValueError: owner cannot be empty
ValueError (mutable default): mutable default <class 'list'> for field items is not allowed: use default_factory
True
FrozenInstanceError: cannot assign to field 'amount'
1945999141625537588
```

Every claim checks out exactly as written. `c1.items is c2.items` being `False` confirms `field(default_factory=list)` behaves like `__init__`'s `self.items = []` from Topic 1's fix, not like a shared class-level default — each `Cart()` call invokes the factory (`list`) fresh, once, producing a brand-new, independent list per instance. `hash(m1)` succeeding at all (rather than raising, the way an unhashable normal-`__eq__` class from §10 would) is the direct payoff of `frozen=True` promising the object can never change after construction — exactly the reasoning the doc describes.

**Flow diagram — the actual sequence of events that produces the `ValueError: owner cannot be empty`:**

```
Cart(owner="")

    Step 1: the auto-generated __init__ runs first
            → self.items = list()   (calls the default_factory)
            → self.owner = ""
    Step 2: IMMEDIATELY after __init__ finishes, @dataclass
            automatically calls self.__post_init__() if you defined
            one — you don't call it yourself, it's wired in for you
    Step 3: __post_init__ runs:
              if not self.owner:      ← "" is falsy (empty string,
                                          from the fundamentals doc's
                                          truthiness rules!)
                  raise ValueError("owner cannot be empty")
```

This is a nice, concrete tie-back to the very first topic doc's truthiness rules — `not self.owner` relies on the exact same "empty string is falsy" fact from `01 python fundamentals.md` §4, now doing real validation work in a dataclass.

---

## 19. Instance methods vs `@classmethod` vs `@staticmethod` — worked through in depth

This expands on §4 above. Every method defined inside a class automatically receives something as its first argument — that's the entire distinction between the three:

- instance method → `self`, the specific object it was called on
- `@classmethod` → `cls`, the class itself
- `@staticmethod` → neither — it's a plain function that just happens to live inside the class body

**Instance method only — needs `self`, because it needs THIS object's own data:**

```python
class Pizza:
    def __init__(self, toppings, size):
        self.toppings = toppings
        self.size = size

    def price(self):                      # instance method — takes self
        base = {"small": 150, "medium": 250, "large": 350}[self.size]
        return base + len(self.toppings) * 30

p1 = Pizza(["cheese", "mushroom"], "medium")
p2 = Pizza(["cheese"], "small")
print(p1.price())   # 310
print(p2.price())   # 180
```

`price()` gives a different answer for `p1` vs `p2` because it reads `self.toppings` and `self.size` — data that belongs to that specific pizza. That's the defining trait of an instance method: it can't be answered without knowing which object you're asking about. This is what you'll write most of the time.

### Running this for real — confirmed exactly as commented

**Real, verified output:**

```
310
180
```

`p1`: base for `"medium"` is `250`, plus `2` toppings × `30` = `60`, totals `310`. `p2`: base for `"small"` is `150`, plus `1` topping × `30` = `30`, totals `180`. Both match the doc's inline comments exactly.

**`@classmethod` only — needs `cls`, because it works with the class, not one object:**

```python
class Pizza:
    def __init__(self, toppings, size):
        self.toppings = toppings
        self.size = size

    def __repr__(self):
        return f"Pizza({self.toppings}, '{self.size}')"

    @classmethod
    def margherita(cls, size="medium"):        # classmethod — takes cls, not self
        return cls(["cheese", "tomato"], size)   # cls(...) means "call whichever class this was invoked on"

p1 = Pizza.margherita()          # called on the CLASS, not an instance — no pizza exists yet, that's the point
print(p1)                          # Pizza(['cheese', 'tomato'], 'medium')
```

This pattern is an **alternate constructor** — instead of forcing every caller to remember `Pizza(["cheese", "tomato"], "medium")`, you give them a named, self-documenting way to build the common case. `cls` matters specifically because of inheritance:

```python
class StuffedCrustPizza(Pizza):
    pass

s = StuffedCrustPizza.margherita()
print(type(s))    # <class 'StuffedCrustPizza'> — NOT Pizza!
```

Because `margherita` uses `cls(...)` instead of hardcoding `Pizza(...)`, calling it via a subclass correctly returns an instance of *that subclass*. Hardcoding the class name would silently break the moment someone subclassed `Pizza` — this is the real reason `classmethod` exists instead of just writing a plain function.

### Running both the base-class and subclass calls for real, with proof `cls` genuinely resolves differently each time

**Real, verified output:**

```python
p1 = Pizza.margherita()
print(p1)

class StuffedCrustPizza(Pizza):
    pass

s = StuffedCrustPizza.margherita()
print(type(s))
print(s)
```

```
Pizza(['cheese', 'tomato'], 'medium')
<class '__main__.StuffedCrustPizza'>
Pizza(['cheese', 'tomato'], 'medium')
```

(That last `print(s)` shows `Pizza(...)`-formatted text purely because `StuffedCrustPizza` inherited `__repr__` from `Pizza` unchanged and never overrode it — `type(s)` above is the reliable way to see it's genuinely a `StuffedCrustPizza` instance underneath, not a mislabeled `Pizza`.)

**Flow diagram — why `cls` resolves to a *different* class depending on how `margherita` was called, even though it's the exact same method body running both times:**

```
@classmethod
def margherita(cls, size="medium"):
    return cls(["cheese", "tomato"], size)

Pizza.margherita()

    Called THROUGH the Pizza class directly → Python automatically
    supplies cls = Pizza
    → return cls(...)  means  return Pizza(["cheese","tomato"],"medium")
    → builds and returns a Pizza instance

StuffedCrustPizza.margherita()

    margherita is NOT redefined on StuffedCrustPizza — Python finds
    it by walking up the MRO to Pizza (same lookup mechanism as §5,
    §11, §17), but CRITICALLY: it still records that the call was
    made THROUGH StuffedCrustPizza, and supplies cls = StuffedCrustPizza,
    NOT cls = Pizza, even though the METHOD CODE itself is physically
    defined on Pizza.
    → return cls(...)  means  return StuffedCrustPizza(["cheese","tomato"],"medium")
    → builds and returns a StuffedCrustPizza instance — a DIFFERENT
      class than what running the exact same line of code produced
      one call earlier
```

This is the single concrete reason `@classmethod` exists as a distinct tool rather than just writing `margherita` as a `@staticmethod` that hardcodes `return Pizza(...)`: a hardcoded version would return a `Pizza` *every single time*, regardless of which class it was invoked through — silently wrong the moment anyone subclasses `Pizza` and expects `StuffedCrustPizza.margherita()` to actually build a `StuffedCrustPizza`.

**`@staticmethod` only — needs neither, it's just grouped here for organization:**

```python
class Pizza:
    VALID_SIZES = {"small", "medium", "large"}

    @staticmethod
    def is_valid_size(size):              # no self, no cls — just a plain function
        return size in Pizza.VALID_SIZES

print(Pizza.is_valid_size("medium"))   # True
print(Pizza.is_valid_size("jumbo"))     # False
```

`is_valid_size` doesn't need a specific pizza (`self`), and it doesn't need to know its class dynamically (`cls`) either — it's a pure utility check. It would behave identically as a standalone function sitting outside the class; the only reason to nest it as `@staticmethod` is namespacing — `Pizza.is_valid_size(...)` signals "this belongs with `Pizza`" instead of leaving a loose function floating in the module that someone might not connect back to it.

### Running this for real

**Real, verified output:**

```
True
False
```

Matches exactly.

**All three together, doing real work in one class:**

```python
class Pizza:
    VALID_SIZES = {"small": 150, "medium": 250, "large": 350}   # size -> base price

    def __init__(self, toppings, size):
        if not Pizza.is_valid_size(size):
            raise ValueError(f"invalid size: {size}")
        self.toppings = toppings
        self.size = size

    def __repr__(self):
        return f"Pizza({self.toppings}, '{self.size}')"

    def price(self):                                     # instance method — needs THIS pizza's own data
        base = Pizza.VALID_SIZES[self.size]
        return base + len(self.toppings) * 30

    @classmethod
    def margherita(cls, size="medium"):                    # classmethod — alternate constructor, stays correct under subclassing
        return cls(["cheese", "tomato"], size)

    @staticmethod
    def is_valid_size(size):                                # staticmethod — utility, needs neither self nor cls
        return size in Pizza.VALID_SIZES


p = Pizza.margherita("large")          # classmethod builds it
print(p)                                  # Pizza(['cheese', 'tomato'], 'large')
print(p.price())                          # instance method: 350 + 30 = 380
print(Pizza.is_valid_size("small"))     # staticmethod: True

bad = Pizza(["cheese"], "jumbo")        # __init__ calls the staticmethod internally -> ValueError: invalid size: jumbo
```

`__init__` calling `Pizza.is_valid_size(size)` shows a static method being used *internally* by an instance method — that's completely normal. The three categories describe what a method *needs*, not who's allowed to call it.

### Running the combined class for real — and a genuine discrepancy worth flagging

**Real, verified output:**

```python
p = Pizza.margherita("large")
print(p)
print(p.price())
print(Pizza.is_valid_size("small"))

try:
    bad = Pizza(["cheese"], "jumbo")
except ValueError as e:
    print("ValueError:", e)
```

```
Pizza(['cheese', 'tomato'], 'large')
410
True
ValueError: invalid size: jumbo
```

**A discrepancy worth calling out honestly, since the whole point of this verification pass is catching exactly this kind of thing:** the inline comment on `print(p.price())` above (left completely untouched, as originally written) says `# instance method: 350 + 30 = 380` — but the actual, verified output is `410`, not `380`. Tracing why: `margherita("large")` builds `cls(["cheese", "tomato"], "large")` — note that's **two** toppings, `"cheese"` and `"tomato"`, not one. `price()` computes `base + len(self.toppings) * 30` → `350 + len(["cheese", "tomato"]) * 30` → `350 + 2 * 30` → `350 + 60` → `410`. The original comment's arithmetic (`350 + 30 = 380`) only holds if there were exactly *one* topping, but `margherita` always builds a two-topping pizza (`["cheese", "tomato"]`) — so `380` was simply a small arithmetic slip in the original comment, and `410` is the genuinely correct, actually-running value. This is left exactly as it originally appeared above (per the rule that nothing existing gets altered), with this note added alongside it — exactly the kind of thing "verify by actually running it" catches that reasoning alone can miss.

**The decision rule, distilled for interviews:**

Does the method need one specific object's own data (`self.something`)? → **instance method** — your default; reach for it unless you have a specific reason not to.

Does the method need to build an instance a different way, or touch class-level (shared) data, in a way that should stay correct under subclassing? → **`@classmethod`**.

Does the method conceptually belong with the class but touches neither instance nor class state — a pure helper grouped here just for organization? → **`@staticmethod`**.

Interview one-liner: *"instance methods operate on an object, classmethods operate on the class itself — usually as alternate constructors — and staticmethods operate on neither, they're just namespaced utility functions."*

---

## Practice questions

1. **Build a `BankAccount` class** with `owner` (str) and `balance` (float, default `0`). Add methods `deposit(amount)` and `withdraw(amount)` — `withdraw` should raise a `ValueError` (Topic 1!) if the withdrawal would take the balance negative. Add a `__repr__` so printing an account looks like `BankAccount(owner='Ani', balance=500)`.

2. **Inheritance.** Create a `SavingsAccount(BankAccount)` that adds an `interest_rate` and a method `apply_interest()` that increases the balance by `balance * interest_rate`. Use `super().__init__()` — don't repeat the parent's field assignments.

3. **`__eq__` vs default equality.** Create two separate (non-dataclass) `Transaction` objects with identical `category` and `amount`, *without* writing `__eq__`. Confirm `t1 == t2` is `False`. Then add `__eq__` and confirm it becomes `True`. Explain in your own words, in one or two lines, *why* Python needs to be told what equality means for your own classes when it already knows for ints and strings.

4. **Rewrite as a dataclass.** Take your `BankAccount` from Q1 and rewrite it using `@dataclass` instead. You'll find `withdraw`'s validation logic doesn't fit neatly into a dataclass's auto-generated `__init__` — figure out how to still raise the `ValueError` on an invalid withdrawal (hint: the validation doesn't have to live in `__init__` at all; it can live in the `withdraw` method itself, same as before — `@dataclass` only replaces the boilerplate, not every method you write).

5. **Property.** Take your `BankAccount` from Q1 and convert `balance` into a `@property` with a setter that raises `ValueError` on a direct negative assignment (`account.balance = -50`), separate from the validation already inside `withdraw`. In a line or two: why might you want both — the setter guard *and* `withdraw`'s own check?

6. **`__eq__` and `__hash__`.** Using your `Transaction` class from Q3 (the version with `__eq__` defined, no `__hash__`), try putting `t1` and `t2` into a `set` — confirm it raises `TypeError`. Then add a correct `__hash__` and confirm the set now works and collapses to one item. In one line: why does defining `__eq__` alone break hashing?

7. **MRO.** Build the diamond from §11 yourself — classes `A`, `B(A)`, `C(A)`, `D(B, C)`, each with its own `greet()` returning its own letter. Predict `D().greet()` and `D.__mro__` *before* running it, then verify.

8. **Abstract base class.** Define an abstract `Shape(ABC)` with an abstract `area()`. Create `Circle` and `Rectangle` subclasses that implement it. Confirm `Shape()` directly raises `TypeError`, and that a subclass which forgets to implement `area()` also raises `TypeError` on instantiation, not just a silent pass.

9. **Dataclass, done right.** Write a `Cart` dataclass with a mutable `items: list` field using `field(default_factory=list)` (not `= []`), and a `__post_init__` that raises `ValueError` if `owner` is an empty string. Show what happens if you try `items: list = []` directly instead.

10. **Instance vs classmethod vs staticmethod, combined.** Take your `BankAccount` from Q1. Add a `@classmethod` `from_deposit_only(cls, owner, initial_deposit)` — an alternate constructor that starts the account at balance `0` and immediately deposits `initial_deposit`. Add a `@staticmethod` `is_valid_owner_name(name)` that returns `False` for an empty string and `True` otherwise, and have `__init__` call it internally to validate `owner`. Then create a `SavingsAccount(BankAccount)` subclass and call `SavingsAccount.from_deposit_only(...)` — confirm with `type()` that you get back a `SavingsAccount`, not a `BankAccount`.

11. **Explain in your own words**, in 2-3 lines: why does `cls(...)` inside a classmethod behave differently from hardcoding the class name directly, once subclasses are involved?

---

*Same as always — write real code, paste it when done, I'll check it. This one's bigger, so take your time — feel free to split it across a couple of sittings, just tell me which questions you're submitting. Say "next" when you're fully through and I'll build the doc for venvs & package management.*
