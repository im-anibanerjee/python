# Topic 10 — `*args`, `**kwargs` & Functional Tools, Deep Dive

*Phase 1, Intermediate group — item 6 of 6, the last one before the Advanced group. You've already used `*args`/`**kwargs` in every decorator you've written — this doc is the full mechanics behind them, plus `map`/`filter`/`reduce` and the rest of Python's small functional-programming toolkit.*

---

## 1. `*args` — collecting extra positional arguments

```python
def add_all(*args):
    print(args, type(args))
    return sum(args)

add_all(1, 2, 3)      # args = (1, 2, 3) <class 'tuple'>  -> 6
add_all(5)              # args = (5,) <class 'tuple'>        -> 5
add_all()                 # args = () <class 'tuple'>          -> 0
```

`*args` in a function's *signature* means "collect however many positional arguments were passed, as a tuple, and call it `args`." (`args` is just a convention — the `*` is what does the collecting; you could call it `*numbers` and it'd work identically. But `*args` is the name everyone uses, and deviating from it in real code just makes it harder for other people to read at a glance.) Note the type: always a `tuple`, always — even with zero arguments passed, you get an empty tuple, never `None`.

## 2. `**kwargs` — collecting extra keyword arguments

```python
def describe(**kwargs):
    print(kwargs, type(kwargs))

describe(name="Ani", role="engineer")     # kwargs = {'name': 'Ani', 'role': 'engineer'} <class 'dict'>
describe()                                        # kwargs = {} <class 'dict'>
```

`**kwargs` collects however many *keyword* arguments were passed — ones given as `name=value` — into a `dict`, keyed by the argument name. Same story as `args`: `kwargs` is convention, `**` is the mechanism, always a `dict`, empty dict on zero keyword arguments.

## 3. The full parameter ordering rules

A function signature can mix five different kinds of parameters, and Python enforces a strict order for them. Laid out fully:

```python
def f(a, b=1, *args, c, d=2, **kwargs):
    ...
```

`a` — a normal **positional** parameter, no default, required.
`b=1` — positional, but *with* a default — can still be passed positionally or by keyword, but optional.
`*args` — collects any extra positional arguments beyond `a`/`b`.
`c` — appears *after* `*args`. This makes `c` **keyword-only**: once you've written `*args` (or a bare `*` with no name — see below), every parameter after it can *only* be passed as `keyword=value`, never positionally, no matter how many positional arguments you pass. This exists specifically to force clarity at the call site for parameters where a positional call would be ambiguous or error-prone to read.
`d=2` — also keyword-only (still after `*args`), with a default this time — optional.
`**kwargs` — always comes last; collects any extra keyword arguments not otherwise named.

```python
f(10, 20, 30, 40, c=5)
# a=10, b=20, args=(30, 40), c=5, d=2 (default), kwargs={}

f(10, c=5, d=6, extra="hi")
# a=10, b=1 (default), args=(), c=5, d=6, kwargs={'extra': 'hi'}

f(10, 20, c=5, e="x")
# a=10, b=20, args=(), c=5, d=2 (default), kwargs={'e': 'x'}
```

**A bare `*` with no name after it** does the same "everything after this is keyword-only" job, *without* collecting extra positional arguments into a tuple — useful when you want to force keyword-only arguments but don't actually want a catch-all for extra positional ones:

```python
def connect(host, port, *, timeout=30):
    ...

connect("localhost", 8080, timeout=5)     # fine
connect("localhost", 8080, 5)                  # TypeError — timeout can't be positional, the bare * blocks it
```

**A bare `/` (Python 3.8+)** is the mirror image — everything *before* it is **positional-only**, meaning it can *never* be passed by keyword, even though it has a name:

```python
def power(base, exponent, /):
    return base ** exponent

power(2, 3)                        # 8 — fine
power(base=2, exponent=3)   # TypeError — base/exponent are positional-only, can't use their names
```

This shows up in built-ins more than in code you'll typically write yourself — e.g. `len(obj, /)` is positional-only, which is why `len(obj=[1,2,3])` fails even though `obj` clearly has a name internally. It exists so a library author can rename an internal parameter later without breaking anyone who was calling it by keyword.

## 4. Unpacking — the *other* use of `*` and `**`

Everything above is about *receiving* arguments in a signature. `*` and `**` do the reverse job too, at the *call site* — spreading an existing collection out into separate arguments:

```python
def add3(a, b, c):
    return a + b + c

nums = [1, 2, 3]
add3(*nums)          # same as add3(1, 2, 3) — * unpacks a list/tuple into positional arguments

data = {"a": 1, "b": 2, "c": 3}
add3(**data)         # same as add3(a=1, b=2, c=3) — ** unpacks a dict into keyword arguments, matching by key name
```

This is the exact mechanism that makes the decorator pattern from Topic 8 work: `func(*args, **kwargs)` inside `wrapper` isn't collecting anything — `args`/`kwargs` are already tuples/dicts by that point — it's *spreading them back out* to call `func` with whatever was originally passed in, individually, as if you'd written out each argument by hand. Collecting (in a signature) and unpacking (at a call site) are two directions of the same `*`/`**` idea, and a single line of code often does both in sequence, as you've already seen: `def wrapper(*args, **kwargs): return func(*args, **kwargs)` collects into `wrapper`'s `args`/`kwargs`, then immediately unpacks those same two variables to call `func`.

`**` unpacking also works to merge dictionaries inline:

```python
defaults = {"color": "blue", "size": "M"}
overrides = {"size": "L"}
merged = {**defaults, **overrides}
# {'color': 'blue', 'size': 'L'} — later keys win when there's a collision, same as dict.update()
```

## 5. `lambda` — a one-line, unnamed function

Before the functional tools below make sense, you need `lambda` — Python's syntax for a small, throwaway function written inline, with no `def` and no name:

```python
square = lambda x: x ** 2
square(5)          # 25

# equivalent to:
def square(x):
    return x ** 2
```

`lambda parameters: expression` — that's the whole syntax. It can take any number of parameters (`lambda x, y: x + y`), but the body must be a single *expression* — no statements, no `if`/`else` blocks (only the expression form of `if`, e.g. `lambda x: "even" if x % 2 == 0 else "odd"`), no multiple lines. `lambda`'s entire reason to exist is being passed somewhere that expects a small function *right there*, without the ceremony of a separate `def` a few lines up — which is exactly what `map`, `filter`, and `sorted(key=...)` are built around.

## 6. `map()` — apply a function to every item

```python
nums = [1, 2, 3, 4]
squares = map(lambda x: x ** 2, nums)
print(squares)          # <map object at 0x...> — a LAZY ITERATOR, not a list, same idea as generators
print(list(squares))    # [1, 4, 9, 16]
```

`map(func, iterable)` returns an iterator (not a list — you already know this shape from the generators doc: it produces values one at a time, on demand, and you need `list(...)` or a `for` loop to actually pull them out). Every value from `iterable` gets passed through `func`, one at a time. `map` also accepts *multiple* iterables, zipping them together argument-by-argument:

```python
a = [1, 2, 3]
b = [10, 20, 30]
list(map(lambda x, y: x + y, a, b))     # [11, 22, 33]
```

The equivalent comprehension — and it's worth seeing both, since comprehensions are usually the more idiomatic modern choice:

```python
[x ** 2 for x in nums]      # same result as list(map(lambda x: x**2, nums)), more Pythonic
```

## 7. `filter()` — keep only items that pass a test

```python
nums = [1, 2, 3, 4, 5, 6]
evens = filter(lambda x: x % 2 == 0, nums)
print(list(evens))     # [2, 4, 6]
```

`filter(func, iterable)` keeps only the items where `func(item)` is truthy — also a lazy iterator, same as `map`. Passing `None` as the function is a documented special case: `filter(None, iterable)` keeps only the *truthy* items of `iterable` directly, with no function at all (`filter(None, [0, 1, "", "hi", None, 5])` → `[1, "hi", 5]`).

Equivalent comprehension:
```python
[x for x in nums if x % 2 == 0]      # same result, and this is the version you'll actually see most often in real code
```

## 8. `functools.reduce()` — collapse a sequence into one value

```python
from functools import reduce

nums = [1, 2, 3, 4]
total = reduce(lambda acc, x: acc + x, nums)
print(total)     # 10
```

`reduce(func, iterable)` is the one of these three with no comprehension equivalent — it doesn't produce a new sequence, it collapses the whole sequence down into a single result by repeatedly applying `func` to a running "accumulator" and the next item. Trace it explicitly:

```
nums = [1, 2, 3, 4]
step 1: acc = 1 (first element, no explicit start given), x = 2  ->  func(1, 2) = 3
step 2: acc = 3,                                       x = 3  ->  func(3, 3) = 6
step 3: acc = 6,                                       x = 4  ->  func(6, 4) = 10
result: 10
```

`reduce` also takes an optional third argument, an explicit starting value, which is safer and clearer than relying on the first element:

```python
reduce(lambda acc, x: acc + x, nums, 100)     # starts acc at 100 instead of nums[0]  ->  110
reduce(lambda acc, x: acc + x, [], 0)             # 0 — an empty list with NO starting value would raise TypeError instead
```

`reduce` genuinely earns its place in an interview toolkit for things like "find the maximum," "flatten a list of lists," or "multiply everything together" when you want to express it as one line rather than a manual loop with an accumulator variable — though for very common cases like sum/max/min, Python's built-ins (`sum()`, `max()`, `min()`) already do the job and should be preferred over hand-rolling them with `reduce`.

## 9. `sorted()` with `key=` — functional-style customization, not full functional tools, but the same spirit

```python
words = ["banana", "fig", "apple", "kiwi"]
sorted(words, key=len)                    # ['fig', 'kiwi', 'apple', 'banana'] — sorted by LENGTH, not alphabetically
sorted(words, key=lambda w: w[-1])   # sorted by each word's LAST letter
```

`key=` takes a function, applies it to every item first, and sorts based on *those results* rather than the items themselves — this is the same "pass a function in as configuration" idea as `map`/`filter`, worth grouping mentally with them even though `sorted` isn't purely a "functional tool" in the same textbook sense.

## 10. `functools.partial` — pre-filling some arguments ahead of time

```python
from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)     # "power, but exponent is always 2 now"
cube = partial(power, exponent=3)

square(5)     # 25   -- same as power(5, exponent=2)
cube(5)         # 125  -- same as power(5, exponent=3)
```

`partial(func, *args, **kwargs)` returns a *new* callable that remembers some arguments in advance (via a closure, same underlying mechanism as everything you've already seen in the decorators doc) and lets you supply the rest later. It's a clean way to specialize a general function into several more specific ones without writing a separate `def` for each — a genuine, small piece of functional programming style, distinct from decorators (which wrap a function's *behavior*) — `partial` just pre-fills arguments, the function's actual logic is untouched.

## 11. `any()` and `all()` — quick boolean checks over an iterable, often paired with a generator expression

```python
nums = [2, 4, 6, 8]
all(x % 2 == 0 for x in nums)     # True — every element even
any(x > 100 for x in nums)          # False — none exceed 100
```

Note the generator expression passed directly, no square brackets — `all()`/`any()` only need to look at values one at a time and can stop as soon as the answer is decided (`any` stops at the first `True`; `all` stops at the first `False`), so a generator expression here avoids building the full list of booleans in memory first, same efficiency argument as the generators doc.

## 12. Interview-distilled

"What's the difference between `*args` and `**kwargs`?" — `*args` collects extra *positional* arguments into a tuple; `**kwargs` collects extra *keyword* arguments into a dict. Same underlying idea (catch whatever wasn't explicitly named), different argument style.

"Why do decorators always use `*args, **kwargs` in the wrapper?" — because the wrapper doesn't know in advance what the wrapped function's signature is; `*args, **kwargs` lets it accept literally anything and forward it unchanged via `func(*args, **kwargs)`.

"What makes a parameter keyword-only?" — appearing after a `*args` or a bare `*` in the function signature. It can then only be supplied as `name=value` at the call site, never positionally.

"When would you use `reduce` over a plain loop?" — when the operation is a simple, repeated combination of a running value with each item (sum, product, running max) and you want to express it in one line rather than manually initializing and updating an accumulator variable — though built-ins (`sum`, `max`, `min`) cover the most common cases already.

---

## Practice questions

1. **Write a function `describe_call(*args, **kwargs)`** that returns a single formatted string describing exactly what was passed to it, e.g. `describe_call(1, 2, x=3)` should reflect `args=(1, 2)` and `kwargs={'x': 3}` in its output. Then call it four different ways — no arguments, only positional, only keyword, a mix — and confirm each one's `args`/`kwargs` split matches what you'd expect.

2. **Keyword-only in practice.** Write a function `make_user(name, *, age, active=True)` — `age` should be required and keyword-only; `active` optional and keyword-only. Call it correctly (`make_user("Ani", age=30)`), then deliberately call it with `age` passed positionally (`make_user("Ani", 30)`) and paste the exact `TypeError` you get.

3. **Unpacking round-trip.** Given `values = [10, 20, 30]` and a function `def total(a, b, c): return a + b + c`, call `total` two ways: once by unpacking `values` with `*`, and once by manually building a dict `{"a": 10, "b": 20, "c": 30}` and unpacking it with `**`. Confirm both give the same result.

4. **`map`/`filter` vs. comprehensions.** Take a list of 10 integers of your choice. Using `map`+`lambda`, produce a list of their squares. Using `filter`+`lambda`, keep only the ones divisible by 3. Then rewrite *both* as list comprehensions instead, and note in a comment which version you find more readable and why.

5. **`reduce`, from scratch.** Using `functools.reduce`, write one line that finds the maximum value in a list of numbers *without* using the built-in `max()` (the whole point is practicing the accumulator-comparison pattern by hand). Test it against a list where the maximum isn't the first or last element, to make sure your comparison logic is actually right and not accidentally just returning the first item.

---

*Same as always — write real code, run it, and paste your answers when ready. This closes out the Intermediate group — say "next" and I'll build the doc for the Advanced group's first topic, asyncio.*
