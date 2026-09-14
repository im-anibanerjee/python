# Topic 9 — Context Managers, Deep Dive

*Phase 1, Intermediate group — item 5 of 6. You've already met one dunder method that makes an object "callable" (`__call__`, from the decorators doc). This topic introduces the pair that makes an object work with `with` — `__enter__` and `__exit__`.*

---

## 1. The problem context managers solve

You've already used a context manager without necessarily calling it that — opening a file:

```python
with open("data.txt") as f:
    contents = f.read()
```

Why not just this instead?

```python
f = open("data.txt")
contents = f.read()
f.close()
```

Because if `f.read()` raises an exception, `f.close()` on the line after it **never runs**. The file handle leaks — stays open, holding a lock on the file, using up one of the OS's limited open-file slots — for as long as the program keeps running. The traditional fix is `try`/`finally`:

```python
f = open("data.txt")
try:
    contents = f.read()
finally:
    f.close()      # runs whether the try block succeeded OR raised
```

This works, but it's verbose, and it's easy to forget for any resource that isn't a file — a database connection, a thread lock, a network socket. `with` is that exact `try`/`finally` pattern, packaged into an object once, so you never have to hand-write it again:

```python
with open("data.txt") as f:
    contents = f.read()
# f.close() has ALREADY happened by this point, guaranteed — even if f.read() raised
```

`with` guarantees the cleanup step runs, no matter how the block exits — normally, via `return`, via `break`, or via an uncaught exception. That guarantee is the entire point.

### Proving the leak claim for real, rather than just asserting it

Since deliberately breaking a real file's `read()` is awkward to stage safely, here's the exact same shape of bug reproduced with a stand-in object that behaves like a file (has `.read()` and `.close()`) but lets us directly *observe* whether `close()` actually ran, by checking a `.closed` flag afterward:

```python
class LeakyFile:
    def __init__(self, name):
        self.name = name
        self.closed = False
    def read(self):
        raise ValueError("simulated read failure")
    def close(self):
        self.closed = True

# version WITHOUT try/finally
f = LeakyFile("data.txt")
try:
    contents = f.read()
    f.close()
except ValueError as e:
    print("caught:", e)
print("without try/finally, f.closed =", f.closed)

# version WITH try/finally
f2 = LeakyFile("data.txt")
try:
    try:
        contents = f2.read()
    finally:
        f2.close()
except ValueError as e:
    print("caught:", e)
print("with try/finally, f2.closed =", f2.closed)
```

**Real, verified output:**

```
caught: simulated read failure
without try/finally, f.closed = False
caught: simulated read failure
with try/finally, f2.closed = True
```

This is the leak, made undeniable rather than theoretical: in the first version, `f.read()` raises before the program ever reaches `f.close()` on the next line — that line is simply never executed, skipped entirely by the exception jumping straight to the nearest `except` — so `f.closed` stays `False` forever, even though the exception was caught and handled a moment later. In the second version, `f2.close()` sits inside a `finally`, which Python guarantees to run regardless of whether the `try` block above it succeeded or raised — so `f2.closed` correctly ends up `True`, even though the exact same `ValueError` happened. Both programs catch the same exception and print the same message; only the resource's fate differs, and it differs entirely because of *where* `close()` was placed, not anything about the exception itself.

**Flow diagram — exactly where control jumps in the broken version, line by line:**

```
f = LeakyFile("data.txt")
try:
    contents = f.read()     ← raises ValueError HERE, immediately
    f.close()                 ← THIS LINE IS NEVER REACHED — the raise
                                 above jumps straight past it, out of
                                 the try block entirely, looking for
                                 the nearest matching except
except ValueError as e:
    print("caught:", e)       ← execution resumes HERE instead

f.closed is still False — nothing ever called f.close()
```

## 2. What `with` actually does, mechanically

Strip away the syntax. Given:

```python
with some_object as name:
    BODY
```

Python does exactly this, every time, no exceptions:

```python
manager = some_object
name = manager.__enter__()
try:
    BODY
finally:
    manager.__exit__(exc_type, exc_val, exc_tb)
```

Two dunder methods are involved. `__enter__()` runs first, before the block — whatever it `return`s is what gets bound to `name` (the thing after `as`). `__exit__(exc_type, exc_val, exc_tb)` runs last, after the block, **always** — whether the block finished cleanly or raised. If the block raised, `exc_type`/`exc_val`/`exc_tb` carry the exception's class, the exception instance, and its traceback; if the block finished cleanly, all three are `None`.

### Flow diagram — the mechanical translation, drawn as a single control-flow picture

This section already gives you the translated code directly, which is the clearest possible explanation — but it's worth seeing the *shape* of it once, since every single example for the rest of this doc is just this one picture, filled in differently:

```
with some_object as name:        ┌─────────────────────────────┐
    BODY                          │  manager = some_object       │
                                   │  name = manager.__enter__()   │───► whatever __enter__
                     is exactly:  │  try:                            │      RETURNS becomes
                                   │      BODY                        │      "name"
                                   │  finally:                        │
                                   │      manager.__exit__(...)        │───► ALWAYS runs, body
                                   └─────────────────────────────┘      succeeded or not

    Two guarantees baked into this shape, both worth naming explicitly:
    1. __enter__ ALWAYS runs before BODY — there's no way to skip setup
    2. __exit__ ALWAYS runs after BODY — because it's inside "finally,"
       which itself is defined (from the exceptions doc) to run no
       matter how the try block above it exits: clean completion,
       a caught exception, an uncaught one, even a return/break inside it
```

Every example in §3 through §6 below is a specific instance of filling in `some_object`, `__enter__`, and `__exit__` — the control-flow shape itself never changes.

## 3. Writing your own — a class-based context manager

```python
class Timer:
    def __enter__(self):
        import time
        self.start = time.perf_counter()
        return self                       # this becomes "as timer" — self, so you can read timer.elapsed after

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.elapsed = time.perf_counter() - self.start
        print(f"took {self.elapsed:.4f}s")
        return False                        # don't suppress any exception — explained in §4

with Timer() as timer:
    total = sum(range(10_000_000))

print(timer.elapsed)     # accessible afterwards — __enter__ returned self
```

Trace it: `Timer()` builds an instance. `__enter__` runs, records the start time, and `return self` means the instance itself is what `timer` refers to inside the `with` block — so anything you set on `self` during `__enter__` or inside the block is reachable through `timer` both inside and after the block. The block runs (`total = sum(...)`). `__exit__` runs, computes elapsed time, prints it. This is the class-based sibling of the `Timer` decorator you already built in the decorators doc's practice — same idea (measure elapsed time around some code), different mechanism (`__enter__`/`__exit__` instead of `__call__`), and worth noticing they solve overlapping problems from two different angles: a decorator wraps a *function you're calling repeatedly*; a context manager wraps a *block of code you're running once, right here*.

### Tracing an actual run

Running the exact code above produces two lines — from two different places:

```
took 0.0907s
0.09065930200000238
```

`took 0.0907s` is the `print` living *inside* `__exit__` — it fires the moment the `with` block finishes (right after `total = sum(range(10_000_000))` completes), before control ever reaches the line after `with`. `0.09065930200000238` is the *second*, separate `print(timer.elapsed)` sitting *outside* the `with` block — it's reading the exact same `self.elapsed` value `__exit__` just set, but printing it raw (no `:.4f` formatting this time), so you get the full unrounded float instead of the tidy 4-decimal version. Your own numbers will differ every time you run it — `sum(range(10_000_000))` takes a slightly different amount of wall-clock time depending on your machine and whatever else is running — but the shape is always the same: a short formatted line first, a longer raw float second, and the two are always numerically identical, just rounded differently.

Notice `total` itself never appears anywhere in that output — not because of any timing quirk, just because the code never calls `print(total)`. It's computed, assigned to a local variable inside the block, and then simply sits there unused. It genuinely is fully computed *before* `__exit__` runs, though — not concurrently, not after. Go back to the mechanical translation from §2:

```
manager = Timer()
timer = manager.__enter__()
try:
    total = sum(range(10_000_000))    # <-- the ENTIRE with-block body runs to completion here
finally:
    manager.__exit__(None, None, None)   # <-- only reached AFTER the try block is fully done
```

`__exit__` lives inside the `finally`, and a `finally` block only ever runs *after* its `try` block has finished — whether that finish was normal completion or an exception. So the sequence is strictly: `__enter__` runs, then the *entire* block body runs top to bottom (here just one line, but it could be ten and every one would finish first), and only once that's completely done does `__exit__` fire. That's exactly why `self.start` is captured in `__enter__` and `self.elapsed` is computed in `__exit__` — the elapsed time is measured across precisely that gap: everything the block did, start to finish, before cleanup runs.

### Re-running this fresh, for an independent confirmation

Running the exact same `Timer` code again, on a fresh run, to confirm the shape of the output holds (not just the specific numbers from one earlier run):

**Real, verified output:**

```
took 0.1645s
0.1644527299999936
```

Different absolute numbers (this run happened to take a bit longer — a completely normal amount of machine-load-dependent variance), but the exact same *shape*: a `:.4f`-formatted line from inside `__exit__`, printed automatically as part of leaving the block, followed by the same value again, unrounded, from the explicit `print(timer.elapsed)` after the block. That consistency — different absolute timings, identical structure — is itself a small, concrete confirmation that the mechanism being described (not the specific numbers) is what's reliable here.

**Flow diagram — where each attribute lives, and why `timer.elapsed` is readable after the block ends:**

```
with Timer() as timer:

    Timer()                    ← builds a new, empty Timer instance
    manager = that instance
    timer = manager.__enter__()
        inside __enter__: self.start = <a timestamp>
                            return self   ← the INSTANCE itself
        → timer NOW points at the SAME object as "manager" — not a
          copy, not a different kind of handle — the literal same
          Timer instance, which currently has ONE attribute: start

    total = sum(range(10_000_000))    ← BODY runs; doesn't touch
                                          timer/manager at all

    manager.__exit__(None, None, None)
        inside __exit__: self refers to that SAME instance again
                          self.elapsed = ...   ← a SECOND attribute
                                                   is added to the
                                                   SAME object timer
                                                   already points to
                          print(f"took {self.elapsed:.4f}s")
                          return False

print(timer.elapsed)
    timer still points at that one Timer instance — which by now has
    BOTH start and elapsed set on it — so timer.elapsed reads the
    value __exit__ just wrote, with no special plumbing required:
    it's the same "one object, multiple sticky notes pointing at it"
    idea from the very first fundamentals doc, just with attributes
    instead of variable names.
```

## 4. `__exit__`'s return value — suppressing exceptions

This is the part that trips people up, and it's genuinely important: **whatever `__exit__` returns controls whether an exception that happened inside the block keeps propagating, or gets silently swallowed.**

```python
class SuppressValueError:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is ValueError:
            print(f"suppressing: {exc_val}")
            return True          # <-- True means "I handled it, don't propagate"
        return False              # anything else: let it propagate normally

with SuppressValueError():
    print("before")
    raise ValueError("oops")
    print("after")          # never reached — the raise skips straight to __exit__

print("continuing normally")
```

Output:
```
before
suppressing: oops
continuing normally
```

Walk through why: `raise ValueError("oops")` fires inside the block. Python doesn't let it propagate immediately — first, it calls `__exit__(ValueError, ValueError("oops"), <traceback>)`, exactly per the mechanical translation in §2 (the `finally` block always runs, exception or not). Inside `__exit__`, `exc_type is ValueError` is `True`, so it prints the suppression message and `return True`. That `True` is the signal: "this exception has been dealt with — do not re-raise it." Control resumes normally *after* the `with` block, as if nothing happened — `print("continuing normally")` runs with no exception in sight.

Compare: if `__exit__` had `return False` (or returned nothing at all — `None` is falsy, same effect), the exception would propagate normally once `__exit__` finishes — exactly as if the `with` block weren't there, just with cleanup guaranteed to have run first. **`return False` (or nothing) is almost always what you want** — a context manager that quietly swallows unrelated exceptions is a common source of confusing bugs, since code after the `with` block runs as if everything succeeded when something silently didn't. Only return `True` when you deliberately intend to suppress a *specific*, expected exception type, exactly like the `ValueError`-only check above.

### Running this exact code for real, fresh

**Real, verified output — confirmed to match the doc's stated output exactly:**

```
before
suppressing: oops
continuing normally
```

**Flow diagram — the moment of the `raise`, traced against §2's mechanical translation, with the exception info flowing explicitly into `__exit__`'s three parameters:**

```
manager = SuppressValueError()
manager.__enter__()          → returns self, bound to nothing here
                                 (no "as" clause in this example)
try:
    print("before")            → runs normally
    raise ValueError("oops")   → an exception object is created and
                                   thrown HERE — "after" is never
                                   reached, execution jumps straight
                                   out of the try block
finally:
    manager.__exit__(
        exc_type = ValueError,           ← the CLASS of what was raised
        exc_val  = ValueError("oops"),    ← the actual exception INSTANCE
        exc_tb   = <traceback object>      ← where it happened
    )
        if exc_type is ValueError:   → True
            print(f"suppressing: {exc_val}")   ← exc_val's __str__ is
                                                   "oops" (from the
                                                   exceptions doc's
                                                   ValueError message
                                                   behavior)
            return True

    __exit__ returned True  →  Python's with-statement machinery
    checks this return value SPECIFICALLY, and when it's truthy,
    DISCARDS the pending exception instead of letting the finally
    block's normal behavior (re-raise whatever was in flight) happen.

print("continuing normally")   → reached normally, no exception
                                    anywhere in sight from this point on
```

This is the one place where the §2 translation needs a small addendum to be fully accurate: an ordinary `finally` block, on its own, does *not* have the power to cancel an exception that was already in flight — it only guarantees to *run*, then lets the original exception continue propagating afterward, unless something inside it raises a new one. `with`'s actual implementation (not the simplified translation) specifically checks `__exit__`'s return value and, if it's truthy, tells the exception machinery "this one's been handled, stop propagating it" — a capability plain `try`/`finally` doesn't have on its own. That's the real, specific reason `__exit__`'s return value matters at all, rather than `__exit__` just being "the `finally` part."

## 5. `contextlib.contextmanager` — writing one as a generator instead of a class

Writing a full class with `__enter__`/`__exit__` for something simple is often more boilerplate than the job needs. `contextlib.contextmanager` lets you write a context manager as a single generator function instead:

```python
from contextlib import contextmanager
import time

@contextmanager
def timer():
    start = time.perf_counter()
    try:
        yield                          # <-- this is where the "with" block's code actually runs
    finally:
        elapsed = time.perf_counter() - start
        print(f"took {elapsed:.4f}s")

with timer():
    total = sum(range(10_000_000))
```

Running this prints exactly one line:

```
took 0.0911s
```

Trace the flow step by step, leaning on the generator pause/resume mechanics from the generators doc: `timer()` doesn't run any of the function's body yet — calling a generator function only ever builds a generator object, it never executes anything (same as always). Entering the `with` block is what actually resumes it for the first time: `start = time.perf_counter()` runs, then execution hits `yield` and **pauses right there** — exactly like `next()` pausing a generator at its first `yield`, except here it's `contextmanager`'s machinery doing the "advancing" instead of you calling `next()` by hand. Since this `yield` has no value (`yield` alone, not `yield something`), there's nothing to bind to a `with ... as x`, which is why this `with timer():` line has no `as` at all. The block body (`total = sum(...)`) now runs to completion. Leaving the `with` block is what resumes the *paused* generator a second time, picking up exactly where it left off — right after `yield`, inside the `finally`: `elapsed` gets computed, and `print(f"took {elapsed:.4f}s")` runs. The generator then reaches the end of the function and stops, exactly as any exhausted generator does.

The mental model: **everything before `yield` is `__enter__`; everything after `yield` is `__exit__`.** `contextmanager` takes your generator function and wraps it so that calling `timer()` doesn't run the function immediately — instead, entering the `with` block resumes the generator up to its `yield`, and leaving the `with` block resumes it *from* the `yield` to the end (exactly the "pause and resume" mechanics from the generators doc — this is a real, direct application of that mechanism, not a coincidence). Whatever you `yield` (or `yield some_value`) becomes the thing bound to `as name`, same role as `__enter__`'s return value:

```python
@contextmanager
def timer():
    start = time.perf_counter()
    result = {}
    try:
        yield result             # this dict becomes "as timer" — same "return self" idea as before
    finally:
        result["elapsed"] = time.perf_counter() - start

with timer() as t:
    total = sum(range(10_000_000))
print(t["elapsed"])
```

Running this prints one line — note this version has no `print` inside the function itself, so the only output is the plain `print(t["elapsed"])` at the very bottom:

```
0.11294325500000468
```

Same pause/resume flow as before, with one difference — this time `yield result` yields an actual value (the empty dict), so that's what gets bound to `t`. Trace it: `timer()` builds the generator, `start` and `result = {}` run, execution pauses at `yield result`, and `t` is now bound to that *same* dict object — not a copy of it, the literal same object living inside the paused generator's frame. The block runs (`total = sum(...)`). Leaving the block resumes the generator past `yield`, into the `finally`, where `result["elapsed"] = ...` mutates that dict *in place*. Because `t` and `result` are two names pointing at the exact same dictionary object, that mutation is immediately visible through `t` too — `t["elapsed"]` now holds the elapsed time, even though `t` was assigned back when the dict was still empty. This is the same "shared reference, not a copy" behavior any mutable object has in Python — nothing special to context managers, just worth noticing since it's *how* a `yield`ed empty container ends up populated by the time you read it after the `with` block.

The `try`/`finally` around the `yield` is not optional — it's the *entire mechanism* by which this style handles exceptions correctly. If the `with` block raises, that exception surfaces at the `yield` line itself (the generator resumes with an exception injected exactly where it paused, instead of resuming normally) — without the `finally`, your cleanup code after `yield` would simply never run on the failure path, silently reintroducing the exact bug `with` exists to prevent.

### Re-running both versions fresh, for an independent confirmation

**Real, verified output**, first version (bare `yield`, no `as`):

```
took 0.1683s
```

**Real, verified output**, second version (`yield result`, bound via `as t`):

```
0.16327426599991668
```

Same shape as the original run in both cases — one printed-from-inside line for the bare-`yield` version, one printed-from-outside line for the `yield result` version — confirming this isn't a one-off fluke of the earlier numbers.

### Flow diagram — the pause/resume timeline for `@contextmanager`, drawn explicitly against the generator mechanics from the generators doc

```
def timer():
    start = time.perf_counter()
    try:
        yield              ← PAUSE POINT
    finally:
        elapsed = ...
        print(...)

with timer():
    BODY

Step 1: timer()  called
    → builds a generator object. NOTHING inside the function has run
      yet — exactly like ANY generator function (generators doc §4).
      @contextmanager's own machinery is what's holding this
      generator object, wrapped so it presents as a normal context
      manager (with __enter__/__exit__) from the outside.

Step 2: entering the "with" block
    → @contextmanager's __enter__ calls next() on the underlying
      generator ONE time — this is the FIRST resume.
    → start = time.perf_counter() runs
    → execution reaches "yield" and FREEZES there — every local
      variable (start) preserved exactly as in the generators doc's
      pause mechanics
    → next()'s return value (whatever was yielded, or None for a
      bare "yield") becomes __enter__'s return value, which is what
      gets bound to "as name" (or discarded, with no "as" at all)

Step 3: BODY runs
    → completely separate from the generator — the generator is just
      sitting frozen, mid-function, while this runs

Step 4: leaving the "with" block
    → @contextmanager's __exit__ resumes the SAME frozen generator —
      this is the SECOND (and, for this generator, LAST) resume —
      picking up exactly at the frozen "yield" line
    → falls into the finally: block, computes elapsed, prints it
    → the generator function then reaches its own natural end (no
      more code) → raises StopIteration internally, which
      @contextmanager's machinery correctly interprets as "cleanup
      finished successfully," not as an error bubbling up to you
```

The reason the mental model "everything before `yield` is `__enter__`; everything after is `__exit__`" is exactly right, not just approximately right: those two resumes — the first one driving execution up to `yield`, the second driving it from `yield` to the end — are *literally* the entire implementation of `__enter__` and `__exit__` that `@contextmanager` builds for you, mechanically, from your one generator function.

## 6. Multiple context managers in one `with`

```python
with open("in.txt") as fin, open("out.txt", "w") as fout:
    fout.write(fin.read())
```

Worth slowing down on that one line, `fout.write(fin.read())`, since two files and two operations are packed into it. `fin` is the file object for `in.txt`, opened for reading (the default mode of `open(...)` with no second argument). `fout` is the file object for `out.txt`, opened for **writing** — the `"w"` mode argument — which means `out.txt` gets created if it doesn't exist yet, or completely emptied out first if it already does, before anything is written to it.

Python evaluates the *inner* call first, same as any nested function call: `fin.read()` runs, reading the **entire contents** of `in.txt` from wherever the file's read-position currently is (right at the start, since `fin` was just opened) all the way to the end of the file, and returns it as one single string — for example, given an `in.txt` containing three lines, `fin.read()` returns the string `"first line\nsecond line\nthird line\n"` (the `\n` characters are the actual newlines from the file, now sitting inside the string itself, not something Python added). That whole string is now sitting in memory, as the temporary result of `fin.read()` — nothing has touched `out.txt` yet.

*Then* `fout.write(...)` runs, taking that string and writing it into `out.txt`. Concretely, with `in.txt` containing:
```
first line
second line
third line
```
running the `with` block above and then opening `out.txt` shows:
```
first line
second line
third line
```
— `out.txt`'s contents end up identical to `in.txt`'s, because `fout.write` received the exact string `fin.read()` produced and wrote all of it, unchanged, into the (now-emptied) output file. The net effect of the whole line: **read all of `in.txt`, then write all of it into `out.txt`** — a full-file copy, done in one line because `read()` and `write()` compose directly, with `read()`'s return value flowing straight into `write()`'s argument without ever being stored in its own named variable.

This is exactly equivalent to nesting them:

```python
with open("in.txt") as fin:
    with open("out.txt", "w") as fout:
        fout.write(fin.read())
```

Both files get entered in the order written, left to right, and — crucially — both get exited in the *reverse* order, right to left, even if an exception happens partway through. That reverse-order guarantee matters when resources depend on each other (e.g. closing a database session before closing the connection it came from) — it's the same "last opened, first closed" discipline you'd get from properly nested `try`/`finally` blocks, just without having to write the nesting by hand.

### Running the actual file copy for real

**Real, verified output** — a real `in.txt` was written with exactly those three lines, then the copy `with` block above was run, then `out.txt` was read back:

```
'first line\nsecond line\nthird line\n'
```

Confirms exactly what the doc describes — the raw `repr()` even shows the literal `\n` characters that came from the file itself, matching the doc's own description of what `fin.read()` returns.

### Proving the reverse-order exit claim for real, with a custom context manager that announces its own enter/exit

The doc's claim — "both get exited in the *reverse* order, right to left" — is exactly the kind of thing worth not taking on faith. Here it is proven directly, using three small context managers that each print when they're entered and exited:

```python
class Named:
    def __init__(self, name):
        self.name = name
    def __enter__(self):
        print(f"ENTER {self.name}")
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"EXIT  {self.name}")
        return False

with Named("A") as a, Named("B") as b, Named("C") as c:
    print("inside block")
```

**Real, verified output:**

```
ENTER A
ENTER B
ENTER C
inside block
EXIT  C
EXIT  B
EXIT  A
```

This is direct, undeniable proof: entry happens `A, B, C` — left to right, exactly the order they're written in the `with` statement — and exit happens `C, B, A` — the exact reverse. This is precisely the "last opened, first closed" (LIFO — last in, first out) discipline the doc describes, and it's the same guarantee your nested `try`/`finally` blocks would give you by hand, just automatic here.

**Flow diagram — why the order has to reverse, tied directly to the nested form the doc already shows is equivalent:**

```
with open("in.txt") as fin, open("out.txt", "w") as fout:
    BODY

is equivalent to:

with open("in.txt") as fin:            ← OUTER
    with open("out.txt", "w") as fout:   ← INNER
        BODY

Entering:  outer's __enter__ runs FIRST (you have to get INTO the
           outer "with" before you can even reach the inner one's
           own "with" line at all) — fin, THEN fout.

Exiting:   the INNER with-statement's own finally (its __exit__)
           runs FIRST, because it's the one whose try/finally block
           BODY is physically inside — fout's __exit__ must complete
           before control can even return to the OUTER with-
           statement's own finally, which runs __exit__ for fin
           LAST.

    ENTER fin (outer)
        ENTER fout (inner)
            BODY runs
        EXIT fout (inner)      ← closes first — it's the innermost
    EXIT fin (outer)             ← closes last — it's the outermost
```

This is exactly why the practical guidance about resources depending on each other holds: if `fout` somehow depended on `fin` still being open to finish its own cleanup safely, the reverse order guarantees `fin` is still open at the moment `fout` is closing — it's only closed *after* `fout` has already finished.

## 7. `contextlib` helpers worth knowing

`contextlib.suppress(*exceptions)` — a ready-made context manager for "run this, and if it raises one of these specific exception types, just ignore it":

```python
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove("maybe_doesnt_exist.txt")
# no crash even if the file was never there — but ANY OTHER exception still propagates normally
```

This is a cleaner, purpose-built version of the "catch a specific exception and do nothing" pattern from the exceptions doc — safer than a bare `except: pass`, since it only swallows the exact exception types you name.

`contextlib.closing(thing)` — for objects that have a `.close()` method but weren't written to support `with` directly (no `__enter__`/`__exit__` of their own):

```python
from contextlib import closing
import urllib.request

with closing(urllib.request.urlopen("https://example.com")) as page:
    html = page.read()
# page.close() guaranteed, even though urlopen's return value has no __enter__/__exit__ itself
```

### Running both of these for real

**Real, verified output** — `suppress`, tested both for the exception it's meant to catch (no crash) and a *different* exception type (confirmed to still propagate, exactly as the doc's comment promises):

```python
import os
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove("maybe_doesnt_exist.txt")
print("survived the suppress block")

try:
    with suppress(FileNotFoundError):
        raise TypeError("a different exception")
except TypeError as e:
    print("TypeError propagated through suppress, as expected:", e)
```

```
survived the suppress block
TypeError propagated through suppress, as expected: a different exception
```

**Real, verified output** — `closing()`, demonstrated with a stand-in object (to avoid depending on a live network request) that has a `.close()` method but genuinely no `__enter__`/`__exit__` of its own — exactly the situation `closing()` exists for:

```python
from contextlib import closing

class LegacyResource:
    def __init__(self):
        self.closed = False
        print("resource opened")
    def read(self):
        return "some data"
    def close(self):
        self.closed = True
        print("resource closed")

r = LegacyResource()
with closing(r) as page:
    print("read:", page.read())
print("r.closed after the with block:", r.closed)
```

```
resource opened
read: some data
resource closed
r.closed after the with block: True
```

**Flow diagram — what `closing(thing)` actually is, mechanically, tying it directly back to §3's hand-written `Timer` class:**

```
closing(thing) is ITSELF a tiny context manager, roughly equivalent
to writing this class yourself (this is genuinely close to the real
stdlib implementation):

    class closing:
        def __init__(self, thing):
            self.thing = thing

        def __enter__(self):
            return self.thing        ← hands back the ORIGINAL object,
                                        NOT itself — this is why
                                        "page" above is a LegacyResource,
                                        not a closing object

        def __exit__(self, *exc_info):
            self.thing.close()        ← the ENTIRE job: guarantee
                                          .close() gets called
            return False

with closing(r) as page:
    → closing(r) builds a wrapper AROUND r
    → __enter__ returns r itself → page IS r (same object, proven by
      "r.closed" correctly reflecting True afterward — there's no
      separate copy being closed)
    → leaving the block calls closing's __exit__, which calls
      r.close() for you
```

`LegacyResource` never had to implement `__enter__`/`__exit__` itself at all — `closing()` is a general-purpose adapter that bolts the standard `with`-cleanup guarantee onto *any* object that merely knows how to `.close()` itself, which is exactly the situation `urllib.request.urlopen(...)`'s return value is in (a real object with `.close()`, but no context-manager protocol of its own).

## 8. Real-world use cases

File handling is the one you've already used. Beyond that: **locks** — `with lock:` around code touching shared data in multithreaded code, guaranteeing the lock is released even if that code raises (forgetting to release a lock manually is a classic way to permanently deadlock a program). **Database transactions** — `with connection.begin():` style patterns that commit on success and roll back automatically on any exception, so a half-finished multi-step database change never gets left in an inconsistent state. **Temporary state changes** — `with decimal.localcontext():`, or `unittest.mock.patch(...)` used as a context manager, temporarily changing some global setting for the duration of the block and guaranteeing it's restored afterward no matter what happens inside. The common thread every single time: *some setup, some guaranteed teardown, no matter what happens in between.*

## 9. Interview-distilled

"What problem do context managers solve?" — guaranteed cleanup of a resource (file, lock, connection) even when the code using it raises an exception, without hand-writing `try`/`finally` every time.

"What does `with obj as x:` actually do?" — calls `obj.__enter__()`, binds its return value to `x`, runs the block, then calls `obj.__exit__(exc_type, exc_val, exc_tb)` unconditionally — even on an exception — passing the exception's info if there was one, or `None`s if not.

"What does returning `True` from `__exit__` do?" — suppresses the exception; execution continues normally after the `with` block instead of the exception propagating. Returning `False` (or nothing) lets it propagate as normal, after cleanup has still run.

"Two ways to write a context manager?" — a class with `__enter__`/`__exit__`, or a generator function decorated with `@contextlib.contextmanager`, where code before `yield` is the setup and code after it (inside `finally`) is the teardown.

---

## Practice questions

1. **Write a class-based context manager `Timer`**, matching §3, then deliberately raise an exception inside the `with` block and confirm `__exit__` still runs (add a `print` inside `__exit__` to prove it fires either way) and that the exception still propagates out afterward (wrap the whole `with` in a `try`/`except` outside it and catch it there).

2. **Write `SuppressValueError`-style class** (§4) that suppresses one specific exception type of your choosing but lets every other exception type through unchanged. Test both cases: raise the type you're suppressing (confirm the program continues normally afterward), then raise a *different* exception type inside the same kind of block (confirm it's NOT suppressed — it should still crash your program, or be caught by an outer `try` you wrap around it).

3. **Rewrite your `Timer` from Q1 using `@contextlib.contextmanager`** instead of a class (§5), yielding a dict (like the second `timer()` example) so you can still read the elapsed time afterward via `as t` / `t["elapsed"]`.

4. **Two files, one `with`.** Write two small text files yourself, then use the multi-context-manager form from §6 to open both at once and copy the contents of one into the other. Add a `print` statement right before your `with` block's `open()` calls and one right after the whole `with` block ends, so you can see cleanup has already happened by the time you reach the line after `with`.

5. **`contextlib.suppress` vs bare `try`/`except`.** Write a line of code that raises `KeyError` when looking up a missing dictionary key. Wrap it once in `contextlib.suppress(KeyError)`, and once in a plain `try: ... except KeyError: pass`. Both should behave identically for this case — then explain in a line or two, in your own words, why `suppress` is still considered the safer/cleaner default when you already know exactly which exception type you expect.

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for `*args`/`**kwargs` and functional tools (map/filter/reduce).*
