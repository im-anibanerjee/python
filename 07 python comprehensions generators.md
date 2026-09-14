# Topic 6 — Comprehensions, Generators & Iterators

*Phase 1, Intermediate group — item 3 of 6. This one connects directly back to `csv.DictReader` from Topic 3 — the "notepad cursor" analogy comes back for real here, this time from the inside.*

---

## 1. List comprehensions, past the basics

You've been writing these since Topic 2:

```python
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

Two things worth adding now. First, nested comprehensions — flattening a list of lists:

```python
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [num for row in matrix for num in row]     # [1,2,3,4,5,6,7,8,9]
```

Read the `for` clauses left to right, same order you'd write nested loops: `for row in matrix` (outer), `for num in row` (inner). It's genuinely equivalent to:

```python
flat = []
for row in matrix:
    for num in row:
        flat.append(num)
```

Second, the walrus operator (`:=`, Python 3.8+) inside a comprehension — lets you compute something once and both filter on it and use it, instead of computing it twice:

```python
data = [1, -4, 9, -16, 25]
# without walrus - compute sqrt logic twice, or restructure awkwardly
# with walrus:
results = [y for x in data if (y := x**0.5 if x >= 0 else None) is not None]
```

Don't force the walrus in everywhere — it's genuinely useful when a comprehension needs to both filter and reuse a computed value, but readability loses if you reach for it out of habit.

### Running every one of these for real

**Real, verified output:**

```python
squares = [x**2 for x in range(10)]
print(squares)
evens = [x for x in range(20) if x % 2 == 0]
print(evens)

matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [num for row in matrix for num in row]
print(flat)

data = [1, -4, 9, -16, 25]
results = [y for x in data if (y := x**0.5 if x >= 0 else None) is not None]
print(results)
```

```
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
[1, 2, 3, 4, 5, 6, 7, 8, 9]
[1.0, 3.0, 5.0]
```

**Flow diagram — the walrus example, traced element by element (this is the one worth slowing down for, since two things are happening on one line):**

```
data = [1, -4, 9, -16, 25]

[y for x in data if (y := x**0.5 if x >= 0 else None) is not None]

For EACH x, two things happen INSIDE the `if` clause, before the
comprehension even decides whether to keep this element:

    1. compute  x**0.5 if x >= 0 else None   — a ternary (from the
       fundamentals doc), giving either a real square root or None
    2. ASSIGN that result to y via the walrus (:=), AND simultaneously
       produce that same value as the condition being tested by `if`

x=1:    x>=0? yes -> y := 1**0.5 = 1.0   -> "is y is not None?" True  -> KEEP, append y (1.0)
x=-4:   x>=0? no  -> y := None            -> "is y is not None?" False -> DROP
x=9:    x>=0? yes -> y := 9**0.5 = 3.0   -> True  -> KEEP (3.0)
x=-16:  x>=0? no  -> y := None            -> False -> DROP
x=25:   x>=0? yes -> y := 25**0.5 = 5.0  -> True  -> KEEP (5.0)

result: [1.0, 3.0, 5.0]
```

The reason this needs a walrus at all, rather than just writing `[x**0.5 for x in data if x >= 0]`, is subtle but real: that simpler version would recompute `x**0.5` — but more importantly, in a case where the "compute once, use for both the filter and the output" value is expensive or has side effects, writing it twice (once in the `if`, once in the expression) means doing that work twice for every single element. The walrus computes it exactly once per element and reuses that one result for both the filtering decision and the value that gets appended — which is precisely the doc's framing: "compute something once and both filter on it and use it."

## 2. Dict and set comprehensions, briefly revisited

```python
word_lengths = {word: len(word) for word in ["a", "bb", "ccc"]}     # {'a': 1, 'bb': 2, 'ccc': 3}
unique_lengths = {len(word) for word in ["a", "bb", "ccc", "dd"]}    # {1, 2, 3}
```

Same mental model as list comprehensions — just different brackets and, for dicts, a `key: value` expression instead of a single expression.

### Running these for real

**Real, verified output:**

```
{'a': 1, 'bb': 2, 'ccc': 3}
{1, 2, 3}
```

Worth noticing on the second line: `["a", "bb", "ccc", "dd"]` has *four* words, but `unique_lengths` only has *three* elements — `"ccc"` (length 3) and `"dd"` (length 2)... wait, tracing precisely: lengths are `1, 2, 3, 2` — the two words of length 2 (`"bb"` and `"dd"`) collapse into a single `2` in the resulting set, exactly the same "duplicates silently absorbed" mechanism from the collections doc's set section. A set comprehension inherits set semantics fully — it's not a special case, it's a completely ordinary set, just built with comprehension syntax instead of a literal or a call to `set()`.

## 3. Generator expressions — the one-character change that means everything

Swap the square brackets for parentheses and a list comprehension becomes a **generator expression**:

```python
squares_list = [x**2 for x in range(1_000_000)]     # builds the ENTIRE list in memory, right now
squares_gen  = (x**2 for x in range(1_000_000))     # builds NOTHING yet — just a promise to compute values one at a time
```

This is the single most important idea in this whole doc: a list comprehension computes and stores every value immediately; a generator expression computes nothing until you actually ask for the next value, and it only ever holds *one value at a time* in memory, not all of them.

```python
import sys
print(sys.getsizeof(squares_list))   # a large number - proportional to 1,000,000 items
print(sys.getsizeof(squares_gen))    # a small, fixed number - a generator object, not the data
```

The real tradeoff: a generator is dramatically cheaper in memory for large or unbounded sequences, but you pay for that by only being able to walk through it **once, forward, no peeking backward** — exactly the `csv.DictReader` behavior from Topic 3. Once exhausted, it's empty forever:

```python
gen = (x**2 for x in range(5))
print(list(gen))      # [0, 1, 4, 9, 16] - consumes it entirely
print(list(gen))      # [] - already exhausted, nothing left, no error, just empty
```

This is a genuinely common real bug: someone iterates a generator once (say, to check something), then tries to iterate it again expecting the same data, and silently gets nothing. A `list` never has this problem — it can be iterated as many times as you like, because all the data actually sits there in memory the whole time. That's the whole tradeoff in one sentence: **lists trade memory for repeatability; generators trade repeatability for memory.**

### Running the memory comparison and the exhaustion example for real

**Real, verified output** — the exact sizes on this machine, for a full million-element list versus its generator equivalent:

```
8448728
208
```

That's roughly **40,600x** smaller for the generator (208 bytes — a small, fixed size, completely independent of whether the range is 1,000,000 or 1,000,000,000,000) versus a list whose size genuinely scales with element count (8.4 MB for a million small integers' worth of pointers). This is the concrete, measured version of "a small, fixed number" and "proportional to 1,000,000 items" from the doc's own comments — not an estimate, the real `sys.getsizeof()` reading.

**Real, verified output** — the exhaustion example:

```
[0, 1, 4, 9, 16]
[]
```

**Flow diagram — what a generator object actually holds internally, which is *why* it can be this small and *why* it empties out permanently:**

```
squares_gen = (x**2 for x in range(1_000_000))

A generator object does NOT contain a list of results anywhere inside
it. It contains only a small, fixed bundle of bookkeeping:
    - a reference to the underlying code (the expression x**2, and
      the iterable being walked, range(1_000_000))
    - a "where am I paused" marker — currently: "haven't started yet"
    - the local state needed to resume (here: essentially just x's
      current position in the range)

That's it — regardless of whether range() has 5 elements or 1 trillion,
this bundle is the same small size, because it never holds more than
"where am I right now."

list(gen)   — first call
    Repeatedly asks the generator for "the next value" until it's
    exhausted. Each time: compute x**2 for the CURRENT x, advance the
    internal position, hand the ONE value back. list() collects each
    one as it arrives, building [0, 1, 4, 9, 16].

    After the 5th value, the underlying range(5) has nothing left —
    the generator's internal "where am I" marker moves to a special
    EXHAUSTED state. This state is PERMANENT — there's no way to
    rewind a generator's cursor back to the start; the position marker
    only ever moves forward, and once it falls off the end, it stays
    "finished" for the rest of that object's life.

list(gen)   — second call, on the SAME gen object
    Asks for "the next value" — but the internal marker already says
    EXHAUSTED. Immediately reports "nothing left" (StopIteration
    internally) without recomputing or re-walking anything.
    list() of "nothing left, immediately" is just []  — not an error,
    just an empty result.
```

The genuinely common real bug the doc calls out — check something with one pass, then iterate again expecting the same data — happens precisely because a generator gives no visual signal that it's "used up." Unlike an empty list, which you can `print()` and see is `[]`, a generator that's been exhausted still looks like a perfectly normal generator object; the only way to discover it's spent is to actually try to pull a value from it and get nothing.

## 4. Generator functions — `yield` instead of `return`

A generator expression is a one-liner. For anything with real logic, you write a **generator function** — a normal-looking function that uses `yield` instead of (or alongside) `return`:

```python
def count_up_to(n):
    i = 1
    while i <= n:
        yield i
        i += 1

gen = count_up_to(5)
print(gen)          # <generator object count_up_to at 0x...> - calling it does NOT run the function body yet!
print(next(gen))    # 1
print(next(gen))    # 2
print(list(gen))     # [3, 4, 5] - list() drains the rest
```

This is the part that actually confuses people, so slow down here: calling `count_up_to(5)` does **not** execute a single line inside the function. It just creates a generator object, primed and ready. The function body only starts running the moment you call `next()` on it (or iterate it with a `for` loop, which calls `next()` under the hood repeatedly).

Here's the real mechanics of `yield`, traced step by step:

```python
def demo():
    print("A")
    yield 1
    print("B")
    yield 2
    print("C")

g = demo()          # nothing printed yet - function hasn't started
print(next(g))       # prints "A", then yields 1 and PAUSES right there -> prints 1
print(next(g))       # RESUMES exactly where it paused, prints "B", yields 2, pauses -> prints 2
print(next(g))       # RESUMES after the second yield, prints "C", falls off the end -> raises StopIteration
```

`yield` doesn't just "return a value" — it **pauses the entire function's execution state** (every local variable, the exact line it was on) and hands a value back to whoever called `next()`. The next time `next()` is called, execution resumes from exactly that paused line, with all local state intact, as if nothing happened in between. This is fundamentally different from `return`, which ends the function permanently — a generator function can `yield` many times across many separate `next()` calls, each one picking up exactly where the last left off.

When a generator function finally finishes (falls off the end, or hits an explicit `return`), calling `next()` one more time raises `StopIteration` — this is exactly what a `for` loop is catching silently for you every time you loop over anything.

### Running both examples for real, including the `StopIteration`

**Real, verified output**, first `count_up_to`:

```
<generator object count_up_to at 0x7faa7ed201e0>
1
2
[3, 4, 5]
```

Confirmed: `print(gen)` shows a generator object, not `1` (the first value) — proving the function body genuinely hasn't run at all yet, exactly as the doc states.

**Real, verified output**, the `demo()` trace, extended one more call to actually witness the `StopIteration`:

```python
g = demo()
print(next(g))
print(next(g))
try:
    print(next(g))
except StopIteration:
    print("StopIteration raised")
```

```
A
1
B
2
C
StopIteration raised
```

**Flow diagram — the pause/resume mechanics, drawn as a single timeline with explicit "frozen" markers:**

```
g = demo()
    Generator object created. Execution position: BEFORE the first
    line of the function body. NOTHING has run.

next(g)  call #1
    Execution resumes from "the very beginning":
        print("A")          → prints "A"
        yield 1              → FREEZES here, execution position now
                                 marked exactly at this yield statement,
                                 with EVERY local variable's value
                                 preserved exactly as it was
    next() returns the value 1  →  print(next(g)) prints 1

next(g)  call #2
    Execution RESUMES from the EXACT frozen point — not from the top
    of the function again:
        print("B")           → prints "B"     (this is why "B" comes
                                                  AFTER the first "1"
                                                  was already printed,
                                                  not before)
        yield 2               → FREEZES here
    next() returns 2  →  print(next(g)) prints 2

next(g)  call #3
    Resumes from after the second yield:
        print("C")           → prints "C"
        (function body ENDS — falls off the end, no more yields, no
         explicit return)
    → this is treated exactly like reaching the end of ANY function
      with no return value, EXCEPT that for a generator, "the
      function is now completely done" is signaled by raising
      StopIteration instead of quietly returning None
```

The one-sentence version worth memorizing: **each `next()` call doesn't restart the function — it un-pauses it, continuing from the precise line and variable state where the previous `next()` left off, and `yield` is the pause button, not the exit button `return` is.**

### `yield` is two-way — receiving values back in, not just sending them out

`yield` doesn't only hand a value *out*; the exact spot where it pauses can also *receive* a value back in, the next time the generator is resumed. A bare assignment like `x = yield 1` isn't "assign 1 to x" — it's "yield 1 out, freeze right here mid-statement, and whatever value comes back in when resumed becomes x."

```python
def gen():
    print("start")
    x = yield 1
    print(f"received: {x}")
    yield 2

g = gen()
print(next(g))
print(next(g))
'''
start
1
received: None
2
'''
```

Think of the generator as someone reading this script out loud, who freezes solid the instant they read the word `yield`, and only keeps reading — from that exact frozen word — when you tap them on the shoulder (`next()`). Anything they say while reading happens automatically, as a side effect of that tap; the only thing you actually catch yourself is the one value they hand you the moment they freeze.

Traced call by call:

- **`next(g)` #1** — starts the function from the top. Prints `start`. Reaches `x = yield 1`: sends `1` out and freezes *mid-statement*, before the assignment to `x` has actually happened. `next()` returns that `1`.
- **`next(g)` #2** — resumes from exactly that frozen spot. `next()` always resumes by handing back `None` (it's shorthand for `g.send(None)`), so the frozen assignment finally completes as `x = None`. Execution continues: prints `received: None`. Reaches `yield 2`: sends `2` out and freezes again. `next()` returns that `2`.

That's why the output is `start`, `1`, `received: None`, `2` — two of those lines are values you explicitly printed (`1`, `2`, from `print(next(g))`), and two are things the generator printed automatically *while running toward* those freeze points (`start`, `received: None`).

If you resume with `g.send("hello")` instead of `next(g)`, that same frozen spot completes as `x = "hello"` instead of `x = None` — this two-way "send a value back in" mechanism is exactly what makes generators the foundation for coroutines, which comes back around in the `asyncio` doc later.

```python
'''
next(g) runs the generator until it hits a yield
anything printed along the way happens automatically, as a side effect
it stops only at yield, and hands back that value

like a person reading a script out loud
they freeze the instant they hit "yield"
resume only when tapped again with next()
whatever they say while reading is automatic, not asked for separately
the only thing print(next(g)) shows is the note handed at the freeze point
'''
```

### Running the `next(g)` version and the `g.send(...)` version side by side, for real proof of the two-way claim

**Real, verified output**, `next(g)` twice (matches the doc's comment block exactly):

```
start
1
received: None
2
```

**Real, verified output**, replacing the second call with `g.send("hello")` instead — this is the direct, hands-on proof of the "if you resume with `g.send(...)` instead" claim:

```python
g = gen()
print(g.send(None))       # equivalent to next(g) — starts the generator; "None" is what would be assigned to x if this were a resume, but there's nothing paused yet to resume, so it's ignored on this first call
print(g.send("hello"))     # THIS resumes the frozen "x = yield 1", completing it as x = "hello"
```

```
start
1
received: hello
2
```

The only difference between the two runs is that single line — `received: None` versus `received: hello` — and it's a direct, mechanical consequence of what value was handed back in at the exact moment the frozen `x = yield 1` was resumed. `next(g)` is genuinely nothing more than shorthand for `g.send(None)` — there is no separate, different resumption mechanism; `next()` just always resumes with the specific value `None`, while `.send(value)` lets you choose what comes back in.

## 5. `yield from` — delegating to another generator

```python
def inner():
    yield 1
    yield 2

def outer():
    yield "start"
    yield from inner()      # yields everything inner() yields, one at a time, as if inlined
    yield "end"

print(list(outer()))    # ['start', 1, 2, 'end']
```

Without `yield from`, you'd have to manually loop and re-yield: `for x in inner(): yield x` — `yield from` is just the clean, built-in way to say that. You'll see this pattern in real generator-heavy code (parsers, tree traversals) constantly.

### Running this for real

**Real, verified output:**

```
['start', 1, 2, 'end']
```

**Flow diagram — `yield from inner()` as a single pause/resume timeline spanning TWO functions, not one:**

```
list(outer())   drives outer()'s generator with repeated next() calls,
                  exactly like §4's mechanics — just tracking WHICH
                  function is currently "frozen" at each step:

next() call 1:
    outer() starts, runs  yield "start"  → freezes in OUTER
    → 'start' collected

next() call 2:
    outer() resumes, reaches  yield from inner()
    → this doesn't just call inner() and grab one value — it hands
      control ENTIRELY over to inner()'s own generator, as if outer's
      code had been physically replaced by inner's, right at this line
    → inner() starts fresh, runs  yield 1  → freezes in INNER
    → 1 collected

next() call 3:
    since outer is currently "delegating" to inner, this next() goes
    straight to INNER, resuming exactly where IT was frozen:
    → inner() resumes, reaches  yield 2  → freezes in INNER again
    → 2 collected

next() call 4:
    inner() resumes, has no more yields, falls off the end → inner
    is FINISHED. Control returns automatically to OUTER, resuming
    right after the "yield from inner()" line:
    → outer() continues:  yield "end"  → freezes in OUTER
    → 'end' collected

next() call 5:
    outer() resumes, falls off the end → StopIteration → list()
    knows to stop collecting
```

The manual equivalent — `for x in inner(): yield x` — makes this delegation explicit as an actual loop; `yield from` does exactly the same thing but also correctly forwards a few more advanced details (like `.send()` values and the delegated generator's eventual `return` value) that a hand-written loop would silently get wrong. For the everyday case shown here, both produce identical output — `yield from` is just the shorter, more complete way to write it.

## 6. Iterators and iterables — the protocol underneath all of this

This is the concept `csv.DictReader` was already demonstrating back in Topic 3, made explicit. Two related but distinct ideas:

An **iterable** is anything you can call `iter()` on — anything usable in a `for` loop (`list`, `dict`, `str`, a generator, a file object...). It implements `__iter__`.

An **iterator** is the actual "cursor" object doing the walking — it implements `__next__` (returning the next value, or raising `StopIteration` when done) and *also* `__iter__` (which just returns itself, by convention).

```python
nums = [1, 2, 3]          # nums is ITERABLE
it = iter(nums)             # this gives you the ITERATOR - the actual cursor
print(next(it))             # 1
print(next(it))             # 2
print(next(it))             # 3
print(next(it))             # StopIteration!
```

A `for` loop is doing exactly this mechanically: call `iter()` once on whatever you're looping over to get an iterator, then call `next()` on that iterator repeatedly, catching `StopIteration` to know when to stop. Every generator you write with `yield` is automatically both an iterable and an iterator — Python builds the `__iter__`/`__next__` machinery for you. You can also build this by hand on your own class:

```python
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self            # I AM my own iterator

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

for n in Countdown(3):
    print(n)          # 3, 2, 1
```

`__iter__` is what a `for` loop calls once, right at the start, to get "the thing that will actually do the walking" (the iterator). Here it just `return self` — meaning "I am my own iterator, don't go looking for a separate object, this same instance handles both roles."

`__next__` is what the `for` loop then calls repeatedly, once per loop iteration, to get the next value. It must do one of two things every time: return the next value, or raise `StopIteration` to say "there's nothing left, stop looping."

```python
    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1
        '''
        can also be written as:
        value = self.current      # grab the value before changing anything
        self.current -= 1          # then update state for next time
        return value                 # return what was grabbed, untouched
        '''
```

Same output either way — the second version is just easier to read on a first pass, since nothing has to be mentally "undone" to see what gets returned.

This is genuinely the same mechanism as `csv.DictReader` — it's a class implementing exactly this `__iter__`/`__next__` pair, which is why it behaved like "a cursor that only moves forward" back in Topic 3. Now you know precisely why.

### Running both examples for real, and proving `nums` and `it` are genuinely different kinds of things

**Real, verified output** — the `iter()`/`next()` example, extended to actually confirm the iterable-vs-iterator distinction directly, rather than just asserting it:

```python
nums = [1, 2, 3]
it = iter(nums)
print(next(it))
print(next(it))
print(next(it))
try:
    print(next(it))
except StopIteration:
    print("StopIteration!")

print("is nums an iterator too?", hasattr(nums, "__next__"))
print("is it an iterator?", hasattr(it, "__next__"))
print(iter(it) is it)
```

```
1
2
3
StopIteration!
is nums an iterator too? False
is it an iterator? True
True
```

This is real, direct proof of the distinction the doc draws: `nums` (the list) genuinely does **not** have a `__next__` method at all — a list is an *iterable* (it knows how to *produce* an iterator via `__iter__`), but it is not itself a *cursor*. `it` (what `iter(nums)` returned) genuinely **does** have `__next__` — it's the actual cursor object. `iter(it) is it` being `True` confirms the "an iterator's own `__iter__` just returns itself" convention mentioned in the doc — asking an iterator "give me an iterator over yourself" just hands back itself, unchanged.

**Flow diagram — why `list(some_list)` can be looped over many times, but the iterator `iter(some_list)` gives you cannot:**

```
nums = [1, 2, 3]      ← ONE object, holds the actual data permanently

for n in nums: ...     (first time)
    → Python calls iter(nums) → creates a BRAND NEW iterator object,
      with its own internal position counter starting at 0
    → walks it to completion, discards that iterator afterward

for n in nums: ...     (second time, same nums)
    → Python calls iter(nums) AGAIN → creates ANOTHER BRAND NEW
      iterator object, again starting at position 0
    → this is why looping over the SAME list twice works fine: nums
      itself is untouched by either loop; each loop gets its OWN
      fresh cursor

it = iter(nums)         ← now YOU are holding onto one specific
                            cursor object directly, instead of letting
                            a for loop create and discard one silently
next(it); next(it); next(it)
    → advances THIS ONE cursor's position: 0 -> 1 -> 2 -> 3
    → once at 3 (the end), calling next(it) again raises
      StopIteration — and asking for iter(it) again (as a for loop
      would do internally) just returns THIS SAME exhausted cursor,
      not a fresh one — there is no "reset" operation available
```

This is the precise mechanical reason lists are safely re-iterable while a *specific iterator object* isn't: a `for` loop over a list is *always* implicitly requesting a fresh cursor via `iter()`, discarding it when the loop ends; the "exhaustion" problem from §3 only bites you when you manually grab and hold onto one particular iterator (or a generator, which — unlike a list — behaves as its *own* iterator, so there's no fresh cursor to be handed out a second time at all).

### Running the `Countdown` class for real, and confirming it's genuinely its own iterator

**Real, verified output:**

```python
for n in Countdown(3):
    print(n)

c = Countdown(2)
it1 = iter(c)
print(it1 is c)
```

```
3
2
1
True
```

`it1 is c` printing `True` is the direct proof of "I am my own iterator" — calling `iter(c)` didn't build a separate cursor object at all, it just handed back `c` itself, exactly as `__iter__`'s `return self` says to do.

## 7. `itertools` — worth knowing exists, not memorizing cold

The standard library's `itertools` module has a set of tools for exactly this kind of lazy, memory-efficient iteration:

```python
from itertools import chain, islice, count

list(chain([1, 2], [3, 4]))         # [1, 2, 3, 4] - chains iterables together without building an intermediate combined list
list(islice(range(1000000), 5))       # [0, 1, 2, 3, 4] - takes just the first 5, without ever materializing the full range as a list
counter = count(10)                     # an INFINITE generator: 10, 11, 12, 13... forever
list(islice(counter, 3))                 # [10, 11, 12] - islice is what makes working with an infinite generator safe
```

`islice` is worth remembering specifically — it's the safe way to pull a limited number of items out of a generator (even an infinite one) without accidentally trying to convert the whole thing to a `list` and hanging forever.

### Running this for real, including proof `count()` really is infinite (by pulling one more value manually afterward)

**Real, verified output:**

```python
from itertools import chain, islice, count

print(list(chain([1, 2], [3, 4])))
print(list(islice(range(1000000), 5)))
counter = count(10)
print(list(islice(counter, 3)))
print(next(counter))
```

```
[1, 2, 3, 4]
[0, 1, 2, 3, 4]
[10, 11, 12]
13
```

That final `next(counter)` printing `13` (not an error, not a repeat) is worth pointing at directly: `islice(counter, 3)` consumed exactly `10, 11, 12` from `counter` and then stopped — `counter` itself is a genuinely never-ending generator that has no concept of "done," so asking it for one more value after `islice` finished simply continues exactly where it left off, `13`, and would keep going forever if you kept asking. This is the real, concrete meaning of "infinite generator": there's no upper bound baked into `count()` at all, only whatever *you* choose to stop at, which is exactly the job `islice` does safely — it stops *pulling*, it doesn't (and can't) tell the underlying generator to stop *existing*.

**Flow diagram — why `list(islice(range(1000000), 5))` never actually builds a million-element list, even briefly:**

```
islice(range(1000000), 5)

    This does NOT first materialize range(1000000) into anything,
    and does NOT ask range for "the first 5 elements" as a batch
    operation either. It wraps range(1000000)'s iterator with a
    small counter of its own: "I will forward AT MOST 5 next() calls
    to the underlying iterator, then raise StopIteration myself,
    regardless of how much more the underlying iterator could
    still produce."

    list(...) then drives THAT wrapper with next() calls:
        call 1 -> islice forwards to range's iterator -> 0 -> islice's
                  internal counter: 1 of 5 used
        call 2 -> forwards -> 1 -> counter: 2 of 5
        call 3 -> forwards -> 2 -> counter: 3 of 5
        call 4 -> forwards -> 3 -> counter: 4 of 5
        call 5 -> forwards -> 4 -> counter: 5 of 5 -> reached limit
        call 6 -> islice raises StopIteration itself, WITHOUT even
                  asking range's iterator for anything — range(1000000)
                  never gets asked for its 6th, 7th, ...1000000th value
                  at all

    → at no point does a 1,000,000-element list (or any structure
      even close to that size) ever exist in memory — only ever one
      value at a time, exactly like every other generator-based tool
      in this doc.
```

### Getting just one element, not the whole thing

A generator has no indexing at all — `gen[0]` raises `TypeError: 'generator' object is not subscriptable`. That's not a missing feature, it's a direct consequence of how generators work: there's no way to know what's at "position 5" without first walking through positions 0-4, and once you've walked past a position you can't get it back.

To get just the **first** element, `next()` is exactly that:

```python
gen = squares_up_to(5)
first = next(gen)     # consumes just that one element, leaves the rest untouched
```

To get a **specific later element** without materializing everything in between, `islice` does it without building any intermediate list:

```python
from itertools import islice

gen = squares_up_to(5)
third = next(islice(gen, 2, 3))    # skip 2, take the next 1 -> the element at index 2
```

This still **consumes** everything up through that point on the original `gen` — there's no way to jump to index `2` without passing through `0` and `1` first, the one-way-cursor rule again. If you need to access several specific indices, or the same index more than once, that's a sign you want a `list`, not a generator — convert once with `list(gen)` and index normally from then on.

### Running every piece of this for real, including the `TypeError`

**Real, verified output**, using `squares_up_to(n)` defined as `for x in range(1, n+1): yield x**2`:

```python
gen = squares_up_to(5)
try:
    print(gen[0])
except TypeError as e:
    print("TypeError:", e)

gen = squares_up_to(5)
first = next(gen)
print("first:", first)
print("rest:", list(gen))

gen2 = squares_up_to(5)
third = next(islice(gen2, 2, 3))
print("third:", third)
print("remaining after that:", list(gen2))
```

```
TypeError: 'generator' object is not subscriptable
first: 1
rest: [4, 9, 16, 25]
third: 9
remaining after that: [16, 25]
```

**Flow diagram — `next(islice(gen2, 2, 3))`, traced as an actual sequence of consumption, to make "this still consumes everything up through that point" concrete rather than abstract:**

```
squares_up_to(5) would yield, if fully drained: 1, 4, 9, 16, 25
                                                 (indices: 0, 1, 2, 3, 4)

islice(gen2, 2, 3)   means "skip the first 2 values, then yield
                       exactly 1 more, then stop" — but "skip" here
                       doesn't mean "know how to jump ahead" — it
                       means "pull and DISCARD 2 values first":

    internally:
        pull value at index 0 (=1)  -> DISCARD (this is the "skip 2" part)
        pull value at index 1 (=4)  -> DISCARD
        pull value at index 2 (=9)  -> THIS is the one islice yields
        (then islice itself stops, having yielded its 1 requested item)

next(...)  grabs that one yielded value -> third = 9

list(gen2)   afterward — gen2's cursor position is now sitting AFTER
              index 2 (the values at indices 0, 1, and 2 have all
              already been pulled out of the underlying generator,
              two of them silently discarded by islice, one handed
              to you) — so draining the rest only gives what's LEFT:
              indices 3 and 4  ->  [16, 25]
```

This is the direct, working proof of "there's no way to jump to index 2 without passing through 0 and 1 first" — the values at indices 0 and 1 were genuinely computed and then thrown away, not skipped over for free; `squares_up_to`'s `yield x**2` line really did execute for `x=1` and `x=2` before `islice` ever handed anything back to you.

## 8. When to reach for which — the practical decision

Use a **list** (or list comprehension) when you need to iterate more than once, need random access by index, need `len()` up front, or the data is small enough that memory isn't a real concern.

Use a **generator** (expression or function) when the data is large or unbounded, you only need to walk through it once, front to back, and you want to start processing before the whole thing is even computed — this matters a lot once you hit the ETL/Pandas phase later, where you'll process files far too large to load entirely into memory at once.

---

## Practice questions

1. **Predict, then verify.** What does this print, and why, tracing through the `yield` pause/resume mechanics explicitly:
   ```python
   def gen():
       print("start")
       x = yield 1
       print(f"received: {x}")
       yield 2

   g = gen()
   print(next(g))
   print(next(g))
   ```
   (Hint: a bare `x = yield 1` can also *receive* a value if someone calls `g.send(value)` instead of `next(g)` — but with a plain `next(g)`, what does `x` end up being? Look this up if you get stuck; it's a genuinely subtle corner of `yield`.)

2. **Exhaustion bug, on purpose.** Write a generator function `squares_up_to(n)` that yields `x**2` for `x` in `1..n`. Assign it to a variable, convert it to a `list` once, then try converting the *same* variable to a `list` a second time. Explain what you get and why — tie your explanation to the "notepad cursor" idea from Topic 3.

3. **Memory comparison.** Using `sys.getsizeof`, compare the size of a list comprehension building squares of the first 100,000 integers against the size of the equivalent generator expression. Report the actual numbers you get.

4. **Build your own iterator.** Write a class `EvenNumbers(limit)` that, when iterated with a `for` loop, yields even numbers starting from 0 up to (not including) `limit`. Implement it with `__iter__`/`__next__` by hand (don't just use `yield` inside a method — build the actual protocol, so you feel the mechanics). Confirm `list(EvenNumbers(10))` gives `[0, 2, 4, 6, 8]`.

5. **`yield from`.** Write a generator `flatten(nested)` that takes a list which may contain a mix of plain items and sub-lists (only one level deep, e.g. `[1, [2, 3], 4, [5]]`) and yields every individual item in order, flattened. Use `yield from` for the sub-list case.

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for decorators.*
