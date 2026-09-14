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

### What's actually happening in memory when you run those two lines

This is the single most important mental model for all of Python, and it's worth building it correctly right here at the very start, because every later "gotcha" in this doc (and the next one) traces back to it.

**Simple explanation first.** Think of a variable name like `x` as a sticky note, and every value (`5`, `"hello"`) as a physical box sitting somewhere in a warehouse (memory). "Assigning" a variable — `x = 5` — does not create a box labeled `x` and pour the number 5 into it. Instead, Python creates a box containing `5` somewhere in the warehouse, and sticks a note that says `x` onto that box. `x = "hello"` doesn't erase anything inside the `5` box — it makes a brand new box containing `"hello"`, and *peels the `x` sticky note off the old box and moves it to the new one*. The `5` box is left with no sticky note on it at all, so Python's garbage collector eventually clears it away.

**Step-by-step trace of the two lines above:**

```
Line 1: x = 5
    ┌────────┐
    │   5    │  ← a new int object is created in memory
    └────────┘
        ▲
        │
       [x]        ← the name "x" is bound to (points at) that object

Line 2: x = "hello"
    ┌────────┐        ┌───────────┐
    │   5    │        │  "hello"  │  ← a NEW str object is created
    └────────┘        └───────────┘
                            ▲
                            │
                           [x]        ← "x" is REBOUND to point here instead

    (the "5" object above is now unreferenced — nothing points at it —
     so it becomes eligible for garbage collection)
```

The technical term for this is that Python variables are **names bound to objects**, not typed storage locations. The type doesn't live on the name `x` at all — it lives on the *object* currently being pointed at. That's the literal mechanism behind "dynamically typed": `type(x)` doesn't ask "what type was `x` declared as", it asks "what type is the object `x` is currently pointing at". You can prove this to yourself:

```python
x = 5
print(type(x))     # <class 'int'>
x = "hello"
print(type(x))     # <class 'str'>
```

**Real-world tie-back:** this "name is a sticky note, not a box" model is exactly why the next section's example (`b = a`) behaves the way it does — you're not copying a box, you're sticking a second note on the *same* box.

## 2. Variables & naming

Python uses `snake_case` for variables and functions, `PascalCase` for classes (you'll see this in the OOP doc). A variable is really just a name bound to an object in memory — assignment doesn't copy the value, it points the name at an object.

```python
a = [1, 2, 3]
b = a        # b points at the SAME list, not a copy
b.append(4)
print(a)     # [1, 2, 3, 4] — a changed too
```

This matters constantly once you get to functions and mutable default arguments (see §9). Hold onto it.

### Tracing this for real, with proof it's the *same* object

Running that exact snippet, plus a couple of extra lines to make the "same object" claim provable rather than something you have to take on faith:

```python
a = [1, 2, 3]
b = a
b.append(4)
print(a)
print("id(a) ==", id(a))
print("id(b) ==", id(b))
print("a is b:", a is b)
```

**Real, verified output:**

```
[1, 2, 3, 4]
id(a) == 140016935850560
id(b) == 140016935850560
a is b: True
```

(Your actual `id()` numbers will differ every run — it's a memory address, which changes machine to machine and run to run. What matters is that `id(a)` and `id(b)` are *the same number as each other* — proof they're the same box.)

**Flow diagram — what happens at each line:**

```
Line 1: a = [1, 2, 3]
    ┌───────────────┐
    │ [1, 2, 3]     │   ← one list object created
    └───────────────┘
            ▲
            │
           [a]

Line 2: b = a
    ┌───────────────┐
    │ [1, 2, 3]     │   ← NO new object — nothing was copied
    └───────────────┘
            ▲   ▲
            │   │
           [a] [b]        ← two names, both pointing at the SAME object

Line 3: b.append(4)
    ┌───────────────┐
    │ [1, 2, 3, 4]  │   ← the ONE shared object is mutated in place
    └───────────────┘
            ▲   ▲
            │   │
           [a] [b]        ← both names still point here, so BOTH "see" the change

Line 4: print(a)  ->  [1, 2, 3, 4]
    a was never reassigned — it's still pointing at the object b just mutated.
```

The critical distinction to internalize: `b = a` is a **rebind** (attach a second sticky note to the existing box), while `b.append(4)` is a **mutation** (reach into the box and change what's inside it, without touching any sticky notes at all). If you wanted `b` to be independent, you needed `b = a.copy()` or `b = a[:]` — an actual new box — which is exactly what Topic 2 (`02 python collections.md`, §2) covers under "Copying — the gotcha that connects back to Topic 1." This is that connection, made explicit: the "gotcha" *is* this exact mental model, just applied to `.copy()` afterward.

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

### `type()` vs `isinstance()` — why the difference matters, with a real run

**Simple explanation:** `type(x)` asks "what *exact* box is this?" `isinstance(x, SomeType)` asks the broader question "is this box a `SomeType`, or any more specific kind of `SomeType`?" `bool` being a subclass of `int` (from the table above) is the perfect real example, because it's a case where the two functions actually disagree:

```python
flag = True
print(type(flag) == int)        # is the EXACT type int? 
print(isinstance(flag, int))    # is it an int, or a SUBCLASS of int?
print(isinstance(flag, bool))
```

**Real, verified output:**

```
False
True
True
```

**Why:** `type(True)` is exactly `bool`, not `int` — so the strict `==` check against `int` fails. But `bool` *is a subclass of* `int` (this is stated directly in the table above — `True == 1` only works because of this relationship), so `isinstance(flag, int)` walks up that inheritance chain and correctly reports `True`. This is precisely why the doc recommends `isinstance` for real code: once you reach the OOP doc and start building class hierarchies, a function written with `type(x) == Base` will silently reject every subclass instance, while `isinstance(x, Base)` correctly accepts them. You're not expected to fully feel *why* that matters yet — the OOP doc is where inheritance is built up from scratch — this is just planting the seed with a real, runnable example now so it's not new vocabulary later.

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

### Running every line above for real, and what's happening under the hood

**Real, verified output**, running exactly the lines above wrapped in `print()`:

```
42
42
3.14
False
False
False
False
True
```

Every value matches what the inline comments already promised — good, that confirms the mental model is right. Now the deeper "how":

**How `bool(x)` actually decides true/false.** Every object in Python can be asked "are you truthy?" via a special method Python calls internally, roughly `x.__bool__()`. If an object doesn't define `__bool__`, Python falls back to asking `len(x)` instead — and treats a length of `0` as falsy, anything else as truthy. That's *why* `bool([])` is `False` but `bool([0])` is `True`: an empty list has `len() == 0`, but `[0]` has one element in it — the fact that the element itself happens to be the falsy number `0` is irrelevant, because `bool()` on the list never even looks *inside* it. It only asks "how many things do you contain."

```python
print(bool([0]))     # True — list has 1 element, even though that element is falsy
print(bool([]))      # False — list has 0 elements
```

Running this: `True` then `False` — confirms the "length, not content" rule directly.

**Why `bool("False")` is `True`.** This is the one that actually confuses people, so it's worth a direct flow trace: `bool()` is handed the string `"False"`. It does not read the characters `F`, `a`, `l`, `s`, `e` and think "that spells out falsehood." It only asks one question of the string: "what is your `len()`?" `len("False")` is `5` (five characters) — a non-zero length — so the answer is `True`. The *content* of the string is completely invisible to `bool()`; only its length matters. This is exactly the same rule as the list example above, just applied to a string instead of a list — one rule, two data types, same mechanism.

**Real-world tie-back:** this is the exact bug lurking in code like `if request.form.get("is_active"):` when a web form submits the *string* `"False"` instead of an actual boolean — that `if` will be `True`, because a non-empty string is truthy no matter what it says. This is a genuinely common real bug in form-handling code, not just a trivia question.

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

### Tracing `==` vs `is`, for real, including the small-int cache

**Real, verified output** for the `a`/`b` example plus the small-integer caching claim:

```python
a = [1, 2, 3]
b = [1, 2, 3]
print("a == b:", a == b)
print("a is b:", a is b)
print("a is a:", a is a)

x = 5
y = 5
print("x is y:", x is y)
```

```
a == b: True
a is b: False
a is a: True
x is y: True
```

**Flow diagram — why `a == b` is `True` but `a is b` is `False`:**

```
a = [1, 2, 3]          b = [1, 2, 3]

    ┌───────────┐          ┌───────────┐
    │ [1, 2, 3] │          │ [1, 2, 3] │    ← TWO separate objects, two
    └───────────┘          └───────────┘       separate addresses in memory,
         ▲                      ▲               even though the VALUES inside
         │                      │               them happen to be identical
        [a]                    [b]

a == b  →  Python compares the CONTENTS of the two boxes, element by element.
           Same contents  →  True.

a is b  →  Python compares the ADDRESSES of the two boxes (like comparing
           house numbers, not what's inside the houses).
           Different addresses  →  False.
```

**Why `x is y` came back `True` for `5`.** This is CPython's small-integer cache: at startup, CPython pre-creates a single, shared object for every integer from `-5` to `256` and reuses that *same* object every time your code writes a literal in that range — it never bothers allocating a fresh box for `5` a second time. So `x = 5` and `y = 5` end up as two sticky notes on the *one* pre-made `5` object, which is why `x is y` reports `True` here. This is a CPython implementation detail (not a language guarantee — other Python implementations aren't required to do it, and even CPython doesn't promise to keep doing it forever), which is exactly why the doc's advice stands: never write code that *depends* on `is` working for value comparison, even when you've just seen it work. Always use `==` for values.

### Tracing the short-circuit example, step by step

**Real, verified output:**

```python
def expensive():
    print("called!")
    return True

r1 = False and expensive()
print("result:", r1)
r2 = True or expensive()
print("result:", r2)
```

```
result: False
result: True
```

Notice `"called!"` never appears in the output at all — `expensive()` was never actually invoked, in either line. Here's the step-by-step evaluation Python actually performs:

```
Line: False and expensive()

  Step 1: evaluate the LEFT side first  ->  False
  Step 2: `and` asks: "is the left side already falsy?"
          Yes (False) -> the overall result MUST be falsy no matter what
          the right side is, so Python doesn't even bother evaluating it.
  Step 3: expensive() is SKIPPED entirely — never called, "called!" never prints.
  Result: False   (this is literally the left operand itself, not a new bool)

Line: True or expensive()

  Step 1: evaluate the LEFT side first  ->  True
  Step 2: `or` asks: "is the left side already truthy?"
          Yes (True) -> the overall result MUST be truthy no matter what
          the right side is, so Python doesn't bother evaluating it.
  Step 3: expensive() is SKIPPED entirely — never called, "called!" never prints.
  Result: True    (again, the left operand itself)
```

**Real-world tie-back:** this exact mechanism is why code like `if user and user.is_active:` is safe even when `user` is `None` — because `and` short-circuits, `user.is_active` (which would crash with `AttributeError: 'NoneType' object has no attribute 'is_active'`) is never evaluated when `user` is already falsy. This pattern shows up constantly in real code and is worth recognizing on sight.

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

### Running the ternary for real, both branches

```python
age = 20
status = "adult" if age >= 18 else "minor"
print(status)

age = 15
status = "adult" if age >= 18 else "minor"
print(status)
```

**Real, verified output:**

```
adult
minor
```

**How to read a ternary, mechanically, left to right — this trips people up because the "condition" is in the *middle*, not the front like a normal `if`:**

```
status =  "adult"      if      age >= 18      else      "minor"
           │                    │                         │
           │                    │                         └─ value used if condition is FALSE
           │                    └─ the condition, evaluated FIRST despite being in the middle
           └─ value used if condition is TRUE
```

It is pure syntax sugar for the full `if`/`else` block above it — nothing new is happening semantically, it's a single *expression* (something that produces a value you can assign) instead of a *statement* (a block of code). The full version:

```python
if age >= 18:
    status = "adult"
else:
    status = "minor"
```

does exactly the same thing, in four lines instead of one. Reach for the ternary only when both branches are short, simple values — nesting ternaries or stuffing complex logic into them makes code harder to read, not easier.

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

### Running every loop above for real

**Real, verified output**, running the block exactly as written (with print separators added so it's clear which output belongs to which loop):

```
1
2
3
---range---
0
1
2
3
4
---enumerate---
0 a
1 b
---zip---
1 x
2 y
---while---
final i: 5
---for-else found---
found
---for-else not found---
not found
```

**`enumerate` — flow, step by step.** `enumerate(["a", "b"])` doesn't hand you `"a"` then `"b"` directly — it wraps each item together with its position, producing pairs: `(0, "a")` then `(1, "b")`. The `for i, item in ...` line **unpacks** each pair into two names in one step — `i` gets the number, `item` gets the original value:

```
enumerate(["a", "b"]) produces, one at a time:
    (0, "a")   →   i, item = 0, "a"   →   print(0, "a")
    (1, "b")   →   i, item = 1, "b"   →   print(1, "b")
```

Without `enumerate`, getting the index would mean a manual counter (`i = 0` before the loop, `i += 1` inside it) — `enumerate` exists specifically to remove that boilerplate and the off-by-one bugs it invites.

**`zip` — flow, step by step.** `zip([1, 2], ["x", "y"])` walks *two* iterables in lockstep, pairing up their elements position by position — first item with first item, second with second — and stops as soon as the *shorter* of the two runs out (worth knowing: if the lists were different lengths, `zip` silently drops the extra elements from the longer one rather than erroring):

```
zip([1, 2], ["x", "y"]) produces:
    (1, "x")   →   a, b = 1, "x"   →   print(1, "x")
    (2, "y")   →   a, b = 2, "y"   →   print(2, "y")
```

**`for`/`else` — why it printed `"found"` without ever reaching the `else`, and `"not found"` when it did.** This is the loop construct people find most surprising, because in almost every other language `else` after a loop doesn't exist at all. The rule: the `else` block runs **only if the loop finished all its iterations without ever hitting a `break`.** A `break` skips the `else` entirely.

```
Run 1: target = 3, items = [1, 2, 3, 4]

  iteration 1: item=1, 1 == 3? no
  iteration 2: item=2, 2 == 3? no
  iteration 3: item=3, 3 == 3? YES -> print("found") -> break
  loop exits via break  ->  else block is SKIPPED
  (output: "found" only)

Run 2: target = 99, items = [1, 2, 3, 4]

  iteration 1: item=1, 1 == 99? no
  iteration 2: item=2, 2 == 99? no
  iteration 3: item=3, 3 == 99? no
  iteration 4: item=4, 4 == 99? no
  loop exhausts every item, NEVER hit break -> else block DOES run
  (output: "not found")
```

The mental model that actually sticks for most people: read the loop's `else` as "**no-break**", not as "otherwise." It answers the question "did this loop complete naturally, with nothing found?" — which is exactly the shape of a linear search, and is why this pattern shows up in real interview "search a list" questions.

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

### Running `greet()` for real, and tracing the LEGB and `global` examples

**Real, verified output** for the three `greet()` calls:

```
Hello, Ani!
Hi, Ani!
Hi, Ani!
```

All three calls land on the same result-shape because the third call (`greet(name="Ani", greeting="Hi")`) is just the second call with its positional argument also written as a keyword — Python doesn't care how an argument was *labeled* once it's matched to a parameter, only that every parameter ends up with exactly one value.

**LEGB — real, verified output:**

```
local
enclosing
global
```

**Flow diagram — three stacked scopes, and where each `print(x)` looks first:**

```
Call stack, from outside in:

┌─ GLOBAL scope ─────────────────────────────┐
│  x = "global"                               │
│                                              │
│  ┌─ outer()'s scope (ENCLOSING, relative   │
│  │  to inner) ─────────────────────────────┐│
│  │  x = "enclosing"                        ││
│  │                                          ││
│  │  ┌─ inner()'s scope (LOCAL) ───────────┐││
│  │  │  x = "local"                        │││
│  │  │  print(x)  →ⓛ  looks in inner's own │││
│  │  │              scope FIRST, finds     │││
│  │  │              "local" immediately,   │││
│  │  │              STOPS searching        │││
│  │  └──────────────────────────────────────┘││
│  │                                          ││
│  │  print(x)  →ⓔ  inner() has already      ││
│  │              returned; back in outer's  ││
│  │              own scope, which has its   ││
│  │              own x = "enclosing"        ││
│  └──────────────────────────────────────────┘│
│                                              │
│  print(x)  →ⓖ  outer() has returned too;    │
│              back at module level, only     │
│              global x = "global" exists     │
└──────────────────────────────────────────────┘
```

The key insight the LEGB name encodes: **each `print(x)` starts its search in its *own* innermost scope and stops at the first match** — it never "sees" the other `x`s at all, because a matching name closer in was found first. There are three completely separate `x` variables here, living in three separate boxes; they never collide because each function's assignment (`x = "local"`, `x = "enclosing"`) creates a *new*, shadowing name in that function's own scope, rather than modifying the outer one.

**Real, verified output for the `global` example:**

```python
counter = 0

def increment():
    global counter
    counter += 1

increment()
increment()
print(counter)
```

```
2
```

**Why `global` is required here, traced mechanically.** Without the `global counter` line, `counter += 1` inside `increment()` would raise `UnboundLocalError: local variable 'counter' referenced before assignment`. The reason is subtle and worth getting exactly right, because it's a genuinely common point of confusion: Python decides, **before your function ever runs** — while it's first reading and compiling the function's code — whether each name is local or not, by scanning the function body for *any* assignment to that name anywhere in it. `counter += 1` is secretly `counter = counter + 1`, which is an assignment to `counter` — so Python marks `counter` as local to `increment()` the moment it parses that line, regardless of the fact that a global `counter` also happens to exist. Then, when the function actually *runs*, the right-hand side `counter + 1` tries to *read* the local `counter` — but nothing has assigned it a value yet in this call, so reading it fails immediately, before the assignment even completes. The `global counter` declaration is what tells Python, ahead of time, "don't treat `counter` as local in this function at all — every reference to it means the module-level one," which changes the compile-time classification and makes both the read and the write in `counter += 1` target the outer variable.

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

### Tracing the mutable-default bug with hard proof it's the *same* list object

**Real, verified output** for the buggy version exactly as written above:

```
[1]
[1, 2]
```

That confirms the doc's claim. Now here's proof, not just assertion, that it's genuinely the *same* list object being reused — printing `id(bucket)` on every call:

```python
def add_item(item, bucket=[]):
    print("id of bucket this call:", id(bucket))
    bucket.append(item)
    return bucket

r1 = add_item(1)
r2 = add_item(2)
print(r1 is r2)
```

**Real, verified output:**

```
id of bucket this call: 139903135765056
id of bucket this call: 139903135765056
True
```

Same `id()` both calls, and `r1 is r2` is `True` — this is not two lists that happen to look the same, it is *the exact same box*, referenced twice.

**Flow diagram — why this happens, tied to §1's "name bound to an object" model:**

```
When Python reads (compiles) this function definition:

    def add_item(item, bucket=[]):
        ...

it evaluates the default value expression `[]` EXACTLY ONCE, right then —
NOT every time the function is later called — and stores that one list
object as part of the function object itself.

    ┌─────────────────────────┐
    │  add_item function obj  │
    │  defaults: bucket -> ●──┼──►  ┌────┐
    └─────────────────────────┘     │ [] │   ← ONE list, created at def-time
                                     └────┘

Call 1: add_item(1)
    - "bucket" wasn't passed, so it falls back to the function's stored
      default — that SAME [] object from above.
    - bucket.append(1) mutates that shared object in place.
                                     ┌─────┐
                                     │ [1] │
                                     └─────┘

Call 2: add_item(2)
    - "bucket" wasn't passed AGAIN, so it falls back to the SAME default
      object again — Python has no idea (and no way to know) that the
      previous call already mutated it. There is only ever one default
      object, sitting on the function, permanently, until the function
      is redefined.
    - bucket.append(2) mutates that SAME object again.
                                     ┌────────┐
                                     │ [1, 2] │
                                     └────────┘
```

This is the exact same "shared mutable object" mechanism from §2's `b = a` example — the only difference is *where* the shared reference comes from: in §2 it was an explicit `b = a`, here it's Python silently handing out the same stored default object on every call that doesn't override it. Once you see it as "one box, multiple sticky notes pointing at it, and someone keeps reaching into the box," both bugs are the same bug.

**Why the fix works — tracing the `None`-sentinel version:**

```python
def add_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket

print(add_item(1))
print(add_item(2))
```

**Real, verified output:**

```
[1]
[2]
```

Here, the default value stored on the function is `None` — and `None` is immutable, so there's nothing dangerous about reusing the *same* `None` on every call (you can't "mutate" `None`). The critical difference is the line `if bucket is None: bucket = []` — this creates a **brand-new, empty list, inside the function body, on every single call**, only when the caller didn't supply their own. So call 1 and call 2 each get their own fresh `[]`, never sharing one — which is exactly why `id()` would differ between them here, unlike the buggy version above.

### Verifying the float-precision claim for real, and why it happens

**Real, verified output:**

```python
print(0.1 + 0.2 == 0.3)
print(repr(0.1 + 0.2))
```

```
False
0.30000000000000004
```

**The "why", at the level worth actually understanding (not just memorizing):** computers store floats in binary (base 2), using a fixed number of bits (IEEE 754 double precision — 64 bits total). The problem is that most decimal fractions — including perfectly simple-looking ones like `0.1` — **cannot be represented exactly in binary**, for the same structural reason that `1/3` cannot be written exactly in decimal (you get `0.3333...`, forever, no matter how many digits you allow). `0.1` in binary is an infinitely repeating fraction, so it gets silently rounded to the *nearest representable* 64-bit value — a value that is extremely close to `0.1` but not exactly `0.1`. The same happens to `0.2` and `0.3`. When you add the *rounded* versions of `0.1` and `0.2`, the tiny rounding errors don't cancel out to exactly match the tiny rounding error already baked into the stored `0.3` — so the equality check correctly (if surprisingly) reports `False`, and `repr()` reveals the actual, slightly-off value Python has been carrying around the whole time.

**Real-world tie-back:** this is precisely why the doc calls out `decimal.Decimal` for money — `Decimal` stores numbers in base 10 internally instead of binary, so `0.1` and `0.2` really are stored exactly, at the cost of being slower than native floats. The integer-cents alternative (store `$19.99` as the integer `1999`, only dividing by 100 for display) sidesteps the problem entirely by never using fractional values at all during calculation — both are real techniques used in production financial code, not just interview trivia.

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
