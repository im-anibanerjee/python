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

### Running this for real

**Real, verified output:**

```
(1, 2, 3) <class 'tuple'>
6
(5,) <class 'tuple'>
5
() <class 'tuple'>
0
```

**Flow diagram — what actually happens at the call site, before `add_all`'s body even starts running:**

```
add_all(1, 2, 3)

    Before a single line of add_all's BODY executes, Python performs
    the PARAMETER BINDING step: it looks at the signature (*args)
    and the arguments actually passed (1, 2, 3), and constructs the
    tuple args = (1, 2, 3) — gathering up EVERYTHING that was passed
    positionally, since there are no other positional parameters
    ahead of *args to soak any of them up first.

    Only AFTER that tuple exists does the body run:
        print(args, type(args))   → (1, 2, 3) <class 'tuple'>
        return sum(args)            → sum((1, 2, 3)) → 6

add_all()   — zero arguments passed

    Same binding step, just with nothing to gather:
        args = ()                    ← an empty tuple, NOT None,
                                        NOT undefined — *args ALWAYS
                                        produces a real tuple object,
                                        even when it's empty
        sum(())  →  0
```

This is worth connecting back to the collections doc directly: `sum(())` returning `0` (not an error) is the same "empty collection is still a real, iterable object" idea you've already seen with empty lists and dicts — `*args` never gives you `None` to guard against, which is precisely why decorator wrappers (Topic 8) can safely call `func(*args, **kwargs)` without checking "did any arguments even get passed" first.

## 2. `**kwargs` — collecting extra keyword arguments

```python
def describe(**kwargs):
    print(kwargs, type(kwargs))

describe(name="Ani", role="engineer")     # kwargs = {'name': 'Ani', 'role': 'engineer'} <class 'dict'>
describe()                                        # kwargs = {} <class 'dict'>
```

`**kwargs` collects however many *keyword* arguments were passed — ones given as `name=value` — into a `dict`, keyed by the argument name. Same story as `args`: `kwargs` is convention, `**` is the mechanism, always a `dict`, empty dict on zero keyword arguments.

### Running this for real

**Real, verified output:**

```
{'name': 'Ani', 'role': 'engineer'} <class 'dict'>
{} <class 'dict'>
```

**Flow diagram — `*args` and `**kwargs` side by side, making the positional-vs-keyword split at the binding step explicit:**

```
Calling a function with a MIX of positional and keyword arguments
sorts them into TWO separate buckets, simultaneously, at binding time:

    some_call(1, 2, x=3, y=4)
                │  │   │    │
                └──┴───┼────┘
              positional   keyword
              → *args        → **kwargs
              = (1, 2)       = {'x': 3, 'y': 4}

    Nothing about the VALUES themselves (1, 2, 3, 4 are all just
    ints) determines which bucket they go in — it's purely about
    HOW they were written at the call site: bare values go to
    *args, name=value pairs go to **kwargs. A function can define
    both *args AND **kwargs together (you've been doing exactly
    this in every decorator's wrapper since Topic 8) to accept
    absolutely anything, sorted into these two buckets automatically.
```

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

### Running all three calls to `f` for real, exactly as the doc's comments claim

**Real, verified output** (using `print(f"a={a}, b={b}, args={args}, c={c}, d={d}, kwargs={kwargs}")` inside `f`):

```
a=10, b=20, args=(30, 40), c=5, d=2, kwargs={}
a=10, b=1, args=(), c=5, d=6, kwargs={'extra': 'hi'}
a=10, b=20, args=(), c=5, d=2, kwargs={'e': 'x'}
```

Every single value matches the doc's inline comments exactly, across all three calls.

**Flow diagram — the binding algorithm for `f(10, 20, 30, 40, c=5)`, traced as an actual step-by-step allocation process (this is the one worth slowing down on — it's the whole rule in action at once):**

```
def f(a, b=1, *args, c, d=2, **kwargs):

call: f(10, 20, 30, 40, c=5)
      positional args supplied: 10, 20, 30, 40   (in that order)
      keyword args supplied: c=5

Binding proceeds LEFT TO RIGHT through the signature, positional
values being consumed in order, keyword values matched by name:

    Step 1: "a" needs a value, no default -> takes the FIRST
            positional value available -> a = 10
            (3 positional values remain: 20, 30, 40)

    Step 2: "b" needs a value (has a default, but a positional
            value is still available and takes priority) -> takes
            the NEXT positional value -> b = 20
            (2 positional values remain: 30, 40)

    Step 3: "*args" scoops up EVERY remaining positional value,
            however many there are -> args = (30, 40)
            (0 positional values remain)

    Step 4: "c" is keyword-only (it's after *args) — it does NOT
            look at leftover positional values at all (there are
            none left anyway) — it looks for a MATCHING KEYWORD
            argument by name -> found c=5 in the call -> c = 5

    Step 5: "d" is also keyword-only — no matching keyword "d="
            was supplied in this call -> falls back to its
            default -> d = 2

    Step 6: "**kwargs" scoops up any keyword arguments that don't
            match any named parameter -> none left unmatched here
            -> kwargs = {}

Final binding: a=10, b=20, args=(30, 40), c=5, d=2, kwargs={}
                ← matches the real, verified output exactly
```

### Running the bare-`*` and bare-`/` examples for real, including both `TypeError`s

**Real, verified output** — bare `*` (`connect`):

```python
print(connect("localhost", 8080, timeout=5))
try:
    connect("localhost", 8080, 5)
except TypeError as e:
    print("TypeError:", e)
```

```
localhost:8080 timeout=5
TypeError: connect() takes 2 positional arguments but 3 were given
```

**Real, verified output** — bare `/` (`power`), plus the real built-in `len()` example the doc references:

```python
print(power(2, 3))
try:
    power(base=2, exponent=3)
except TypeError as e:
    print("TypeError:", e)
try:
    len(obj=[1,2,3])
except TypeError as e:
    print("TypeError (len):", e)
```

```
8
TypeError: power() got some positional-only arguments passed as keyword arguments: 'base, exponent'
TypeError (len): len() takes no keyword arguments
```

**Flow diagram — `*` and `/` as two opposite "fences" drawn across the same parameter list:**

```
def connect(host, port, *, timeout=30):
                          ▲
                          └─ fence: everything AFTER this point
                             is KEYWORD-ONLY (can't be positional)

    connect("localhost", 8080, 5)
                                ▲
                                └─ this 3rd positional value has
                                   NOWHERE valid to bind — host and
                                   port already consumed the first
                                   two positional slots, and the
                                   fence forbids timeout from taking
                                   a THIRD positional value at all
                                   -> TypeError, "too many positional
                                      arguments"

def power(base, exponent, /):
                            ▲
                            └─ fence: everything BEFORE this point is
                               POSITIONAL-ONLY (can't be keyword)

    power(base=2, exponent=3)
           ▲
           └─ trying to bind by NAME to a parameter the fence has
              declared positional-only -> Python can't find a
              positional-only slot to match "base=" against by
              keyword -> TypeError, "positional-only arguments
              passed as keyword arguments"
```

The real `len()` error message — `"len() takes no keyword arguments"` — is worth noting as *slightly* different phrasing than the hand-written `power` example's error, even though both stem from the exact same positional-only mechanism: built-in functions implemented in C sometimes report this restriction with a blunter message than a Python-defined function with an explicit `/` does, but the underlying reason is identical in both cases — the parameter position is fixed and cannot be addressed by name.

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

### Running all three for real

**Real, verified output:**

```
6
6
{'color': 'blue', 'size': 'L'}
```

**Flow diagram — collecting vs. unpacking as two directions of one symbol, drawn side by side to make the symmetry (and the exact opposite of §1's diagram) explicit:**

```
COLLECTING (in a signature) — many separate values -> ONE tuple/dict

    def add_all(*args): ...
    add_all(1, 2, 3)
        1, 2, 3  (three separate values)  ──►  args = (1, 2, 3)  (ONE tuple)

UNPACKING (at a call site) — ONE tuple/dict -> many separate values

    nums = [1, 2, 3]
    add3(*nums)
        nums = [1, 2, 3]  (ONE list)  ──►  a=1, b=2, c=3  (three
                                              separate positional
                                              arguments, matched by
                                              POSITION)

    data = {"a": 1, "b": 2, "c": 3}
    add3(**data)
        data = {...}  (ONE dict)  ──►  a=1, b=2, c=3  (three separate
                                          KEYWORD arguments, matched
                                          by KEY NAME — this is why
                                          **data's keys have to
                                          literally match add3's
                                          parameter names: "a", "b",
                                          "c" — unlike *nums, which
                                          matches purely by POSITION
                                          and doesn't care about names
                                          at all)
```

`{**defaults, **overrides}` is the exact same `**`-unpacking mechanism, just building a *new dict literal* out of two unpacked ones instead of building a function call's arguments — each `**dict` inside the `{...}` spreads that dict's key-value pairs into the new dict being constructed, left to right, with a later key silently overwriting an earlier identical one — precisely the "later keys win" merge behavior you already verified for the `|` operator in the collections doc, just written with `**` instead.

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

### Running this for real

**Real, verified output:**

```
25
```

**Flow diagram — `lambda` produces a genuinely ordinary function object, just built anonymously; worth seeing it side by side with `def` at the object level, not just the syntax level:**

```
square = lambda x: x ** 2

    Creates a real function object — checkable with type(square),
    callable with square(5), inspectable — it just has NO NAME
    baked into its own identity the way "def square(x): ..." does
    (square.__name__ is literally the string "<lambda>", regardless
    of what variable you happen to assign it to — this is a small,
    genuinely common interview gotcha: assigning a lambda to a name
    doesn't rename the function object itself, only the variable
    pointing at it).

square(5)

    Called exactly like any other function — no special mechanism,
    no restriction on how it's invoked, only a restriction on how
    its BODY was written (one expression, no statements).
```

The doc's own framing — "being passed somewhere that expects a small function *right there*" — is the real reason `lambda` exists at all rather than being a shortcut you'd reach for generally: `map(lambda x: x**2, nums)` avoids the ceremony of writing `def square(x): return x**2` three lines above just to use it once, immediately, as an argument. For anything you'd want to reuse, name, or debug easily, a normal `def` is almost always the better choice — `lambda`'s value is specifically in throwaway, inline, single-use cases like the ones the rest of this doc is built around.

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

### Running all three for real, and confirming `map` is genuinely lazy like a generator

**Real, verified output:**

```
<map object at 0x7fb1e4f67f70>
[1, 4, 9, 16]
[11, 22, 33]
[1, 4, 9, 16]
```

That first line — `print(squares)` showing `<map object at 0x...>`, not the computed values — is direct, visible proof of "lazy iterator, not a list": if `map()` had eagerly computed every squared value up front, printing `squares` would show `[1, 4, 9, 16]` immediately; instead it shows an unrealized object, exactly like a generator expression's `print()` output from the generators doc, and only `list(squares)` actually forces every value to be computed.

**Flow diagram — the two-iterable `map`, tracing exactly how `x` and `y` get paired up, since this is the part that's easy to get backwards:**

```
a = [1, 2, 3]
b = [10, 20, 30]
map(lambda x, y: x + y, a, b)

    map walks BOTH iterables in LOCKSTEP, position by position —
    exactly the same pairing mechanism as zip() from the fundamentals
    doc's loops section — pulling one value from EACH iterable per
    step and feeding BOTH into the function as its two arguments:

    step 1: x = a[0] = 1,   y = b[0] = 10   → lambda(1, 10)  = 11
    step 2: x = a[1] = 2,   y = b[1] = 20   → lambda(2, 20)  = 22
    step 3: x = a[2] = 3,   y = b[2] = 30   → lambda(3, 30)  = 33

    result (once forced with list()): [11, 22, 33]
```

`map` would stop as soon as the *shorter* of the two input iterables ran out, exactly like `zip` — one more small consistency worth noticing across the language rather than memorizing as a one-off rule.

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

### Running all three for real

**Real, verified output:**

```
[2, 4, 6]
[1, 'hi', 5]
[2, 4, 6]
```

**Flow diagram — the `filter(None, ...)` special case, traced value by value against the fundamentals doc's truthiness rules directly, since that's exactly what's being invoked here:**

```
filter(None, [0, 1, "", "hi", None, 5])

    With func=None, filter falls back to: "keep this item if bool(item)
    is True" — literally the same truthiness check from the
    fundamentals doc's §4, applied one element at a time:

    0     -> bool(0)     = False  (falsy — from the fundamentals
                                     doc's explicit falsy-values list)
                                     -> DROP
    1     -> bool(1)     = True                                -> KEEP
    ""    -> bool("")    = False  (empty string, falsy)          -> DROP
    "hi"  -> bool("hi")  = True   (non-empty string, truthy)      -> KEEP
    None  -> bool(None)  = False  (falsy)                          -> DROP
    5     -> bool(5)     = True                                     -> KEEP

    result: [1, "hi", 5]
```

This is a genuinely nice, concrete payoff of having internalized the fundamentals doc's truthiness rules early — `filter(None, ...)`'s behavior isn't a separate rule to memorize, it's a direct, mechanical application of the exact same "what counts as falsy" list you already know cold.

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

### Running every one of these for real, including the exact `TypeError` the doc alludes to

**Real, verified output:**

```python
print(reduce(lambda acc, x: acc + x, nums))
print(reduce(lambda acc, x: acc + x, nums, 100))
print(reduce(lambda acc, x: acc + x, [], 0))
try:
    reduce(lambda acc, x: acc + x, [])
except TypeError as e:
    print("TypeError:", e)
```

```
10
110
0
TypeError: reduce() of empty iterable with no initial value
```

That last line is the real, verified proof behind the doc's parenthetical claim ("an empty list with NO starting value would raise `TypeError` instead") — `reduce([], 0)` (with an explicit start) safely returns `0`, while `reduce([])` (no start, and nothing in the list to use as a first accumulator either) has genuinely nothing to return and nothing to combine, so it raises rather than silently guessing.

**Flow diagram — the accumulator threading through, drawn as an explicit chain, for `reduce(lambda acc, x: acc + x, nums, 100)`:**

```
nums = [1, 2, 3, 4],  start = 100

    acc starts as the EXPLICIT start value this time, not nums[0]:
        acc = 100

    step 1: x = 1  →  func(100, 1) = 101   →  acc becomes 101
    step 2: x = 2  →  func(101, 2) = 103   →  acc becomes 103
    step 3: x = 3  →  func(103, 3) = 106   →  acc becomes 106
    step 4: x = 4  →  func(106, 4) = 110   →  acc becomes 110

    nums itself is walked ONE full time through (all 4 elements
    used as "x"), unlike the no-start version which used nums[0]
    AS the initial acc and only walked the REMAINING 3 elements as
    "x" — this is the real, mechanical reason an explicit start is
    "safer and clearer": it decouples "what value do I begin
    accumulating from" from "which elements of the sequence actually
    get combined," which otherwise silently overlap when you let
    the first element serve double duty.

    result: 110
```

## 9. `sorted()` with `key=` — functional-style customization, not full functional tools, but the same spirit

```python
words = ["banana", "fig", "apple", "kiwi"]
sorted(words, key=len)                    # ['fig', 'kiwi', 'apple', 'banana'] — sorted by LENGTH, not alphabetically
sorted(words, key=lambda w: w[-1])   # sorted by each word's LAST letter
```

`key=` takes a function, applies it to every item first, and sorts based on *those results* rather than the items themselves — this is the same "pass a function in as configuration" idea as `map`/`filter`, worth grouping mentally with them even though `sorted` isn't purely a "functional tool" in the same textbook sense.

### Running both for real

**Real, verified output:**

```
['fig', 'kiwi', 'apple', 'banana']
['banana', 'apple', 'fig', 'kiwi']
```

**Flow diagram — what `key=` actually computes before sorting even happens, for the last-letter example:**

```
words = ["banana", "fig", "apple", "kiwi"]
key=lambda w: w[-1]

Step 1: apply the key function to EVERY word FIRST, building an
        invisible parallel list of sort keys (this doesn't happen
        as a separate visible step in your code, but it's exactly
        what sorted() does internally):

    "banana" -> w[-1] = "a"
    "fig"    -> w[-1] = "g"
    "apple"  -> w[-1] = "e"
    "kiwi"   -> w[-1] = "i"

Step 2: sort the ORIGINAL words, but using these COMPUTED keys to
        decide order, not the words' own natural alphabetical order:

    keys in alphabetical order:  "a" < "e" < "g" < "i"
    corresponding words:      "banana" < "apple" < "fig" < "kiwi"

    result: ['banana', 'apple', 'fig', 'kiwi']
```

This "compute a key for every item once, then sort by that" strategy is also why `key=` is far more efficient than manually writing a custom comparison function for every pair of items — `len` or the lambda only ever runs once per item (`n` times total for `n` items), not once per *comparison* (which would be closer to `n log n` times) — a small but real performance detail worth knowing if it comes up.

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

### Running this for real, and looking directly at what a `partial` object actually stores

**Real, verified output:**

```python
print(square(5))
print(cube(5))
print(square)
print(square.func, square.args, square.keywords)
```

```
25
125
functools.partial(<function power at 0x7f0db0b984a0>, exponent=2)
<function power at 0x7f0db0b984a0> () {'exponent': 2}
```

That last line is worth pausing on directly: `square` isn't a closure-based function the way every decorator's `wrapper` has been — it's a real, distinct `functools.partial` object (confirmed by `print(square)` itself showing `functools.partial(...)`, not `<function ...>`), and it has its own inspectable attributes: `.func` (the original `power`), `.args` (any pre-filled *positional* arguments — empty here, since `exponent=2` was pre-filled as a *keyword*), and `.keywords` (the pre-filled keyword arguments — `{'exponent': 2}`).

**Flow diagram — what happens, mechanically, when `square(5)` is finally called, tracing how the pre-filled and freshly-supplied arguments get merged:**

```
square = partial(power, exponent=2)

    Stores, without calling power AT ALL yet:
        .func = power
        .args = ()                  (no positional pre-fills given)
        .keywords = {'exponent': 2}

square(5)

    THIS is the moment power actually gets called. partial's own
    __call__ (yes — partial is ANOTHER real-world example of the
    __call__-based, class-based callable mechanism from the
    decorators doc's §7) combines:
        - the pre-filled args/keywords stored on the partial object
        - PLUS whatever new arguments were just passed to square(5)
      into ONE call to the original function:

        power(*(() + (5,)), **{**{'exponent': 2}})
            = power(5, exponent=2)
            = 5 ** 2
            = 25
```

The reason `partial` is described as "distinct from decorators" despite clearly reusing familiar machinery (closures/`__call__`): a decorator's whole purpose is to change *what happens* when a function runs (add timing, logging, retries) while typically preserving its call signature; `partial`'s whole purpose is to change *what arguments* a function receives, while leaving its actual logic (`base ** exponent`) completely untouched — `square` and `cube` still ultimately run the exact same `power` function body, just pre-supplied with a different fixed `exponent` each time.

## 11. `any()` and `all()` — quick boolean checks over an iterable, often paired with a generator expression

```python
nums = [2, 4, 6, 8]
all(x % 2 == 0 for x in nums)     # True — every element even
any(x > 100 for x in nums)          # False — none exceed 100
```

Note the generator expression passed directly, no square brackets — `all()`/`any()` only need to look at values one at a time and can stop as soon as the answer is decided (`any` stops at the first `True`; `all` stops at the first `False`), so a generator expression here avoids building the full list of booleans in memory first, same efficiency argument as the generators doc.

### Running this for real, and proving the short-circuit claim with actual evidence, not just the assertion

**Real, verified output**, the doc's own two lines:

```
True
False
```

**Real, verified proof of the short-circuit claim** — wrapping the check in a function that announces every time it's actually called, to see with your own eyes exactly when `any()` stops asking:

```python
nums = [2, 4, 6, 8]

def loud(x):
    print("checking", x)
    return x > 4

print(any(loud(x) for x in nums))
```

```
checking 2
checking 4
checking 6
True
```

This is the concrete evidence: there are **four** elements in `nums`, but `loud()` was only called **three** times — `8` was never checked at all, because `any()` already found its `True` (at `6 > 4`) and stopped immediately, never even pulling the fourth value out of the generator expression. If `any()` weren't short-circuiting, you'd see `checking 8` too, every time, regardless of what came before it.

**Flow diagram — `any()`'s stopping rule, traced against the generator's own pause/resume mechanics from the generators doc (this is a real, direct application of that exact mechanism, not a separate feature):**

```
any(loud(x) for x in nums)

    "loud(x) for x in nums" is a GENERATOR EXPRESSION — it produces
    ONE value at a time, on demand, exactly like every generator in
    the generators doc. any() drives it with repeated next() calls,
    checking each result as it arrives:

    next() call 1: x=2  → loud(2) prints "checking 2", returns False
                   any() sees False -> "not decided yet, keep going"
    next() call 2: x=4  → loud(4) prints "checking 4", returns False
                   any() sees False -> keep going
    next() call 3: x=6  → loud(6) prints "checking 6", returns True
                   any() sees True -> "DECIDED — answer is True" ->
                   STOPS calling next() entirely, right here
    (x=8 is NEVER pulled from the generator at all — the generator
     sits there, still holding it, never asked for it)

    any() returns True
```

This is exactly why the doc recommends a generator expression over a list comprehension here: `all(... for x in nums)` inside square brackets — `[x % 2 == 0 for x in nums]` — would force Python to compute *every single* boolean up front, materializing a whole list, before `any`/`all` even started looking at the first one; the parenthesis-less generator form lets `any`/`all` stop pulling new values the instant the answer is already certain, which the `loud()` demonstration above proves is a real, observable difference in behavior, not just a memory optimization that happens to not matter for output.

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
