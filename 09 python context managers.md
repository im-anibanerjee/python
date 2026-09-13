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
