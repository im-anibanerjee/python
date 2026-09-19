# Topic 15 — Logging & Profiling, Deep Dive

*Phase 1, Advanced group — item 5 of 5, and the last topic before Git and the Wknd 1-3 build (asyncio, GIL, type hints/mypy, pytest, logging/profiling). Two genuinely separate tools bundled into one doc because they answer the same underlying question from opposite directions: logging tells you **what happened** in a running program, after the fact, in a structured and controllable way; profiling tells you **where the time actually went**, precisely, instead of guessing. Every snippet below was actually run for real.*

---

## 0. The picture to hold in your head before any code

`print()` is shouting something into a room and having it vanish the instant it's said — no record, no way to say "only tell me the urgent stuff," no way to send some shouts to one place and others somewhere else. **Logging is keeping a proper notebook instead**: every entry gets a timestamp and a severity label automatically, you can tell the notebook "only write down warnings and worse, ignore routine notes," and you can have two notebooks running at once — one on your desk showing only the urgent entries, one in a drawer recording absolutely everything, from the exact same stream of events.

Profiling is a different tool entirely: a **stopwatch with a clipboard**, standing next to your program while it runs, clicking the stopwatch every time control enters or leaves a function and writing down exactly how long each one took and how many times it was called. Instead of guessing "I bet the database call is the slow part," you get an itemized receipt telling you precisely which function actually consumed the time — which, as §7 shows directly, is very often *not* the function you'd have guessed.

---

## 1. Why `logging`, not just `print()`

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

logger = logging.getLogger(__name__)
logger.debug("this is a debug message")
logger.info("server started")
logger.warning("disk space low")
logger.error("failed to connect to database")
```

Real output:
```
2026-09-19 12:04:35,697 INFO __main__: server started
2026-09-19 12:04:35,697 WARNING __main__: disk space low
2026-09-19 12:04:35,697 ERROR __main__: failed to connect to database
```

Two things worth noticing immediately. First, **every line got a real timestamp and a labeled severity for free** — no manual `f"{datetime.now()} INFO: ..."` string-building, which is what you'd be doing by hand with `print()`. Second, and more important: **`logger.debug(...)` never printed anything at all.** `basicConfig(level=logging.INFO)` told the logging system "only actually emit messages at `INFO` severity or higher" — `DEBUG` is below that threshold, so it was silently, correctly dropped. `print()` has no concept of severity at all; every `print()` call is unconditionally the same "priority," so the only way to silence some of them is to physically delete or comment out the lines — with `logging`, you flip one setting (the level) and every `debug()` call across your entire codebase goes quiet at once, without touching a single one of them.

```
FLOW -- what logging.basicConfig(level=logging.INFO) actually gates
========================================================================
call site                 severity     level threshold (INFO)     emitted?
------------------------------------------------------------------------
logger.debug(...)          DEBUG        DEBUG < INFO                NO
logger.info(...)           INFO         INFO >= INFO                YES
logger.warning(...)        WARNING      WARNING >= INFO             YES
logger.error(...)          ERROR        ERROR >= INFO               YES
logger.critical(...)       CRITICAL     CRITICAL >= INFO            YES
```

The five standard levels, low to high severity: `DEBUG` (fine-grained diagnostic detail, noisy, off in production), `INFO` (routine confirmation that things are working — "server started"), `WARNING` (something unexpected, but the program is still working), `ERROR` (something failed), `CRITICAL` (the program itself may be unable to continue). Setting a level means "show me this severity and everything *above* it" — never below.

---

## 2. Handlers and formatters — sending different severities to different places

A **logger** decides *whether* a message is severe enough to go anywhere at all. A **handler** decides *where* a message that passed that check actually ends up — and each handler can apply its *own*, independent severity filter and its own formatting, on top of the logger's:

```python
import logging

logger = logging.getLogger("multi_handler_demo")
logger.setLevel(logging.DEBUG)   # logger itself allows everything through

console = logging.StreamHandler()
console.setLevel(logging.WARNING)   # console only shows WARNING and above
console.setFormatter(logging.Formatter("CONSOLE %(levelname)s: %(message)s"))

file_handler = logging.FileHandler("app.log", mode="w")
file_handler.setLevel(logging.DEBUG)   # file gets everything
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))

logger.addHandler(console)
logger.addHandler(file_handler)

logger.debug("debug message")
logger.info("info message")
logger.warning("warning message")
```

Real console output:
```
CONSOLE WARNING: warning message
```

Real contents of `app.log`:
```
2026-09-19 12:04:46,042 DEBUG: debug message
2026-09-19 12:04:46,042 INFO: info message
2026-09-19 12:04:46,043 WARNING: warning message
```

The exact same three `logger.debug/info/warning(...)` calls produced **two completely different results**, depending only on which handler received them: the console handler's own `WARNING` threshold dropped `debug` and `info`, so only one line reached the screen — but the file handler's `DEBUG` threshold let all three through, so the log file has the complete record. This is the entire point of separating loggers from handlers: it's genuinely common to want "show me only warnings and worse on my screen while I'm working, but keep a complete, permanent record of *everything* on disk in case I need to dig in later" — and this is exactly how that's configured, with zero changes to the actual `logger.debug/info/warning(...)` call sites.

```
FLOW -- one log call, two independent filters
==================================================
logger.debug("debug message")
  -> logger's own level check: DEBUG >= DEBUG?  yes -> passes to handlers
  -> console handler's level check: DEBUG >= WARNING?  NO  -> dropped here
  -> file handler's level check: DEBUG >= DEBUG?  yes -> written to app.log

A message must clear BOTH the logger's level AND a given handler's level
to reach that particular handler. Different handlers can disagree.
```

---

## 3. The logger hierarchy — dotted names and propagation

`logging.getLogger("app.database")` isn't just a string label — the dot makes it a **child** of a logger named `"app"`, which is itself a child of the **root logger**. By default, a message that a child logger accepts doesn't just go to the child's own handlers — it also **propagates upward** through every ancestor, all the way to the root:

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")

child = logging.getLogger("app.database")   # dotted name -- child of "app"
child.info("connected to db")
```

Real output:
```
app.database INFO: connected to db
```

Nobody ever explicitly configured a logger named `"app.database"` with a handler — `basicConfig()` only set up the **root** logger. The message still appeared, because it propagated all the way up from `"app.database"` to the root logger's own handler. This is genuinely convenient in real code: give every module its own logger (the universal convention is `logging.getLogger(__name__)`, so each module's logger is automatically named after that module), and configure handlers *once*, at the root — every module's messages find their way there automatically, with no per-module setup.

Propagation can be turned off per logger, which stops that bubbling-up entirely:

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")

child = logging.getLogger("app.database")
child.propagate = False   # stop it from bubbling up to the root logger's handler

child.info("connected to db - should NOT print, propagation disabled")
print("(nothing above this line means propagate=False worked)")
```

Real output:
```
(nothing above this line means propagate=False worked)
```

Nothing from `child.info(...)` printed at all — `propagate = False` cut off the path to the root logger's handler entirely, and `"app.database"` has no handlers of its own, so the message simply had nowhere to go. This is the tool for a specific, deliberate case (silencing an especially noisy third-party library's logger without silencing your own), not something to reach for by default — leave propagation on unless you have a specific reason to cut it.

---

## 4. `timeit` — measuring small pieces of code precisely

**`timeit` runs a snippet many times in a row and reports how long it actually took**, specifically built to avoid the pitfalls of a hand-rolled `time.perf_counter()` benchmark (one-off system noise, startup overhead) by repeating the measurement many times and being explicit about exactly what's being timed:

```python
import timeit

def build_with_plus(n):
    result = []
    for i in range(n):
        result = result + [i]   # creates a whole NEW list every iteration
    return result

def build_with_append(n):
    result = []
    for i in range(n):
        result.append(i)        # grows the same list in place
    return result

t_plus = timeit.timeit(lambda: build_with_plus(2000), number=50)
t_append = timeit.timeit(lambda: build_with_append(2000), number=50)

print(f"list + [x] each time: {t_plus:.4f}s for 50 runs")
print(f"list.append(x): {t_append:.4f}s for 50 runs")
print(f"append is {t_plus / t_append:.1f}x faster")
```

Real output:
```
list + [x] each time: 0.1443s for 50 runs
list.append(x): 0.0014s for 50 runs
append is 102.0x faster
```

A genuinely dramatic, real gap — **102 times faster**, not a rounding difference. `result = result + [i]` builds an entirely new list, copying every existing element, on *every single iteration* — the cost of each iteration grows as the list grows, making the whole loop quadratic (`O(n²)`) in the number of elements. `result.append(i)` grows the same list object in place, and Python's list implementation over-allocates space so most appends don't even need to resize anything — each append is (amortized) constant time, making the whole loop linear (`O(n)`). This is exactly the kind of real performance bug that "looks fine" reading the code casually (both versions are three lines, both are obviously correct) and only shows up as a genuine problem once `n` gets large — which is precisely why measuring it, rather than eyeballing it, matters.

---

## 5. `cProfile` — finding out where a whole program's time actually goes

`timeit` answers "how long does *this specific snippet* take?" — `cProfile` answers the bigger question: **"across this entire function call, which of the functions it calls are actually eating the time?"**

```python
import cProfile
import time

def slow_step():
    time.sleep(0.05)

def fast_step():
    total = 0
    for i in range(10000):
        total += i
    return total

def main():
    for _ in range(3):
        slow_step()
        fast_step()

cProfile.run("main()")
```

Real output:
```
         13 function calls in 0.152 seconds

   Ordered by: standard name

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.152    0.152 <string>:1(<module>)
        1    0.000    0.000    0.152    0.152 p1.py:13(main)
        3    0.000    0.000    0.150    0.050 p1.py:4(slow_step)
        3    0.001    0.000    0.001    0.000 p1.py:7(fast_step)
        1    0.000    0.000    0.152    0.152 {built-in method builtins.exec}
        3    0.150    0.050    0.150    0.050 {built-in method time.sleep}
        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
```

Read the two time columns carefully, because the distinction is the entire point of profiling: **`tottime`** is time spent *inside that function's own code*, excluding any functions it calls. **`cumtime`** is the *cumulative* time, including everything it called. `slow_step` has `tottime` of `0.000` — its own code (just calling `time.sleep`) does almost nothing — but a `cumtime` of `0.150`, because that's how long the thing it called (`time.sleep`) actually took. `time.sleep` itself is where the real `tottime` of `0.150` shows up. `fast_step`, despite looping 10,000 times, only cost `0.001` total across all 3 calls — genuinely negligible next to the sleep calls. **If you only looked at `fast_step`'s loop and assumed it was the bottleneck because it "does more work," you'd have been looking in completely the wrong place** — this is exactly why profiling beats guessing.

For a real codebase, you'd typically capture the same data into a `pstats.Stats` object and sort it explicitly, rather than reading the default listing top to bottom:

```python
import cProfile, pstats

profiler = cProfile.Profile()
profiler.enable()
main()
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats("tottime")
stats.print_stats(3)   # top 3 by time actually spent IN that function
```

Real output:
```
         11 function calls in 0.151 seconds

   Ordered by: internal time
   List reduced from 5 to 3 due to restriction <3>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        3    0.150    0.050    0.150    0.050 {built-in method time.sleep}
        3    0.001    0.000    0.001    0.000 p2.py:8(fast_step)
        1    0.000    0.000    0.151    0.151 p2.py:14(main)
```

Sorted by `tottime`, `time.sleep` is unambiguously first — which is exactly the honest, measured answer to "what's actually slow here," with no guessing involved.

---

## 6. Interview-distilled

"Why `logging` instead of `print()`?" — severity levels let you silence noisy messages globally with one setting instead of deleting `print()` calls; handlers let the same message go to multiple destinations (console, file) with independent filtering and formatting; every message gets structured metadata (timestamp, logger name, level) automatically (§1, §2).

"What's the difference between a logger and a handler?" — the logger decides whether a message is severe enough to be processed *at all*; each handler attached to it independently decides whether *that handler* actually emits it, and how it's formatted. A message needs to clear both checks to reach a given handler (§2).

"What does logger propagation mean?" — a message accepted by a child logger (e.g. `"app.database"`) also flows up to its parent loggers (`"app"`, then the root) by default, so configuring handlers once at the root captures everything below it without per-module setup. `logger.propagate = False` stops that (§3).

"`timeit` vs `cProfile` — when do you reach for which?" — `timeit` for comparing two small alternative implementations of the same thing head to head (§4). `cProfile` for finding which function, across a whole real call tree, is actually consuming the time — without needing to already suspect which one it is (§5).

"What's the difference between `tottime` and `cumtime` in a profile?" — `tottime` is time spent in that function's own code only; `cumtime` includes everything it calls. A function can have near-zero `tottime` but huge `cumtime` if it just calls something slow (§5) — that's the signal to look at what it called, not the function itself.

---

## Practice questions

1. **Prove the level gate, yourself.** Set up a logger with `basicConfig(level=logging.WARNING)`. Call `.debug()`, `.info()`, `.warning()`, and `.error()` on it. Confirm exactly which two calls actually print anything, and explain in a comment why the other two were silently dropped.

2. **Two handlers, two different views of the same events.** Attach a `StreamHandler` (console) set to `WARNING` and a `FileHandler` set to `DEBUG` to one logger whose own level is `DEBUG`. Log one message at each of the five standard levels. Confirm the console only shows the severe ones while the log file (open and check it) has the complete record.

3. **Propagation, proven both ways.** Create a child logger with a dotted name (e.g. `"app.worker"`) under a `basicConfig`-configured root. Confirm a message from the child reaches the root's handler with no configuration of the child logger at all. Then set `propagate = False` on the child and confirm the same message no longer appears anywhere.

4. **`timeit` a real before/after.** Pick two different ways of doing the same thing (e.g., building a string with `+=` in a loop vs. `"".join(...)`, or checking membership in a `list` vs. a `set` for a large collection). Time both with `timeit.timeit(..., number=...)` and report the real ratio between them in a comment.

5. **`cProfile` a function with a hidden bottleneck.** Write a function that calls two helper functions — one that's actually slow (e.g. `time.sleep(...)`, or a deliberately inefficient loop) and one that merely *looks* like it does more work (a tight loop over many iterations, but each iteration is cheap). Run it through `cProfile.run(...)`, and in a comment, identify which helper has the bigger `tottime` and confirm it's the one you designed to actually be slow — not necessarily the one with more code or more iterations.

---

*Same as always — write real code, run it, and paste your answers when ready. That closes out the Advanced group. Say "next" and I'll build the Git doc — the last topic before the Wknd 1-3 build itself.*
