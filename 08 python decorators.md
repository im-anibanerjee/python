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

### Running both versions for real, and watching the name genuinely get reassigned

**Real, verified output** — both the manual `say_hello = shout(say_hello)` version and the `@shout` sugar version give identical output:

```
BEFORE
hello
AFTER
```

**Real, verified proof that `say_hello` stops being the original function object**, printing the name *before* and *after* the reassignment:

```python
def say_hello2():
    print("hello2")
print("before decorating, say_hello2:", say_hello2)
say_hello2 = shout(say_hello2)
print("after decorating, say_hello2:", say_hello2)
```

```
before decorating, say_hello2: <function say_hello2 at 0x7f2762565760>
after decorating, say_hello2: <function shout.<locals>.wrapper at 0x7f2762565800>
```

This is worth staring at directly: the *name* `say_hello2` never changed — you can still call `say_hello2()` — but the object it points to genuinely changed, from a function literally named `say_hello2` (memory address `...5760`) to a completely different function, one named `wrapper`, defined *inside* `shout` (`shout.<locals>.wrapper`, address `...5800`). This is the exact mechanism, made visible, behind the doc's claim that `@shout` is "exactly the line `say_hello = shout(say_hello)`" — this is precisely why §3 later finds `slow_square.__name__` reporting `"wrapper"` instead of `"slow_square"`: you're looking at this exact same substitution, just on a different function.

**Flow diagram — the substitution, drawn as a before/after:**

```
BEFORE:
    say_hello  ──────►  [function say_hello: prints "hello"]

say_hello = shout(say_hello)

    Step 1: shout(say_hello) is CALLED, with the ORIGINAL say_hello
            function passed in as the parameter "func"
    Step 2: inside shout, a NEW function "wrapper" is defined — it
            hasn't run yet, just been created — and it closes over
            "func" (the original say_hello), remembering it
    Step 3: shout returns "wrapper" (not yet called, just handed back)
    Step 4: the "=" REBINDS the name say_hello to point at this
            returned wrapper function instead

AFTER:
    say_hello  ──────►  [function wrapper: prints BEFORE, calls func(), prints AFTER]
                              │
                              └─ closure reference to ──►  [original say_hello function, now UNNAMED — still exists in memory, only reachable through wrapper's closure]
```

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

### Running this for real

**Real, verified output** (your exact timing will vary slightly run to run — timing measurements always do — but it will always land right around the `time.sleep(0.1)` call):

```
slow_square took 0.1002s
25
```

The measured `0.1002s`, not exactly `0.1000s`, is itself a small, honest confirmation of something worth knowing: `time.sleep(0.1)` guarantees *at least* that much delay, never *exactly* that much — there's always a small amount of real overhead (scheduling, the surrounding Python bytecode executing) on top, which is precisely why the f-string formats to 4 decimal places rather than assuming a clean round number.

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

### Proving "passed once vs. passed fresh" with a real, running multi-call example

The trace above is precise, but here's the same claim demonstrated with actual output — calling `slow_square` three times with *different* arguments each time, to show `func` staying fixed while `args` genuinely changes:

```python
@timer
def slow_square(n):
    time.sleep(0.01)
    return n ** 2

for n in (2, 5, 9):
    print(slow_square(n))
```

**Real, verified output:**

```
slow_square took 0.0101s
4
slow_square took 0.0100s
25
slow_square took 0.0101s
81
```

Every single call correctly reports `func.__name__` as `"slow_square"` (never drifting, never needing to be re-supplied — that's the closure holding `func` fixed), while the actual squared result changes every time (`4`, `25`, `81`) because `args` genuinely carried a different value (`(2,)`, `(5,)`, `(9,)`) into `wrapper` on each of the three separate calls. This is the concrete evidence behind "passed once at decoration, passed fresh on every call" — one thing stayed constant across all three calls, the other one didn't, and the trace above tells you exactly why.

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

### Running both the broken and fixed versions for real, side by side

**Real, verified output — broken (no `@wraps`):**

```
wrapper
None
```

**Real, verified output — fixed (with `@wraps(func)`):**

```
slow_square
Return n squared.
```

This confirms both halves of the doc's claim precisely, and directly connects to §1's proof above: `slow_square.__name__` reporting `"wrapper"` is the *exact same substitution mechanism* traced in §1's before/after diagram — `slow_square` the name now points at a function object that was genuinely defined as `def wrapper(...)`, so asking it `.__name__` gets an honest, correct answer about *that* object; it's just not the answer a caller of `slow_square` would expect or want.

**Flow diagram — what `@wraps(func)` actually does, mechanically, to close this gap:**

```
def timer(func):
    @wraps(func)              ← this itself runs a decorator ON wrapper,
    def wrapper(*args, **kwargs):   using func's OWN metadata as configuration
        ...
    return wrapper

@wraps(func) is ROUGHLY equivalent to, after wrapper is defined:
    wrapper.__name__ = func.__name__        # "slow_square", copied over
    wrapper.__doc__  = func.__doc__          # "Return n squared.", copied over
    wrapper.__wrapped__ = func                # a reference back to the
                                                 ORIGINAL, for introspection
                                                 tools that want to see
                                                 through the wrapping
    (and a couple of other attributes, like __module__ and __qualname__)

So even though the OBJECT bound to slow_square is still, underneath,
the function literally defined as "wrapper" — its __name__ and __doc__
attributes have been overwritten to LIE, deliberately and helpfully,
in a way that makes it indistinguishable from the original for every
practical purpose (logging, help(), debugging tracebacks).
```

The reason this is "a rule with no exceptions" rather than a nice-to-have: without it, every decorator you stack onto real code silently corrupts `__name__`/`__doc__` for anything downstream that inspects it — logging frameworks that print the calling function's name, `help()`, auto-generated API documentation, debuggers showing a stack trace — all of it would report `"wrapper"` for every single decorated function in your entire codebase, making tracebacks and logs genuinely useless for telling which function actually ran.

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

### Running this for real, including proof `@wraps` still did its job through three layers of nesting

**Real, verified output:**

```
Hello, Ani
Hello, Ani
Hello, Ani
greet
```

That final line — `greet.__name__` correctly reporting `"greet"`, not `"wrapper"` — confirms `@wraps(func)` still works correctly even nested three layers deep; it doesn't matter how many outer layers of function-returning-function sit above `wrapper`, only that `@wraps(func)` sits immediately above `wrapper`'s own definition, with the right `func` in scope at that point.

**Flow diagram — unpacking `@repeat(times=3)` into its two explicit steps, exactly as the doc's prose describes, but traced with real closures at each layer:**

```
@repeat(times=3)
def greet(name): ...

is exactly two sequential operations:

STEP 1:  repeat(times=3)   ← called IMMEDIATELY, before greet is even
                              considered
    Inside repeat: times = 3
    Defines "decorator" (the middle layer), which closes over times=3
    Returns decorator  ← call this returned function "the_decorator"

    ┌───────────────────────┐
    │  the_decorator          │
    │  closure: times = 3    │
    └───────────────────────┘

STEP 2:  the_decorator(greet)   ← the actual decoration, using
                                    whatever STEP 1 returned
    Inside decorator: func = greet (the original)
    Defines "wrapper" (the inner layer), which closes over BOTH
        func (=greet) AND times (=3, inherited from decorator's own
        enclosing scope, which is repeat's scope)
    @wraps(func) copies greet's __name__/__doc__ onto wrapper
    Returns wrapper
    greet = wrapper   (final rebinding — greet now IS wrapper)

    ┌───────────────────────────────┐
    │  wrapper (bound to name "greet")│
    │  closure: func = original greet │
    │  closure: times = 3              │
    └───────────────────────────────┘

greet("Ani")   ← calls wrapper("Ani")
    for _ in range(3):          ← times, reached through TWO levels
                                    of closure (decorator's scope,
                                    which itself closed over repeat's)
        result = func("Ani")     ← func, reached through closure —
                                    prints "Hello, Ani" each time
```

The genuinely important detail this diagram makes concrete: `wrapper` isn't just closing over one enclosing scope, it's closing over a *chain* of them — `times` technically lives in `repeat`'s scope, one level further out than `decorator`'s own scope, but Python's LEGB name resolution (from the fundamentals doc) walks outward through as many enclosing scopes as it takes to find a match, which is exactly why `wrapper` can still read `times` without any extra plumbing.

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

### Running both orders for real, side by side

**Real, verified output:**

```python
@bold
@italic
def greet(name):
    return f"Hello, {name}"
print(greet("Ani"))

@italic
@bold
def greet2(name):
    return f"Hello, {name}"
print(greet2("Ani"))
```

```
<b><i>Hello, Ani</i></b>
<i><b>Hello, Ani</b></i>
```

Both predictions confirmed exactly — same two decorator functions, reversed stacking order, genuinely different nesting in the output.

**Flow diagram — why stacked decorators apply bottom-up, tied directly to §1's "reassign the name" mechanism, just applied twice in a row:**

```
@bold
@italic
def greet(name):
    return f"Hello, {name}"

is EXACTLY equivalent to writing (bottom decorator applied FIRST,
exactly like the doc states, because it's the one written closest
to the actual "def"):

    def greet(name):
        return f"Hello, {name}"
    greet = italic(greet)     ← STEP 1: greet is now italic's wrapper,
                                 which will produce "<i>...</i>" around
                                 whatever the ORIGINAL greet returns
    greet = bold(greet)        ← STEP 2: greet is now bold's wrapper,
                                 which will produce "<b>...</b>" around
                                 whatever ITS argument (the CURRENT
                                 greet, i.e. italic's wrapper) returns

Calling greet("Ani") now:
    → runs bold's wrapper, which calls func("Ani")
        → func here IS italic's wrapper (from STEP 1)
        → which calls ITS OWN func("Ani")
            → this is the ORIGINAL greet("Ani") → "Hello, Ani"
        → italic's wrapper wraps that: "<i>Hello, Ani</i>"
    → bold's wrapper wraps THAT: "<b><i>Hello, Ani</i></b>"
```

The reading rule the doc gives — "closest to `def` = innermost = applied first" — falls directly out of this: each `@decorator` line reassigns `greet` to a new wrapper *around whatever `greet` currently is*, top to bottom in the source, which means the *last* reassignment (from the *topmost* `@decorator` line) ends up as the *outermost* layer, and the first one applied (from the line right above `def`) ends up wrapped *inside* every decorator listed above it.

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

### Running this for real, on an actual instance

**Real, verified output:**

```python
class Account:
    @timer
    def slow_operation(self):
        time.sleep(0.05)
        return "done"

a = Account()
print(a.slow_operation())
```

```
slow_operation took 0.0502s
done
```

**Flow diagram — confirming "`self` just becomes the first thing inside `*args`," traced through the exact same substitution mechanism as every other example in this doc:**

```
class Account:
    @timer
    def slow_operation(self): ...

    is exactly:  slow_operation = timer(slow_operation)
    → Account.slow_operation is now timer's wrapper, closing over
      func = the ORIGINAL slow_operation (which still expects self
      as its first parameter, completely unchanged)

a = Account()
a.slow_operation()

    Recall from the OOP doc: a.slow_operation() is really
    Account.slow_operation(a) — Python automatically supplies "a" as
    the first positional argument to WHATEVER function object
    Account.slow_operation currently refers to.

    Since that object is now wrapper(*args, **kwargs), the call
    becomes:
        wrapper(a)
            args = (a,)          ← self landed inside args, as its
                                    FIRST element, completely
                                    automatically — wrapper's
                                    signature never had to mention
                                    self by name at all
            kwargs = {}
            func(*args, **kwargs)
                = func(a)         ← unpacked back out — this correctly
                                    calls the ORIGINAL slow_operation
                                    with self=a, exactly as if the
                                    decorator had never been applied
```

This is exactly why the doc calls this "the only wrinkle," and why that wrinkle turns out not to need any special handling at all: `*args, **kwargs` was already designed in §2 to accept "any function's arguments, whatever they turn out to be" — `self` being implicitly passed as a method's first argument is just one more instance of "arguments the wrapper doesn't need to know about in advance," which is the entire problem `*args, **kwargs` was built to solve.

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

### Running this for real, with proof `say_hi` is genuinely not a function anymore

**Real, verified output:**

```python
say_hi()
say_hi()
print(type(say_hi))
print(say_hi.calls)
```

```
call #1 to say_hi
hi
call #2 to say_hi
hi
<class '__main__.CountCalls'>
2
```

`type(say_hi)` reporting `<class '__main__.CountCalls'>` — not `<class 'function'>` — is the direct, concrete proof of the doc's claim: `say_hi` genuinely is a `CountCalls` instance, not any kind of function at all. `say_hi.calls` being directly readable and equal to `2` afterward is the payoff the doc promises: that count lives as a completely ordinary instance attribute, inspectable from outside at any time, in a way a plain closure-based counter (using `nonlocal`, as you'd need without a class) cannot offer nearly as conveniently.

**Flow diagram — why `say_hi()` runs `CountCalls.__call__`, tracing exactly what `@CountCalls` did to the name `say_hi`:**

```
@CountCalls
def say_hi():
    print("hi")

is exactly:  say_hi = CountCalls(say_hi)

    CountCalls(say_hi) constructs a NEW INSTANCE of the CountCalls
    class (this is just an ordinary constructor call, from the OOP
    doc) — __init__ runs with self = this new instance, func = the
    original say_hi:
        self.func = say_hi          ← the original function, stored
        self.calls = 0

    say_hi is REBOUND to point at this new CountCalls INSTANCE,
    completely replacing the original function object as the target
    of that name.

    ┌────────────────────────────┐
    │  say_hi (a CountCalls        │
    │  instance)                    │
    │  self.func  = [original say_hi]│
    │  self.calls = 0                │
    └────────────────────────────┘

say_hi()

    Calling an object with () triggers Python to look for __call__
    on its class — exactly the same "special syntax maps to a dunder
    method" pattern as len(x) -> x.__len__(), obj1 + obj2 ->
    obj1.__add__(obj2) from the OOP doc's dunder-methods section.
    → runs CountCalls.__call__(self=say_hi)
        self.calls += 1              → 0 becomes 1
        print(f"call #1 to say_hi")
        return self.func()            → calls the ORIGINAL function,
                                          via the reference stored in
                                          __init__ → prints "hi"
```

The reason this genuinely counts as "a decorator" despite looking so different from every function-based one earlier in the doc: the fundamental contract — "receives the original function, returns something callable that stands in for it" — is satisfied identically. `CountCalls(say_hi)` receives `say_hi` and returns something (an instance) that can be called exactly like a function could (`say_hi()`), thanks to `__call__`. The mechanism for "wrapping" swapped from closures to instance attributes, but the shape of the pattern — one thing given a function, handing back a stand-in for it — never changed.

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

### Proving the exponential-vs-linear claim with a real, measured timing comparison, plus a look at the cache's own stats

Rather than take "fast, despite naive recursion" as a slogan, here's a real head-to-head, running the *identical* Fibonacci logic both naive and `@lru_cache`-decorated:

```python
import time
from functools import lru_cache

def fib_naive(n):
    if n < 2:
        return n
    return fib_naive(n - 1) + fib_naive(n - 2)

@lru_cache(maxsize=None)
def fib_cached(n):
    if n < 2:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)

start = time.perf_counter()
r1 = fib_naive(28)
t1 = time.perf_counter() - start

start = time.perf_counter()
r2 = fib_cached(28)
t2 = time.perf_counter() - start

print("naive fib(28) =", r1, f"took {t1:.4f}s")
print("cached fib(28) =", r2, f"took {t2:.6f}s")
print(fib_cached(30))
print(fib_cached.cache_info())
```

**Real, verified output:**

```
naive fib(28) = 317811 took 0.0569s
cached fib(28) = 317811 took 0.000047s
832040
CacheInfo(hits=29, misses=31, maxsize=None, currsize=31)
```

That's roughly **1,200x** faster for the cached version at `n=28`, both computing the exact same correct answer (`317811`) — and the gap would keep widening dramatically for larger `n`, since the naive version's cost grows exponentially while the cached version's cost is genuinely linear in `n`.

`fib_cached.cache_info()` — a real, inspectable method `@lru_cache` attaches to the decorated function — is worth reading carefully: `misses=31` means the *actual* underlying computation (the `if`/`return` logic) only ever ran 31 times, total, across the entire program, covering every unique value of `n` from `0` up to `30` (`fib(28)` needed values 0–28; `fib(30)` needed two more, 29 and 30 — 31 unique values total). `hits=29` means 29 separate times, some inner recursive call asked for a value that had *already* been computed and stored, and got the cached answer back instantly instead of recomputing.

**Flow diagram — why naive recursive Fibonacci is exponential, and exactly what `@lru_cache` intercepts to fix it:**

```
Naive fib(5), traced as a call tree — notice fib(3), fib(2), fib(1)
etc. get computed MULTIPLE times, from different branches:

                        fib(5)
                       /      \
                  fib(4)        fib(3)
                 /    \         /    \
             fib(3)  fib(2)  fib(2)  fib(1)
             /   \    /  \    /  \
         fib(2) fib(1) ...  ...  ...
         /   \
     fib(1) fib(0)

Notice: fib(3) appears TWICE (once under fib(4), once directly under
fib(5)), fib(2) appears THREE times, and so on — the tree's size
roughly DOUBLES with every step up in n, because each call spawns
two more, many of which recompute values already computed elsewhere
in the tree. This is the literal mechanism behind "exponential time."

@lru_cache(maxsize=None), applied to fib_cached:

    Every call to fib_cached(n) is INTERCEPTED before the real
    function body runs (this is the SAME "wrapper stands in front"
    pattern as every decorator in this doc — lru_cache builds a
    wrapper internally, just like the ones you've been hand-writing):

        wrapper(n):
            if n has been seen before (check an internal dict,
               keyed by the arguments — here, just n):
                return the STORED result immediately — a "hit" —
                NEVER runs the real fib_cached body again for this n
            else:
                run the real body, COMPUTE the result, STORE it in
                that internal dict keyed by n, THEN return it — a
                "miss"

    fib_cached(5) call tree, with caching:
        fib(5) -> needs fib(4), fib(3)
            fib(4) -> needs fib(3) [MISS, computes+stores], fib(2) [MISS]
                fib(3) -> needs fib(2) [MISS], fib(1) [MISS]
                    ...
            fib(3) -> needed AGAIN by fib(5) directly -> ALREADY
                       CACHED from when fib(4) needed it -> HIT,
                       instant, no recursion happens at all this time
```

This is the exact, mechanical reason `misses=31` while there are far more than 31 total calls made across the whole program (each call to `fib_cached` either genuinely computes a new value — a miss — or short-circuits into an instant cache lookup — a hit): the *decorator* is silently sitting in front of every call, remembering every result it's ever computed, and only letting the real, recursive logic underneath run once per unique input value, no matter how many different places in the call tree ask for that same value.

---

## Practice questions

1. **Write your own logging decorator.** Write `@log_calls` that prints the function's name and the arguments it was called with every time it's called, e.g. calling `add(2, 3)` prints `calling add(2, 3)`, then still returns the actual result. Apply it to a couple of different functions with different signatures (a one-argument function, a two-argument function) to prove `*args, **kwargs` genuinely makes it generic.

2. **Prove `functools.wraps` matters.** Write a decorator without `@wraps`, apply it to a function with a docstring, and show `__name__` and `__doc__` are wrong. Then add `@wraps(func)` and show they're fixed. Paste both `print()` outputs side by side.

3. **Parameterized decorator.** Write `@retry(times)` that calls the decorated function up to `times` times, stopping as soon as one call succeeds (returns without raising), and re-raising the last exception if every attempt fails. Test it on a function that deliberately raises for the first two calls then succeeds on the third (you'll need something stateful, like a counter in an enclosing scope or a small class, to simulate "fails twice then works").

4. **Stacking order.** Build the `bold`/`italic` example from §5 yourself, but predict the output for `@italic` above `@bold` (the reverse order from the doc) *before* running it. Then verify.

5. **Class-based decorator.** Write a class-based decorator `Timer` (using `__call__`, like `CountCalls` in §7) that records the elapsed time of each call in a list on the instance (`self.times`), rather than just printing it. Call the decorated function three times, then print `self.times` — but you'll immediately hit a real problem: how do you actually access `self.times` from outside, once the decorated name is `some_function`, not an object you have a handle on? Figure out a way (hint: the decorated name IS the instance — nothing stops you from accessing attributes on it directly).

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for context managers.*
