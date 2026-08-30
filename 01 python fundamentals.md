# Topic 1 — Python Fundamentals: Syntax, Types, Control Flow & Functions

*Phase 1, Beginner group — item 1 of 4. Read this end to end, type out the examples yourself (don't just read them), then attempt the practice questions at the bottom before checking anything off in the tracker.*

---

## 1. How Python actually runs

Python is interpreted and dynamically typed. There's no compile step you manage yourself — `python file.py` reads your file top to bottom and executes it. Dynamically typed means a variable's type isn't declared; it's just whatever value is currently bound to that name.

```python
x = 5        # x is an int right now
x = "hello"  # now x is a str — no error, no declaration needed
```

This is different from statically typed languages (Java, C++), where `int x = 5;` locks `x` to `int` forever. It's also *why* type hints (covered in the Advanced doc later this phase) exist — they're optional documentation for humans and tools, not enforced by the interpreter at runtime.

## 2. Variables & naming

Python uses `snake_case` for variables and functions, `PascalCase` for classes (you'll see this in the OOP doc). A variable is really just a name bound to an object in memory — assignment doesn't copy the value, it points the name at an object.

```python
a = [1, 2, 3]
b = a        # b points at the SAME list, not a copy
b.append(4)
print(a)     # [1, 2, 3, 4] — a changed too
```

This matters constantly once you get to functions and mutable default arguments (see §9). Hold onto it.

## 3. Core data types

| Type | Example | Mutable? | Notes |
|---|---|---|---|
| `int` | `42` | No | Arbitrary precision — Python ints don't overflow |
| `float` | `3.14` | No | IEEE 754 double — has precision quirks (§9) |
| `str` | `"hi"` | No | Immutable — every "modification" makes a new string |
| `bool` | `True` / `False` | No | Actually a subclass of `int` — `True == 1` |
| `NoneType` | `None` | No | Python's "no value" — not `0`, not `""`, not `False` |
| `list` | `[1, 2]` | **Yes** | Ordered, mutable |
| `tuple` | `(1, 2)` | No | Ordered, immutable — covered in doc 2 |
| `dict` | `{"a": 1}` | **Yes** | Key-value pairs — covered in doc 2 |
| `set` | `{1, 2}` | **Yes** | Unordered, unique — covered in doc 2 |

Check any value's type with `type(x)`, and check *category* membership with `isinstance(x, int)` — prefer `isinstance` in real code since it also handles subclasses correctly (relevant once you hit inheritance).

## 4. Type conversion & truthiness

```python
int("42")      # 42
str(42)        # "42"
float("3.14")  # 3.14
bool(0)        # False
bool("")       # False
bool([])       # False
bool(None)     # False
bool("False")  # True — a non-empty string is truthy, REGARDLESS of its content
```

That last line trips people up constantly. `bool()` doesn't parse meaning, it checks emptiness/zeroness. Falsy values in Python: `0`, `0.0`, `""`, `[]`, `{}`, `()`, `set()`, `None`, `False`. Everything else is truthy.

## 5. Operators

**Arithmetic:** `+ - * / // % **`
- `/` always returns a `float` (even `4 / 2` → `2.0`)
- `//` is floor division — `7 // 2` → `3`
- `%` is modulo — `7 % 2` → `1`
- `**` is exponent — `2 ** 10` → `1024`

**Comparison:** `== != < > <= >=` — compare *values*.

**Identity:** `is` / `is not` — compare *object identity* (same object in memory), not value.

```python
a = [1, 2, 3]
b = [1, 2, 3]
a == b   # True — same values
a is b   # False — different objects in memory
a is a   # True
```

This is a very common interview question. Small integers (-5 to 256) and short strings are cached by CPython, so `x = 5; y = 5; x is y` can be `True` — but never rely on that; always use `==` for value comparison and reserve `is` for checking against `None` (`x is None`, not `x == None`).

**Logical:** `and`, `or`, `not` — and they short-circuit:

```python
def expensive():
    print("called!")
    return True

False and expensive()   # "called!" never prints — and stops at the first falsy value
True or expensive()     # "called!" never prints — or stops at the first truthy value
```

**Membership:** `in`, `not in` — works on strings, lists, dicts (checks keys), sets, tuples.

## 6. Control flow

```python
if condition:
    ...
elif other_condition:
    ...
else:
    ...
```

No parentheses required, no braces — indentation *is* the block. Mixing tabs and spaces is a real syntax error, not a style nit; configure your editor to insert spaces.

Ternary (conditional expression):

```python
status = "adult" if age >= 18 else "minor"
```

## 7. Loops

```python
for item in [1, 2, 3]:
    print(item)

for i in range(5):        # 0,1,2,3,4
    print(i)

for i, item in enumerate(["a", "b"]):   # (0, "a"), (1, "b")
    print(i, item)

for a, b in zip([1, 2], ["x", "y"]):    # pairs them up: (1,"x"), (2,"y")
    print(a, b)

i = 0
while i < 5:
    i += 1
```

`break` exits the loop entirely; `continue` skips to the next iteration. Less common but does get asked: loops have an `else` clause that runs only if the loop completed *without* hitting `break` — useful for "search and not found" patterns:

```python
for item in items:
    if item == target:
        print("found")
        break
else:
    print("not found")
```

## 8. Functions

```python
def greet(name, greeting="Hello"):   # "greeting" has a default value
    """Return a greeting string for name."""   # docstring
    return f"{greeting}, {name}!"

greet("Ani")                    # positional — "Hello, Ani!"
greet("Ani", greeting="Hi")     # keyword — "Hi, Ani!"
greet(name="Ani", greeting="Hi") # both as keyword — fine, order doesn't matter then
```

A function with no explicit `return` returns `None`. Always write a one-line docstring for anything non-trivial — it's cheap and interviewers notice its absence.

### Scope (the LEGB rule)

Python resolves a name by looking in this order: **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in.

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)       # "local" — found immediately, search stops
    inner()
    print(x)           # "enclosing"

outer()
print(x)                # "global"
```

To *modify* a variable from an outer scope instead of shadowing it, you need `global` or `nonlocal`:

```python
counter = 0

def increment():
    global counter
    counter += 1   # without `global` here, this raises UnboundLocalError
```

This trips people up because Python decides a variable is "local to a function" at *compile time* if it's assigned anywhere in that function — so `counter += 1` without the `global` declaration doesn't quietly modify the outer `counter`, it errors, because Python already treats `counter` as local the moment it sees the assignment.

## 9. Common interview traps — know these cold

**Mutable default arguments** — the single most-asked Python gotcha:

```python
def add_item(item, bucket=[]):   # DANGER
    bucket.append(item)
    return bucket

add_item(1)   # [1]
add_item(2)   # [1, 2]  <-- surprise! Same list reused across calls
```

Default arguments are evaluated *once*, when the function is defined, not on every call. Fix: use `None` as the default and create the list inside.

```python
def add_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

**Floating point precision:**

```python
0.1 + 0.2 == 0.3   # False! It's actually 0.30000000000000004
```

Binary floats can't represent most decimals exactly. For money, use `decimal.Decimal` or work in integer cents — directly relevant to your finance-domain project later this plan.

**`is` vs `==`** — covered above, but it's asked so often it's worth repeating: use `==` for value equality, `is` only for identity checks (`is None`, `is True`), never for general comparisons.

---

## Practice questions

Attempt these yourself first — write actual code, run it, see what happens. Then ask me anything that surprised you, or paste your answer for a check.

1. **Predict the output** (then run it and see if you were right):
   ```python
   def mystery(x, y=[]):
       y.append(x)
       return y

   print(mystery(1))
   print(mystery(2))
   print(mystery(3, []))
   print(mystery(4))
   ```

2. **Write a function** `fizzbuzz(n)` that returns a list of strings for numbers 1 through `n`: `"Fizz"` for multiples of 3, `"Buzz"` for multiples of 5, `"FizzBuzz"` for multiples of both, and the number itself (as a string) otherwise. Use it to make sure your loop, control flow, and string handling are all solid.

3. **Explain in your own words** (out loud or in a note, not just in your head): why does `0.1 + 0.2 == 0.3` evaluate to `False`? What would you use instead if you were summing prices in a financial application?

4. **Scope puzzle** — predict what this prints, then verify:
   ```python
   x = 10

   def f():
       print(x)
       x = 20

   f()
   ```
   (Hint: this one *errors* — figure out why before running it, then explain the LEGB rule's role in the error.)

---

*When you've worked through these, tell me your answers or where you got stuck — that's more useful than me just handing you solutions. Once this topic's checked off, say "next" and I'll build the doc for collections (lists, tuples, dicts, sets).*
