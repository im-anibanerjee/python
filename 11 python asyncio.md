# Topic 11 — `asyncio`, Deep Dive

*Phase 1, Advanced group — item 1 of 5 (asyncio, GIL, type hints/mypy, pytest, logging/profiling). This is the first genuinely new execution model you've met so far — everything up to now ran one line after another, top to bottom. `asyncio` is about running many things that are each mostly *waiting*, without wasting time waiting for them one at a time.*

---

## 1. The problem `asyncio` solves

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

Each `fetch` call **blocks** — the entire program sits there doing nothing, waiting for that one network request, before it can even start the next one. But almost all of that 1 second per call isn't your CPU doing work — it's your program idly waiting on a network response. The CPU is free the entire time; nothing is stopping you from starting request 2 while request 1 is still waiting for its response. `asyncio` is Python's tool for doing exactly that: running many *I/O-bound* operations (network calls, file/database I/O, anything that spends most of its time waiting rather than computing) concurrently, on a single thread, by explicitly handing control back and forth between them whenever one of them is just waiting.

Important scope note up front: `asyncio` helps with **I/O-bound** waiting — things where the delay is external (network, disk, a database). It does **not** speed up **CPU-bound** work (heavy computation, tight loops crunching numbers) — for that, you'd need actual parallelism (multiple threads or processes), which is a different topic entirely (the GIL doc, right after this one, explains exactly why threads don't help with CPU-bound Python code the way you might expect).

## 2. `async def` — a coroutine function, not a running function

```python
async def greet():
    print("hello")
    return "done"

result = greet()
print(result)     # <coroutine object greet at 0x...> — NOT "hello", NOT "done"
```

This is the single most common first surprise: calling `greet()` does **not** run the function body — `print("hello")` never happens here. `async def` defines a **coroutine function**; calling it just builds a **coroutine object**, ready to run, exactly the same relationship as a generator function and the generator object it returns (`def gen(): yield 1` vs `gen()` — calling it builds an object, doesn't execute anything yet). A coroutine only actually *runs* when something explicitly drives it forward — either `await`ing it from inside another coroutine, or handing it to the event loop via `asyncio.run(...)`.

```python
import asyncio

async def greet():
    print("hello")
    return "done"

result = asyncio.run(greet())
print(result)     # hello
                        # done
```

`asyncio.run(coroutine)` is the standard entry point: it creates an event loop, runs the given coroutine to completion inside it, and returns whatever that coroutine returned. It's meant to be called *once*, at the top level of your program — not from inside another coroutine.

## 3. `await` — pausing one coroutine without blocking everything else

```python
import asyncio

async def fetch(name, delay):
    print(f"{name}: starting")
    await asyncio.sleep(delay)     # pause HERE, but let other things run meanwhile
    print(f"{name}: done")
    return f"data from {name}"

asyncio.run(fetch("a", 1))
# a: starting
# (1 second passes)
# a: done
```

`await` can only appear inside an `async def` function, and it means: "pause *this* coroutine right here until the thing I'm awaiting finishes — but don't block the entire program while waiting; let the event loop go run something else in the meantime, if there's anything else to run." This is mechanically the same pause-and-resume idea as `yield` in a generator (which is not a coincidence — coroutines are built on the same underlying machinery) — except a generator pauses waiting for `next()` to be called again by *you*, while a coroutine pauses waiting for the awaited operation (a sleep, a network response, anything) to actually finish, and the *event loop* is what resumes it automatically once that happens.

**`asyncio.sleep()` vs `time.sleep()` — this distinction matters enormously.** `time.sleep(1)` blocks the entire thread — the whole program, event loop included, freezes for that second, doing literally nothing else. `await asyncio.sleep(1)` pauses *only this one coroutine* and hands control back to the event loop, which is then completely free to go run any *other* coroutines that are ready to make progress during that second. Using `time.sleep()` inside an `async def` function is a genuine, common bug — it silently defeats the entire point of using `asyncio` in the first place, because it blocks everything rather than yielding control.

## 4. Running things concurrently — `asyncio.gather()`

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
    print(f"took {time.perf_counter() - start:.2f}s")

asyncio.run(main())
# a: starting
# b: starting
# c: starting
# (about 1 second passes, not 3)
# a: done
# b: done
# c: done
# ['data from a', 'data from b', 'data from c']
# took 1.00s
```

This is the payoff. `asyncio.gather(*coroutines)` starts all the given coroutines and runs them **concurrently** — all three print "starting" essentially immediately, because each one hits its `await asyncio.sleep(...)` and hands control straight back to the event loop, which immediately moves on to start the next one. All three sleeps are happening *during the same one second*, not stacked one after another — so the whole thing finishes in about 1 second total, not 3. `gather` waits for all of them to finish and returns their results as a list, in the same order they were passed in (regardless of which one actually finished first).

**Concurrency, not parallelism** — worth being precise about this distinction, since it's a real interview question. This is all still happening on a **single thread**. Nothing is running at the *exact same instant*; instead, the event loop is rapidly switching between coroutines, running each one until it hits an `await` and pauses, then moving to the next ready one — cooperative multitasking, not true simultaneous execution. It works beautifully for I/O-bound waiting (where nothing is actually happening on the CPU during the wait anyway), but it wouldn't speed up genuine CPU-bound computation at all, since there's only ever one thread doing the actual computing.

## 5. `asyncio.create_task()` — starting a coroutine without waiting for it immediately

```python
async def main():
    task = asyncio.create_task(fetch("a", 2))     # starts running NOW, in the background
    print("task started, doing other stuff")
    await asyncio.sleep(0.5)
    print("still doing other stuff")
    result = await task     # NOW wait for it to actually finish
    print(result)
```

`create_task(coroutine)` schedules a coroutine to start running immediately (as soon as the event loop next gets a chance) and hands you back a `Task` object you can hold onto — without blocking on it right away like a plain `await` would. You can go do other things, and `await task` later to actually collect its result once you need it. `gather` is really a convenience built on top of this same idea — it creates tasks for everything you pass it and awaits them all together.

## 6. `async with` and `async for` — the asynchronous versions of familiar syntax

```python
async def read_file_async():
    async with some_async_resource() as res:     # async version of a context manager
        data = await res.read()
    return data

async def process_stream():
    async for item in some_async_generator():    # async version of iterating
        print(item)
```

These exist because a regular context manager's `__enter__`/`__exit__` and a regular iterator's `__next__` are ordinary, blocking function calls — they can't themselves `await` anything internally. `async with` (using `__aenter__`/`__aexit__`) and `async for` (using `__aiter__`/`__anext__`) are the asynchronous counterparts, letting *entering*, *exiting*, or *fetching the next item* each involve their own `await` internally — used by real async libraries (database drivers, HTTP clients like `aiohttp`) where opening a connection or fetching the next row is itself an I/O-bound operation that should yield control while it waits, not block everything.

## 7. Where this actually shows up in real code

Making many independent API calls concurrently instead of one at a time (exactly the fetch example above, just with `aiohttp` or `httpx` instead of `requests`, since `requests` itself is synchronous/blocking and doesn't cooperate with an event loop at all — this is a genuine gotcha: mixing a blocking library like `requests` into async code silently reintroduces the exact blocking problem `asyncio` exists to avoid). Handling many simultaneous client connections in a web server (this is exactly why FastAPI — already on your resume roadmap — supports `async def` route handlers: so the server can serve other requests while one request's handler is waiting on a database query). Reading from multiple files or database connections concurrently. Anything that's fundamentally "start several slow, wait-heavy things and let them all progress at once" rather than "compute something fast."

## 8. Interview-distilled

"What problem does `asyncio` solve?" — running many I/O-bound (waiting-heavy) operations concurrently on a single thread, without the overhead of full multithreading, by explicitly yielding control at `await` points instead of blocking.

"What does `await` actually do?" — pauses the current coroutine until the awaited operation completes, and hands control back to the event loop in the meantime so it can run other ready coroutines, rather than blocking the whole program.

"Concurrency vs. parallelism, in the `asyncio` context?" — concurrency: multiple coroutines make progress by taking turns on one thread (what `asyncio` gives you). Parallelism: multiple things genuinely execute at the same instant, typically on multiple CPU cores (what `asyncio` does *not* give you — that needs multiprocessing, or threads for I/O-release cases, covered in the GIL doc next).

"Why is `time.sleep()` inside async code a bug?" — it blocks the entire thread, including the event loop itself, so no other coroutine can make progress during that time — it defeats the entire purpose of using `asyncio`, unlike `await asyncio.sleep()`, which yields control back.

"When would `asyncio` *not* help?" — CPU-bound work (heavy computation). Since it's all cooperative multitasking on one thread, there's no waiting to yield during — the CPU is genuinely busy the whole time, so nothing else gets a turn regardless.

---

## Practice questions

1. **Blocking vs non-blocking, side by side.** Write two versions of a 3-URL "fetch" simulation using `asyncio.sleep(1)` as the stand-in delay: one using plain sequential `await` calls (one after another, not `gather`), one using `asyncio.gather`. Time both with `time.perf_counter()` and confirm the sequential version takes roughly 3x as long as the concurrent one.

2. **Reproduce the `time.sleep()` bug on purpose.** Take your `gather`-based version from Q1 and swap one of the three `fetch` functions to use `time.sleep()` instead of `await asyncio.sleep()`. Run it, time it, and explain in your own words (as a comment) why the total time changes the way it does — tie it to the "blocks the whole event loop" behavior from §3.

3. **`create_task` and doing something else in between.** Write a coroutine that starts a `fetch("a", 2)` task with `create_task`, then — before awaiting that task — prints a message, awaits a short `asyncio.sleep(0.5)`, prints another message, and only *then* awaits the task to get its result. Confirm from the print order that the task genuinely was progressing in the background the whole time.

4. **Coroutine object vs. running it.** Write any `async def` function, call it without `await` or `asyncio.run`, and `print()` the result directly — confirm you get a `<coroutine object ...>`, not the function's actual printed output or return value. Then explain in a comment, in your own words, why calling an `async def` function doesn't run its body — tie it back to the generator-function comparison in §2.

5. **Order of completion vs. order passed in.** Using `asyncio.gather`, run three `fetch`-style coroutines with *different* delays (e.g. 3, 1, 2 seconds) so they finish in a different order than they were started. Confirm the `results` list `gather` returns is still in the original order you passed the coroutines in (not the order they actually completed) — and note in a comment which print statements *do* appear out of order (the "done" prints) versus which stay in original order (the final `results` list).

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for the GIL — the piece that explains exactly why threads behave the way they do in Python, and why `asyncio` (not threads) is the usual answer for I/O concurrency.*
