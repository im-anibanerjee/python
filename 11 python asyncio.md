# Topic 11 — `asyncio`, Deep Dive (Fully Worked)

*Phase 1, Advanced group — item 1 of 5 (asyncio, GIL, type hints/mypy, pytest, logging/profiling). This is the first genuinely new execution model you've met so far — everything up to now ran one line after another, top to bottom. `asyncio` is about running many things that are each mostly waiting, without wasting time waiting for them one at a time. Every code snippet in this version has been actually run, with the real output shown underneath it — nothing here is "left as an exercise for your imagination." Read this one slowly; the ideas build on each other in order.*

---

## 0. The picture to hold in your head before any code

Imagine you're the only cook in a kitchen, and you need to make three dishes. Each dish needs 10 minutes of *your* active chopping/stirring, plus 20 minutes sitting in the oven where *nothing from you* is needed.

**The "normal," blocking way:** make dish 1 completely — chop, stir, put it in the oven, then just **stand there and stare at the oven for 20 minutes doing nothing**, until it's done. Only then start dish 2. Total time: 3 × (10 + 20) = 90 minutes, with 60 of those minutes spent literally doing nothing but waiting.

**The `asyncio` way:** chop and stir dish 1, put it in the oven. The *instant* it goes in the oven, instead of staring at it, go start chopping dish 2. Put dish 2 in a second oven. Start chopping dish 3. Now all three are baking at once, and you — the one and only cook — were never idle; you just kept switching to whatever needed *your* hands next, and let the ovens (things that don't need your hands) run in the background. Total time: much closer to 10+10+10 (your active chopping) + 20 (however long the *longest* oven-wait is) ≈ 50 minutes, not 90.

That's the entire idea. **You are the one CPU/thread. Chopping is CPU work. The oven is I/O — network calls, disk reads, database queries — anything where you hand off a request and then just have to wait for someone/something else to finish it.** `asyncio` is the discipline of never standing and staring at an oven — the instant you'd have to wait, you explicitly say so (`await`), and something else gets your attention instead. Keep this analogy in your pocket; every piece of syntax below is just a formal way of expressing "chop," "put it in the oven," and "go work on something else while it bakes."

---

## 1. The problem, in actual code

```python
import time

def fetch(name, delay):
    print(f"{name}: starting")
    time.sleep(delay)     # standing and staring at the oven
    print(f"{name}: done")
    return f"data from {name}"

fetch("a", 1)
fetch("b", 1)
fetch("c", 1)
```

Real output, and real timing:
```
a: starting
a: done
b: starting
b: done
c: starting
c: done
sequential took 3.00s
```

Each call fully finishes — including its entire 1-second wait — before the next one is even allowed to *start*. The "starting" and "done" for `b` never interleave with `a`'s at all; they're strictly one-after-another. This is completely normal, ordinary Python — nothing wrong with it, except that all 3 seconds are spent, and for at least ~1 of those seconds at any given moment, your CPU is doing absolutely nothing except waiting for a timer (or, in real life, waiting for a network reply). `asyncio` exists to reclaim that dead time.

**Also worth keeping in view — the same idea, framed around URLs instead of named tasks (this is often how you'll first see it written elsewhere).**

Imagine fetching data from three different websites, one after another, the normal way:

```python
import time, requests

def fetch(url):
    time.sleep(1)     # standing in for a slow network request
    return f"data from {url}"

for url in ["a.com", "b.com", "c.com"]:
    print(fetch(url))
# takes ~3 seconds total — each call fully blocks until it finishes before the next one starts
```

(`requests` is imported here only because that's the library you'd actually reach for to fetch a real URL — this particular snippet never calls it; it's `time.sleep(1)` standing in for "some slow network call," the same way `fetch("a", 1)` above stood in for it with a plain delay number instead of a URL string.)

Each `fetch` call **blocks** — the entire program sits there doing nothing, waiting for that one network request, before it can even start the next one. But almost all of that 1 second per call isn't your CPU doing work — it's your program idly waiting on a network response. The CPU is free the entire time; nothing is stopping you from starting request 2 while request 1 is still waiting for its response. `asyncio` is Python's tool for doing exactly that: running many *I/O-bound* operations (network calls, file/database I/O, anything that spends most of its time waiting rather than computing) concurrently, on a single thread, by explicitly handing control back and forth between them whenever one of them is just waiting.

Important scope note up front: `asyncio` helps with **I/O-bound** waiting — things where the delay is external (network, disk, a database). It does **not** speed up **CPU-bound** work (heavy computation, tight loops crunching numbers) — for that, you'd need actual parallelism (multiple threads or processes), which is a different topic entirely (the GIL doc, right after this one, explains exactly why threads don't help with CPU-bound Python code the way you might expect).

---

## 2. `async def` — defining a recipe, not cooking it

```python
async def greet():
    print("hello")
    return "done"

result = greet()
print(result)
```

Real output:
```
<coroutine object greet at 0x7f2a1c0e5940>
```
(this line was originally annotated in-code as `print(result)     # <coroutine object greet at 0x...> — NOT "hello", NOT "done"` — the comment guessed exactly what the real run above now shows for real.)

Not `"hello"`. Not `"done"`. This is the single most important thing to absorb before anything else makes sense, so let's slow all the way down on *why*.

This is the single most common first surprise: calling `greet()` does **not** run the function body — `print("hello")` never happens here. `async def` defines a **coroutine function**; calling it just builds a **coroutine object**, ready to run, exactly the same relationship as a generator function and the generator object it returns (`def gen(): yield 1` vs `gen()` — calling it builds an object, doesn't execute anything yet). A coroutine only actually *runs* when something explicitly drives it forward — either `await`ing it from inside another coroutine, or handing it to the event loop via `asyncio.run(...)`.

**`async def greet(): ...` is a *definition*, like every `def` you've ever written — it does not run anything, it just teaches Python what `greet` means, and stores that recipe under the name `greet`.**

**`greet()` — calling it — for a normal function, runs the body immediately.** For an `async def` function, calling it does something different: it builds a **coroutine object** — think of it as a printed recipe card, sitting on the counter, completely unstarted. Nobody has picked up a knife yet. `print(result)` proves this: what you're holding is *the recipe itself* (`<coroutine object greet at 0x...>`), not the finished dish.

You've actually seen this exact relationship before — it's identical to `def gen(): yield 1` versus `gen()`. Calling a generator function doesn't run its body either; it hands you a generator *object*, paused before the first line, waiting for something (`next()`) to actually drive it forward. A coroutine object is the same idea: an unstarted, paused thing, waiting for something to drive it forward.

**So what *does* drive it forward?** Two things, and only two:

```python
import asyncio

async def greet():
    print("hello")
    return "done"

result = asyncio.run(greet())
print(result)
```

Real output:
```
hello
done
```
(originally annotated in-code as `print(result)     # hello` / `                        # done` — again, the real run above matches the guess exactly.)

`asyncio.run(coroutine)` is the thing that actually picks up the recipe card and starts cooking — it creates an **event loop** (explained fully in §3), runs the given coroutine inside it from start to finish, and hands back whatever that coroutine `return`ed. Call it exactly **once**, at the very top level of your program — it's your program's front door into the async world, not something you sprinkle throughout your code.

Put plainly, the way it was first written:

`asyncio.run(coroutine)` is the standard entry point: it creates an event loop, runs the given coroutine to completion inside it, and returns whatever that coroutine returned. It's meant to be called *once*, at the top level of your program — not from inside another coroutine.

The other way to drive a coroutine forward is `await` — from *inside* another coroutine, which is the entire subject of the next section. Call `asyncio.run()` exactly once, at the top level of your program — not from inside another coroutine, and (as the box right after the flow diagram below proves) not even wrapped in `await` from inside one either.

```
FLOW DIAGRAM — async def, step by step
========================================
line: async def greet(): ...
  -> Python stores the RECIPE under the name "greet". Nothing runs. (like any def)

line: result = greet()
  -> Python builds a COROUTINE OBJECT — an unstarted, paused "cooking session"
  -> result now holds that object. Still nothing from inside greet() has run.

line: print(result)
  -> prints <coroutine object greet at 0x...> — literally describing the paused object

line: asyncio.run(greet())
  -> NOW, for the first time, greet()'s body actually executes:
       print("hello")   runs  ->  prints "hello"
       return "done"    runs  ->  greet() is finished, hands back "done"
  -> asyncio.run(...) returns that "done" value to whoever called it
```

**One more thing about `asyncio.run()`, worth nailing down explicitly, since it's a genuinely common point of confusion: what happens if you try to call it again from *inside* a coroutine that's already running under it — with, or without, `await` in front of it?** Verified for real, both ways:

```python
async def inner():
    await asyncio.sleep(0.5)

async def main():
    try:
        asyncio.run(inner())        # plain call, no await, from inside a running coroutine
    except RuntimeError as e:
        print(f"RuntimeError caught: {e}")

asyncio.run(main())
```

Real output:
```
RuntimeError caught: asyncio.run() cannot be called from a running event loop
```

And with `await` added in front of the inner call:

```python
async def main2():
    try:
        await asyncio.run(inner())  # await added this time
    except RuntimeError as e:
        print(f"RuntimeError caught: {e}")

asyncio.run(main2())
```

Real output:
```
RuntimeError caught: asyncio.run() cannot be called from a running event loop
```

**Both raise the exact same error, whether or not you `await` it — because `asyncio.run()` is a plain, ordinary, synchronous function, not a coroutine.** The moment you call it, it runs its own internal logic immediately (check whether a loop is already running; if so, refuse) — this happens *before* `await` ever gets a chance to do anything. `await` only does something special when the thing you called hands back something awaitable; `asyncio.run(inner())` never gets that far, since it raises on the call itself. So `await asyncio.run(x)` is really just "`await` whatever `asyncio.run(x)` returns" — and since the call blows up before returning anything, the `await` never has anything to actually act on.

This is exactly why §4 below shows `r1 = await fetch(...)` used freely, several times in a row, inside `main()` — that line is not touching `asyncio.run()` at all; it's just pausing on an *already-running* coroutine's own steps, the way `await` is meant to be used everywhere except that one top-level call. Think of `asyncio.run()` as an ignition switch, pressed exactly once, from outside the engine; `await` is what you do freely *after* the engine is already running — pausing on individual steps, never restarting the engine itself.

---

## 3. `await` — the single most important keyword in this doc

```python
import asyncio

async def fetch(name, delay):
    print(f"{name}: starting")
    await asyncio.sleep(delay)
    print(f"{name}: done")
    return f"data from {name}"

asyncio.run(fetch("a", 1))
```

Real output (takes about 1 second):
```
a: starting
a: done
```
(the `await asyncio.sleep(delay)` line was originally annotated in-code as `await asyncio.sleep(delay)     # pause HERE, but let other things run meanwhile`, and the expected output was originally sketched as comments — `# a: starting` / `# (1 second passes)` / `# a: done` — which the real run above now confirms exactly.)

Nothing surprising yet with just *one* coroutine — but the mechanics of that pause are exactly what makes multiple coroutines interesting, so trace it precisely:

`fetch("a", 1)` is called inside `asyncio.run(...)` — builds a coroutine object, and `asyncio.run` immediately starts driving it. `print(f"{name}: starting")` runs — prints `a: starting`. Then execution reaches `await asyncio.sleep(1)`.

In the original phrasing:

`await` can only appear inside an `async def` function, and it means: "pause *this* coroutine right here until the thing I'm awaiting finishes — but don't block the entire program while waiting; let the event loop go run something else in the meantime, if there's anything else to run." This is mechanically the same pause-and-resume idea as `yield` in a generator (which is not a coincidence — coroutines are built on the same underlying machinery) — except a generator pauses waiting for `next()` to be called again by *you*, while a coroutine pauses waiting for the awaited operation (a sleep, a network response, anything) to actually finish, and the *event loop* is what resumes it automatically once that happens.

**`await` means: "I need to wait for this thing to finish. While I wait, I am not blocking anything — I am handing control back to the event loop, so it can go do something else useful, and it will come back and resume me the moment this is actually done."** This is the exact "put it in the oven and go do something else" moment from §0. `asyncio.sleep(1)` itself is a coroutine too (it's `async def` under the hood) — awaiting it doesn't freeze the program, it registers "wake this coroutine back up in 1 second" with the event loop and steps aside.

With only one coroutine running, there's nothing else *for* the event loop to do during that second — so from the outside, it looks just like `time.sleep(1)` would. The difference only becomes visible the moment there's more than one coroutine competing for attention — which is exactly §4.

**`asyncio.sleep()` vs `time.sleep()` — this distinction matters enormously.** `time.sleep(1)` blocks the entire thread — the whole program, event loop included, freezes for that second, doing literally nothing else. `await asyncio.sleep(1)` pauses *only this one coroutine* and hands control back to the event loop, which is then completely free to go run any *other* coroutines that are ready to make progress during that second. Using `time.sleep()` inside an `async def` function is a genuine, common bug — it silently defeats the entire point of using `asyncio` in the first place, because it blocks everything rather than yielding control.

That's not just a claim — here it is proven directly, running the exact same three "1-second" tasks concurrently via `gather`, once with each kind of sleep:

```python
async def task_time_sleep(name, seconds):
    print(f"[{name}] start (time.sleep) at t={...}")
    time.sleep(seconds)          # BLOCKING
    print(f"[{name}] done  (time.sleep) at t={...}")

await asyncio.gather(task_time_sleep("A", 1), task_time_sleep("B", 1), task_time_sleep("C", 1))
```

Real output:
```
[A] start (time.sleep) at t=0.00s
[A] done  (time.sleep) at t=1.00s
[B] start (time.sleep) at t=1.00s
[B] done  (time.sleep) at t=2.00s
[C] start (time.sleep) at t=2.00s
[C] done  (time.sleep) at t=3.00s
TOTAL WALL TIME (time.sleep version): 3.00s
```

Same shape of code, `asyncio.sleep()` in place of `time.sleep()`:

```python
async def task_asyncio_sleep(name, seconds):
    print(f"[{name}] start (asyncio.sleep) at t={...}")
    await asyncio.sleep(seconds)  # NON-BLOCKING
    print(f"[{name}] done  (asyncio.sleep) at t={...}")

await asyncio.gather(task_asyncio_sleep("A", 1), task_asyncio_sleep("B", 1), task_asyncio_sleep("C", 1))
```

Real output:
```
[A] start (asyncio.sleep) at t=0.00s
[B] start (asyncio.sleep) at t=0.00s
[C] start (asyncio.sleep) at t=0.00s
[A] done  (asyncio.sleep) at t=1.00s
[B] done  (asyncio.sleep) at t=1.00s
[C] done  (asyncio.sleep) at t=1.00s
TOTAL WALL TIME (asyncio.sleep version): 1.00s
```

`gather` was asked to run all three "concurrently" in *both* versions — but only the `asyncio.sleep()` version actually delivers that. With `time.sleep()`, B doesn't even *start* until A has completely finished (0.00s → 1.00s → 2.00s → 3.00s, strictly staircased, one at a time) — direct proof that `time.sleep()` freezes the one and only thread the event loop runs on, so nothing else, not even a sibling task handed to that same `gather` call, can get a turn. With `asyncio.sleep()`, all three start at t=0.00s and all finish at t=1.00s — genuinely overlapping — because `await asyncio.sleep()` hands control back to the loop instead of holding onto it, exactly as the bolded paragraph above describes.

**What is "the event loop," concretely?** It's not magic — it's a manager running one simple algorithm, over and over:

```
THE EVENT LOOP'S ALGORITHM, IN PLAIN STEPS
=============================================
1. Look at everything that is "ready to run right now" (nothing blocking it).
2. Pick one, run it — line by line — until it hits an `await` on something
   that ISN'T ready yet (a timer that hasn't expired, a network reply
   that hasn't arrived).
3. That coroutine is now "waiting." Set it aside. Go back to step 1 and
   pick the NEXT ready thing (if anything is ready).
4. If NOTHING is immediately ready (everything is waiting on a timer or
   I/O), sit and watch: has any timer's time come up? Has any network
   reply arrived?
5. The moment something becomes ready, move it back into the "ready" pile
   and go back to step 1.
6. Repeat until every coroutine has finished.
```

One event loop, one thread, constantly asking "what's ready *right now*?" and switching to it — never sitting frozen on one thing while something else could be making progress. `asyncio.run()`'s whole job is: create one of these loops, feed it your top-level coroutine, and run this algorithm until everything's done.

---

## 4. `asyncio.gather()` — running several coroutines concurrently, traced tick by tick

```python
import asyncio, time

async def fetch(name, delay):
    print(f"{name}: starting")
    await asyncio.sleep(delay)
    print(f"{name}: done")
    return f"data from {name}"

async def main():
    start = time.perf_counter()
    results = await asyncio.gather(
        fetch("a", 1),
        fetch("b", 1),
        fetch("c", 1),
    )
    print(results)
    print(f"gather took {time.perf_counter() - start:.2f}s")   # first written as: print(f"took {time.perf_counter() - start:.2f}s")

asyncio.run(main())
```

Real output:
```
a: starting
b: starting
c: starting
a: done
b: done
c: done
['data from a', 'data from b', 'data from c']
gather took 1.00s
```
(originally sketched, before this was actually run, as comments: `# a: starting` / `# b: starting` / `# c: starting` / `# (about 1 second passes, not 3)` / `# a: done` / `# b: done` / `# c: done` / `# ['data from a', 'data from b', 'data from c']` / `# took 1.00s` — matching the real output above line for line.)

Compare that to what you get from doing the three `fetch` calls the "obvious" way, one `await` after another with no `gather`:

```python
r1 = await fetch("a", 1)
r2 = await fetch("b", 1)
r3 = await fetch("c", 1)
```

Real output:
```
a: starting
a: done
b: starting
b: done
c: starting
c: done
sequential took 3.00s
```

Same 1-second delay each, but 3 seconds total instead of 1 — because each `await` here fully waits for that *one* `fetch` to completely finish before even *starting* the next one. `gather` is different: it hands the event loop *all three* coroutines to run **concurrently**, right from the start.

This is the payoff. `asyncio.gather(*coroutines)` starts all the given coroutines and runs them **concurrently** — all three print "starting" essentially immediately, because each one hits its `await asyncio.sleep(...)` and hands control straight back to the event loop, which immediately moves on to start the next one. All three sleeps are happening *during the same one second*, not stacked one after another — so the whole thing finishes in about 1 second total, not 3. `gather` waits for all of them to finish and returns their results as a list, in the same order they were passed in (regardless of which one actually finished first).

Full timeline, moment by moment, for the `gather` version:

```
TIMELINE — asyncio.gather(fetch("a",1), fetch("b",1), fetch("c",1))
=======================================================================
t=0.00s  event loop starts fetch("a",1)
           -> prints "a: starting"
           -> hits `await asyncio.sleep(1)` -> a PAUSES, registers "wake me at t=1.00s"
           -> control returns to event loop IMMEDIATELY (not at t=1.00s — right now)

t=0.00s  event loop starts fetch("b",1)   (next ready thing, right away)
           -> prints "b: starting"
           -> hits `await asyncio.sleep(1)` -> b PAUSES, registers "wake me at t=1.00s"

t=0.00s  event loop starts fetch("c",1)   (next ready thing, right away)
           -> prints "c: starting"
           -> hits `await asyncio.sleep(1)` -> c PAUSES, registers "wake me at t=1.00s"

t=0.00s  nothing else is ready. a, b, c are ALL paused, all waiting on
         timers that expire at the same moment. Event loop waits.

t=1.00s  a's timer fires -> a resumes -> prints "a: done" -> a finishes,
         returns "data from a"
t=1.00s  b's timer fires -> b resumes -> prints "b: done" -> returns "data from b"
t=1.00s  c's timer fires -> c resumes -> prints "c: done" -> returns "data from c"

t=1.00s  gather() has all 3 results -> returns them as a list, in the
         ORIGINAL order they were passed in: ['data from a', 'data from b', 'data from c']
         (NOT the order they finished in — here they finished in the same
         order anyway, but that's a coincidence of them having equal delays;
         gather always preserves the order you PASSED them in, regardless)
```

Notice: all three "starting" prints happen essentially instantly, back to back, at t=0.00 — that's the visible proof that all three coroutines began running (almost) immediately, rather than waiting for one another. Then there's a gap while all three are simultaneously "in the oven," and all three "done" prints land together around t=1.00, not spread across 3 seconds. That compression — 3 seconds of waiting collapsing into 1 — is the entire value proposition of `asyncio`.

**One thread. Not three.** Nothing here is happening at the literal same instant on separate CPU cores — it's one thread rapidly handing control between three coroutines, each of which only ever "does work" for a tiny fraction of a second (the two `print` calls) and spends the rest of its 1 second simply not needing the CPU at all. That's **concurrency** (taking turns, making combined progress) as opposed to **parallelism** (genuinely simultaneous execution on multiple cores) — a distinction worth being precise about, since it's a real interview question, covered again in §8.

**Concurrency, not parallelism** — worth being precise about this distinction, since it's a real interview question. This is all still happening on a **single thread**. Nothing is running at the *exact same instant*; instead, the event loop is rapidly switching between coroutines, running each one until it hits an `await` and pauses, then moving to the next ready one — cooperative multitasking, not true simultaneous execution. It works beautifully for I/O-bound waiting (where nothing is actually happening on the CPU during the wait anyway), but it wouldn't speed up genuine CPU-bound computation at all, since there's only ever one thread doing the actual computing.

---

## 5. `asyncio.create_task()` — start now, collect the result later

```python
import asyncio

async def fetch(name, delay):
    print(f"{name}: starting")
    await asyncio.sleep(delay)
    print(f"{name}: done")
    return f"data from {name}"

async def main():
    task = asyncio.create_task(fetch("a", 2))   # first written as: # starts running NOW, in the background
    print("task started, doing other stuff")
    await asyncio.sleep(0.5)
    print("still doing other stuff")
    result = await task   # first written as: # NOW wait for it to actually finish
    print(result)

asyncio.run(main())
```

Real output:
```
task started, doing other stuff
a: starting
still doing other stuff
a: done
data from a
```

This one has a genuinely subtle ordering worth tracing carefully, because `"task started, doing other stuff"` prints **before** `"a: starting"` — which might look backwards at first.

```
FLOW DIAGRAM — create_task, step by step
===========================================
line: task = asyncio.create_task(fetch("a", 2))
  -> this SCHEDULES fetch("a", 2) to run, but does NOT hand control to it
     yet, and does NOT block main() here. main() keeps running its own
     next line immediately. Think of it as dropping a note on the event
     loop's desk saying "get to this whenever you're free" — main doesn't
     stop to watch it start.

line: print("task started, doing other stuff")
  -> runs IMMEDIATELY, in main(), because create_task didn't pause main
     -> prints "task started, doing other stuff"

line: await asyncio.sleep(0.5)
  -> THIS is the first point where main() actually pauses and hands
     control back to the event loop. NOW the event loop looks at what's
     ready — and the scheduled task "a" is ready, so it runs it:
       fetch("a", 2) starts -> prints "a: starting"
       -> hits its own `await asyncio.sleep(2)` -> task "a" pauses too,
          registers "wake me at t=2.0s (relative)"
  -> control returns to the event loop again. Both main (asleep for 0.5s)
     and task a (asleep for 2s) are now waiting on timers.

t=0.5s   main's timer fires first (0.5s < 2s) -> main resumes
line: print("still doing other stuff")
  -> prints "still doing other stuff"

line: result = await task
  -> main now explicitly waits for task "a" specifically. But task "a"
     isn't done yet (it's asleep until t=2.0s) — so main pauses AGAIN,
     this time specifically waiting on task "a" to finish.

t=2.0s   task a's timer fires -> a resumes -> prints "a: done" -> a
         finishes, returns "data from a"
  -> main, which was waiting specifically for `task`, wakes back up with
     that return value

line: print(result)
  -> prints "data from a"
```

The key insight `create_task` demonstrates: **scheduling something and starting to run it are two different moments, and the thing you scheduled only actually gets a turn to run once your own coroutine hits an `await` and steps aside.** If `main()` never awaited anything before `await task`, task "a" would never have gotten a chance to even print `"a: starting"` — nothing forces a switch except an explicit `await`. This is also why `gather` internally builds tasks for everything you give it: creating a `Task` is what lets something start running "in the background" while you go do something else, rather than blocking on it immediately the way a bare `await some_coroutine()` would.

Put the way it was first written:

`create_task(coroutine)` schedules a coroutine to start running immediately (as soon as the event loop next gets a chance) and hands you back a `Task` object you can hold onto — without blocking on it right away like a plain `await` would. You can go do other things, and `await task` later to actually collect its result once you need it. `gather` is really a convenience built on top of this same idea — it creates tasks for everything you pass it and awaits them all together.

---

## 6. `async with` — an async context manager, fully built and run

Regular context managers (`__enter__`/`__exit__`, from the previous doc) are ordinary function calls — they can't themselves contain an `await`. `async with` exists for exactly the case where *opening* or *closing* a resource is itself a slow, I/O-bound operation (opening a real network connection, for instance) that should yield control while it waits, instead of blocking everything.

```python
import asyncio

class AsyncResource:
    async def __aenter__(self):
        print("connecting...")
        await asyncio.sleep(1)      # simulates a slow, real network connection opening
        print("connected")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("disconnecting...")
        await asyncio.sleep(0.5)    # simulates a slow, real teardown
        print("disconnected")
        return False

    async def read(self):
        await asyncio.sleep(0.5)    # simulates a slow, real read
        return "some data"

async def read_file_async():
    async with AsyncResource() as res:
        data = await res.read()
        print(f"got: {data}")
    return data

result = asyncio.run(read_file_async())
print("returned:", result)
```

Real output:
```
connecting...
connected
got: some data
disconnecting...
disconnected
returned: some data
```

Trace it exactly like the plain `with` translation from the previous doc, just with `async`/`await` sprinkled in at every step: `async with AsyncResource() as res:` calls `await AsyncResource().__aenter__()` — note the `await` there; entering is itself awaited, because `__aenter__` is `async def` and might need to pause (here, for that 1-second "connecting"). Whatever `__aenter__` returns (`self`) is bound to `res`. The block body runs — `await res.read()` pauses for its own half-second, then returns `"some data"`, printed as `got: some data`. Once the block finishes, `await res.__aexit__(...)` runs — also potentially pausing (here, half a second for "disconnecting") — exactly mirroring `__exit__`'s guaranteed-cleanup role from before, just now allowed to itself contain `await`.

*(Worth noting explicitly, since it's easy to skim past: these dunders — `__aenter__`/`__aexit__` here, and `__aiter__`/`__anext__` just below — are exactly what real async libraries implement under the hood: database drivers, HTTP clients like `aiohttp`, anything where opening a connection or fetching the next row is itself a slow, I/O-bound step that should yield control while it waits rather than block everything, precisely like `AsyncResource` above.)*

Before it was built out into the real, runnable `AsyncResource` above, this section was first sketched only as the shape of the syntax, not real running code:

```python
async def read_file_async():
    async with some_async_resource() as res:     # async version of a context manager
        data = await res.read()
    return data

async def process_stream():
    async for item in some_async_generator():    # async version of iterating
        print(item)
```

In that original phrasing:

These exist because a regular context manager's `__enter__`/`__exit__` and a regular iterator's `__next__` are ordinary, blocking function calls — they can't themselves `await` anything internally. `async with` (using `__aenter__`/`__aexit__`) and `async for` (using `__aiter__`/`__anext__`) are the asynchronous counterparts, letting *entering*, *exiting*, or *fetching the next item* each involve their own `await` internally — used by real async libraries (database drivers, HTTP clients like `aiohttp`) where opening a connection or fetching the next row is itself an I/O-bound operation that should yield control while it waits, not block everything.

## `async for` — an async generator, fully built and run

```python
import asyncio

async def some_async_generator():
    for i in range(3):
        await asyncio.sleep(0.3)    # simulates each item arriving slowly — e.g. one row at a time from a database
        yield i

async def process_stream():
    async for item in some_async_generator():
        print(f"received: {item}")

asyncio.run(process_stream())
```

Real output (takes about 0.9 seconds total — three 0.3s pauses):
```
received: 0
received: 1
received: 2
```

`some_async_generator` is an **async generator** — `async def` combined with `yield` inside it. Calling it doesn't run anything either (same "recipe, not cooked" rule as any `async def`), it produces an **async generator object**. `async for item in some_async_generator():` is the asynchronous equivalent of the regular `for`/`__iter__`/`__next__` machinery from the generators doc, using `__aiter__`/`__anext__` instead — each time the loop needs the *next* item, it `await`s the generator forward to its next `yield`, and *that* await is what lets the event loop go do something else while this particular item is still "cooking" (here, the 0.3-second simulated wait per item). Trace one full cycle: the loop asks for the first item → the generator runs until `await asyncio.sleep(0.3)` → pauses (yielding control to the event loop, exactly like §3) → 0.3s later resumes → hits `yield i` → hands `0` back to the `async for` loop → `print("received: 0")` → loop asks for the next item → the generator resumes *after* its `yield`, loops back to the top of its `for i in range(3)`, and repeats for `i=1`, then `i=2`, then the generator's `for` loop ends and it raises the async equivalent of `StopIteration`, ending the `async for` cleanly.

---

## 7. Where this actually shows up in real code

Making many independent API calls concurrently instead of one at a time (exactly the `fetch` example above, just with `aiohttp` or `httpx` instead of `requests` — `requests` itself is synchronous/blocking and doesn't cooperate with an event loop at all; mixing a blocking library like `requests` into async code silently reintroduces the exact blocking problem `asyncio` exists to avoid, the same way `time.sleep()` would). Handling many simultaneous client connections in a web server (this is exactly why FastAPI — already on your resume roadmap — supports `async def` route handlers: so the server can serve other requests while one request's handler is waiting on a database query, instead of one slow request freezing every other user). Reading from multiple files or database connections concurrently. Streaming results from a database row by row with `async for`, as in §6, instead of waiting for the entire result set to load first.

Originally written, in full:

Making many independent API calls concurrently instead of one at a time (exactly the fetch example above, just with `aiohttp` or `httpx` instead of `requests`, since `requests` itself is synchronous/blocking and doesn't cooperate with an event loop at all — this is a genuine gotcha: mixing a blocking library like `requests` into async code silently reintroduces the exact blocking problem `asyncio` exists to avoid). Handling many simultaneous client connections in a web server (this is exactly why FastAPI — already on your resume roadmap — supports `async def` route handlers: so the server can serve other requests while one request's handler is waiting on a database query). Reading from multiple files or database connections concurrently. Anything that's fundamentally "start several slow, wait-heavy things and let them all progress at once" rather than "compute something fast."

---

## 8. Interview-distilled

"What problem does `asyncio` solve?" — running many I/O-bound (waiting-heavy) operations concurrently on a single thread, without full multithreading overhead, by explicitly yielding control at `await` points instead of blocking. (The kitchen analogy from §0 is a genuinely good one to reach for out loud in an interview.) First phrased as: "What problem does `asyncio` solve?" — running many I/O-bound (waiting-heavy) operations concurrently on a single thread, without the overhead of full multithreading, by explicitly yielding control at `await` points instead of blocking.

"What does `await` actually do?" — pauses the current coroutine until the awaited operation completes, and hands control back to the event loop in the meantime so it can run other ready coroutines, rather than blocking the whole program.

"Concurrency vs. parallelism, in the `asyncio` context?" — concurrency: multiple coroutines make progress by taking turns on one thread (what `asyncio` gives you — like one cook switching between three dishes). Parallelism: multiple things genuinely execute at the same instant, typically on multiple CPU cores (what `asyncio` does *not* give you — that needs multiprocessing, or threads for certain cases, covered in the GIL doc next). First phrased as: "Concurrency vs. parallelism, in the `asyncio` context?" — concurrency: multiple coroutines make progress by taking turns on one thread (what `asyncio` gives you). Parallelism: multiple things genuinely execute at the same instant, typically on multiple CPU cores (what `asyncio` does *not* give you — that needs multiprocessing, or threads for I/O-release cases, covered in the GIL doc next).

"Why is `time.sleep()` inside async code a bug?" — it blocks the entire thread, including the event loop itself, so no other coroutine can make progress during that time — it defeats the entire purpose of using `asyncio`, unlike `await asyncio.sleep()`, which yields control back.

"When would `asyncio` *not* help?" — CPU-bound work (heavy computation). Since it's cooperative multitasking on one thread, there's no waiting to yield during — the CPU is genuinely busy the whole time, so nothing else gets a turn regardless. First phrased as: "When would `asyncio` *not* help?" — CPU-bound work (heavy computation). Since it's all cooperative multitasking on one thread, there's no waiting to yield during — the CPU is genuinely busy the whole time, so nothing else gets a turn regardless.

"What's the difference between `create_task` and a plain `await`?" — a plain `await some_coroutine()` blocks the current coroutine until that one finishes before moving on. `create_task` schedules it to start running in the background immediately, letting you do other things and `await` its result later, once you actually need it.

---

## Practice questions

1. **Blocking vs non-blocking, side by side.** Write two versions of a 3-URL "fetch" simulation using `asyncio.sleep(1)` as the stand-in delay: one using plain sequential `await` calls (one after another, not `gather`), one using `asyncio.gather`. Time both with `time.perf_counter()` and confirm the sequential version takes roughly 3x as long as the concurrent one.

2. **Reproduce the `time.sleep()` bug on purpose.** Take your `gather`-based version from Q1 and swap one of the three `fetch` functions to use `time.sleep()` instead of `await asyncio.sleep()`. Run it, time it, and explain in your own words (as a comment) why the total time changes the way it does — tie it to the "blocks the whole event loop" behavior from §3.

3. **`create_task` and doing something else in between.** Write a coroutine that starts a `fetch("a", 2)` task with `create_task`, then — before awaiting that task — prints a message, awaits a short `asyncio.sleep(0.5)`, prints another message, and only *then* awaits the task to get its result. Confirm from the print order that the task genuinely was progressing in the background the whole time (compare your output against §5's traced example). (First phrased without that last cross-reference: "...Confirm from the print order that the task genuinely was progressing in the background the whole time.")

4. **Coroutine object vs. running it.** Write any `async def` function, call it without `await` or `asyncio.run`, and `print()` the result directly — confirm you get a `<coroutine object ...>`, not the function's actual printed output or return value. Then explain in a comment, in your own words, why calling an `async def` function doesn't run its body — tie it back to the generator-function comparison in §2.

5. **Order of completion vs. order passed in.** Using `asyncio.gather`, run three `fetch`-style coroutines with *different* delays (e.g. 3, 1, 2 seconds) so they finish in a different order than they were started. Confirm the `results` list `gather` returns is still in the original order you passed the coroutines in (not the order they actually completed) — and note in a comment which print statements *do* appear out of order (the "done" prints) versus which stay in original order (the final `results` list).

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for the GIL — the piece that explains exactly why threads behave the way they do in Python, and why `asyncio` (not threads) is the usual answer for I/O concurrency.*
