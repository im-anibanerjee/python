# Topic 7 — Decorators, Deep Dive

*Phase 1, Intermediate group — item 4 of 6. You've already used `@property`, `@classmethod`, `@staticmethod`, and `@dataclass` without fully seeing what a decorator actually is underneath the `@`. This doc is that reveal.*

---

## 1. What a decorator actually is — no magic, just a function

Strip away the `@` syntax for a second. A decorator is just **a function that takes a function as input and returns a function as output** — usually a *new* function that wraps the original with some extra behavior before and/or after calling it.

```python
def shout(func):
    def wrapper():
        print("BEFORE")
        func()
        print("AFTER")
    return wrapper

def say_hello():
    print("hello")

say_hello = shout(say_hello)     # manually "decorating" - reassign the name to the wrapped version
say_hello()
# BEFORE
# hello
# AFTER
```

`@shout` above a function definition is *exactly* the line `say_hello = shout(say_hello)`, just written differently:

```python
@shout
def say_hello():
    print("hello")

say_hello()      # identical output to above
```

That's the entire mechanism. `@decorator_name` right above `def func(): ...` means "after defining `func`, immediately run `func = decorator_name(func)`." Everywhere you've already used `@property`, `@classmethod`, `@abstractmethod` — every single one of them is a function (or callable) that received your method and handed back something else to bind to that name instead.

## 2. A useful one — timing a function

```python
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_square(n):
    time.sleep(0.1)
    return n ** 2

print(slow_square(5))
# slow_square took 0.100xs
# 25
```

Notice `wrapper(*args, **kwargs)` — this is not optional decoration, it's load-bearing. The wrapper has to accept *any* arguments, because it stands in for a function it knows nothing about ahead of time. Without `*args, **kwargs`, this decorator could only ever wrap functions that take zero arguments — `slow_square(5)` would fail immediately, since `wrapper()` wouldn't accept the `5`. `*args`/`**kwargs` get their own full doc soon (Topic 8), but you need enough of them right now to write any decorator that isn't trivial: `*args` collects any number of positional arguments into a tuple, `**kwargs` collects any number of keyword arguments into a dict, and `func(*args, **kwargs)` unpacks them back out to call the original function with whatever it was actually given.

### `func` vs `args`/`kwargs` — passed once at decoration, passed fresh on every call

Easy to conflate these, so separate them explicitly. `func` is a parameter of the **outer** function (`timer`, or `shout` in §1) — it gets a value exactly **once**, at decoration time, when `timer(slow_square)` (or `shout(say_hello)`) actually runs. `wrapper` itself has no `func` parameter in its own signature at all. It reaches `func` through a **closure**: because `wrapper`'s body refers to a name (`func`) that belongs to its enclosing function, Python keeps that enclosing scope alive and attached to `wrapper` even after the outer function has already returned. `func` is effectively taped onto `wrapper` once, and stays there for as long as that particular `wrapper` object exists.

`args`/`kwargs`, by contrast, are parameters of `wrapper` itself, and get a *fresh* value on **every call** — that's the entire reason `*args, **kwargs` exists.

Traced end to end for `timer`:

```
DEFINITION TIME (runs once)
----------------------------
@timer
def slow_square(n): ...

is exactly:
    def slow_square(n): ...
    slow_square = timer(slow_square)     # func = original slow_square, passed ONCE
                                            # timer defines + returns wrapper
                                            # wrapper closes over func
    # slow_square now refers to wrapper, not the original function

CALL TIME (runs every time you call it)
----------------------------------------
slow_square(5)
  = wrapper(5)                    # slow_square IS wrapper now
        args = (5,)  kwargs = {}    # <- passed fresh, this call only
        result = func(*args, **kwargs)     # func reached via closure, NOT passed in again
               = original slow_square(5)
        ...
```

Same story for `shout`/`say_hello` (§1), minus `args`/`kwargs` entirely, since `say_hello` takes no arguments:

```
DECORATION LINE (runs once)
------------------------------
say_hello = shout(say_hello)     # func = original say_hello, passed ONCE
                                   # wrapper closes over func
                                   # say_hello now refers to wrapper

CALL TIME (every call)
------------------------
say_hello()
  = wrapper()                     # say_hello IS wrapper now
        print("BEFORE")
        func()                      # func reached via closure — original say_hello()
        print("AFTER")
```

The pattern to hold onto: whatever the outer decorator function's parameter is called (`func`, here) gets bound exactly once, at decoration time, and lives on inside the inner function purely through closure — never passed to it again. Whatever the inner function's own parameters are (`*args, **kwargs`, or nothing at all if the wrapped function takes nothing) get supplied fresh, on every single call.

## 3. `functools.wraps` — the thing every real decorator needs

Run this and look closely at what gets printed:

```python
def timer(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

@timer
def slow_square(n):
    """Return n squared."""
    return n ** 2

print(slow_square.__name__)      # wrapper  <- WRONG! should say "slow_square"
print(slow_square.__doc__)        # None       <- WRONG! the docstring is gone
```

Once decorated, `slow_square` isn't really `slow_square` anymore — it's `wrapper`, the inner function the decorator defined, wearing `slow_square`'s name on the outside. Every bit of metadata that tooling relies on (`__name__` for error messages and logging, `__doc__` for `help()`, introspection tools, debuggers) now belongs to `wrapper`, not your actual function. This silently breaks debugging, breaks `help(slow_square)`, and breaks any tool that inspects function metadata.

The fix, and it's genuinely a rule with no exceptions — every decorator you write should use `functools.wraps`:

```python
from functools import wraps

def timer(func):
    @wraps(func)                    # copies __name__, __doc__, and other metadata from func onto wrapper
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

@timer
def slow_square(n):
    """Return n squared."""
    return n ** 2

print(slow_square.__name__)      # slow_square  - correct now
print(slow_square.__doc__)        # Return n squared.  - correct now
```

`@wraps(func)` is itself a decorator — applied to `wrapper`, it copies `func`'s identity onto `wrapper` after the fact. This is worth memorizing as a reflex: **if you write `def wrapper(...)` inside a decorator, the very next line should be `@wraps(func)` right above it**, no exceptions, in real code.

## 4. Decorators that take their own arguments

Sometimes you want to configure the decorator itself — e.g. `@retry(times=3)` instead of just `@retry`. This needs one extra layer of function nesting: a function that takes the *decorator's* arguments and *returns* the actual decorator.

```python
from functools import wraps

def repeat(times):                      # OUTER layer: takes the decorator's own argument(s)
    def decorator(func):                  # MIDDLE layer: the actual decorator, takes the function
        @wraps(func)
        def wrapper(*args, **kwargs):       # INNER layer: the actual wrapping logic
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def greet(name):
    print(f"Hello, {name}")

greet("Ani")
# Hello, Ani
# Hello, Ani
# Hello, Ani
```

Read `@repeat(times=3)` as two steps happening in sequence: first, `repeat(times=3)` runs immediately and returns `decorator` (a real decorator function, now with `times` baked into its closure). Second, *that* returned `decorator` is what actually gets applied to `greet`, exactly like `@shout` in §1. Three layers deep is the standard shape for any "decorator with its own settings" — outer takes the settings, middle takes the function, inner does the wrapping.

## 5. Stacking multiple decorators — order matters, and it's easy to get backwards

```python
def bold(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return f"<b>{func(*args, **kwargs)}</b>"
    return wrapper

def italic(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return f"<i>{func(*args, **kwargs)}</i>"
    return wrapper

@bold
@italic
def greet(name):
    return f"Hello, {name}"

print(greet("Ani"))
# <b><i>Hello, Ani</i></b>
```

Decorators apply **bottom-up** — the one closest to the function runs first. `@italic` wraps `greet` first (producing something that returns `<i>Hello, Ani</i>`), *then* `@bold` wraps *that* (producing `<b><i>Hello, Ani</i></b>`). Read stacked decorators from the function outward: closest to `def` = innermost = applied first. Swap the order (`@italic` above `@bold`) and you'd get `<i><b>Hello, Ani</b></i>` instead — same decorators, different nesting, different result. This is a genuinely common interview trip-up: "what does this stack of decorators print" questions are testing exactly this bottom-up rule.

## 6. Decorating class methods

Decorators work on methods too — the only wrinkle is `self` has to flow through the wrapper like any other argument, which `*args`/`**kwargs` already handles for free:

```python
class Account:
    @timer
    def slow_operation(self):
        time.sleep(0.05)
        return "done"
```

`self` just becomes the first thing inside `*args` when `wrapper` gets called — nothing special to write, the generic `*args, **kwargs` signature from §2 already covers it.

## 7. Class-based decorators — using `__call__` instead of a nested function

A decorator doesn't have to be a function that returns a function — it can be a **class** whose instances are callable, using `__call__` (a dunder you haven't met yet: it lets an *instance* of a class be called like a function, `instance()`, instead of just `instance.some_method()`).

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        print(f"call #{self.calls} to {self.func.__name__}")
        return self.func(*args, **kwargs)

@CountCalls
def say_hi():
    print("hi")

say_hi()      # call #1 to say_hi \n hi
say_hi()      # call #2 to say_hi \n hi
```

`@CountCalls` here means `say_hi = CountCalls(say_hi)` — `say_hi` is no longer a function at all, it's an *instance* of `CountCalls`, and calling `say_hi()` actually invokes `CountCalls.__call__`. The advantage over a plain function-based decorator: state (like `self.calls` here) has an obvious, natural home as instance attributes, instead of needing `nonlocal` or other workarounds to persist data between calls.

## 8. Decorators you already know, reframed

Every one of these, now that you know the mechanism, is just an ordinary decorator that happens to ship with Python or the standard library:

`@property`, `@x.setter` — from the OOP doc. `property` is a class whose instances implement the getter/setter protocol; decorating a method with it swaps that method out for a `property` object.

`@classmethod`, `@staticmethod` — also OOP. Each wraps your function in a descriptor that changes what gets passed as the first argument (`cls`, or nothing) when called through the class.

`@dataclass` — a decorator that takes your class and returns essentially the same class with `__init__`, `__repr__`, `__eq__` (and optionally more) freshly generated and attached.

`@functools.lru_cache` — genuinely worth knowing for interviews: caches a function's return value per unique set of arguments, so calling it again with the same arguments returns the cached result instantly instead of recomputing.

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(30))     # fast, despite naive recursion - repeated calls are cached
```

Without `@lru_cache`, naive recursive Fibonacci recomputes the same values over and over (exponential time); with it, each unique `n` is computed once and reused — a one-line decorator turning an exponential algorithm into a linear one, which is exactly the kind of thing worth having ready to mention in an interview.

`@functools.total_ordering` — met this already in the OOP doc's §15: fills in the rest of the comparison methods from just `__eq__` and `__lt__`.

---

## Practice questions

1. **Write your own logging decorator.** Write `@log_calls` that prints the function's name and the arguments it was called with every time it's called, e.g. calling `add(2, 3)` prints `calling add(2, 3)`, then still returns the actual result. Apply it to a couple of different functions with different signatures (a one-argument function, a two-argument function) to prove `*args, **kwargs` genuinely makes it generic.

2. **Prove `functools.wraps` matters.** Write a decorator without `@wraps`, apply it to a function with a docstring, and show `__name__` and `__doc__` are wrong. Then add `@wraps(func)` and show they're fixed. Paste both `print()` outputs side by side.

3. **Parameterized decorator.** Write `@retry(times)` that calls the decorated function up to `times` times, stopping as soon as one call succeeds (returns without raising), and re-raising the last exception if every attempt fails. Test it on a function that deliberately raises for the first two calls then succeeds on the third (you'll need something stateful, like a counter in an enclosing scope or a small class, to simulate "fails twice then works").

4. **Stacking order.** Build the `bold`/`italic` example from §5 yourself, but predict the output for `@italic` above `@bold` (the reverse order from the doc) *before* running it. Then verify.

5. **Class-based decorator.** Write a class-based decorator `Timer` (using `__call__`, like `CountCalls` in §7) that records the elapsed time of each call in a list on the instance (`self.times`), rather than just printing it. Call the decorated function three times, then print `self.times` — but you'll immediately hit a real problem: how do you actually access `self.times` from outside, once the decorated name is `some_function`, not an object you have a handle on? Figure out a way (hint: the decorated name IS the instance — nothing stops you from accessing attributes on it directly).

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for context managers.*
