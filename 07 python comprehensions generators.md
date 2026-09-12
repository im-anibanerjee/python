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

## 2. Dict and set comprehensions, briefly revisited

```python
word_lengths = {word: len(word) for word in ["a", "bb", "ccc"]}     # {'a': 1, 'bb': 2, 'ccc': 3}
unique_lengths = {len(word) for word in ["a", "bb", "ccc", "dd"]}    # {1, 2, 3}
```

Same mental model as list comprehensions — just different brackets and, for dicts, a `key: value` expression instead of a single expression.

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
