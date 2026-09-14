# Topic 12 — The GIL (Global Interpreter Lock), Deep Dive

*Phase 1, Advanced group — item 2 of 5 (asyncio, GIL, type hints/mypy, pytest, logging/profiling). This doc directly answers the question the asyncio doc kept deferring: "why doesn't threading just solve concurrency the normal way in Python, and why does `asyncio` even need to exist?" Every code snippet below has actually been run on this machine, real output pasted underneath — including a couple of results that are genuinely a little surprising the first time you see them.*

---

## 0. The picture to hold in your head before any code

Imagine a meeting room with one microphone, and several people (threads) who each want to say something. There are multiple people, and technically multiple mouths capable of talking at the exact same instant — but the room's rule is **only whoever is holding the mic may speak**, no exceptions, no matter how many people are physically capable of talking right now.

If everyone's turn is short, the mic gets passed around fast enough that from a distance it *sounds* like a lively conversation — lots of voices, lots of activity. But at any single instant, exactly one voice is actually coming out of that microphone. That's the GIL: it doesn't stop you from having multiple threads: it stops more than one of them from actually *executing Python bytecode* at the same literal instant, no matter how many CPU cores your machine has sitting idle.

Now the important twist, the one that explains almost everything else in this doc: **if someone's turn involves stepping outside the room to go check something (a network call, a disk read, a `sleep`), they hand the mic back while they're gone**, and someone else gets to use it. That's why threads genuinely help with *waiting*. But if someone's turn is "solve this long math problem out loud, in my own head, without stopping" (CPU-bound work), handing them the mic and then trying to interrupt them to give it to someone else accomplishes nothing — nobody else can usefully speak anyway, since the room's only real bottleneck (one voice, one mic) was never about waiting in the first place.

---

## 1. What the GIL literally is — and the first proof that threads don't parallelize CPU work

**In one sentence: the GIL is a single lock inside the CPython interpreter that allows only one thread to execute Python bytecode at a time, for the entire process, regardless of how many CPU cores are available.** "CPython" matters here — this is an implementation detail of the reference interpreter (the one you're almost certainly running), not a property of the Python *language* itself (other implementations, like Jython or the free-threaded build in §6, make different choices).

Prove it directly — a genuinely CPU-bound task (no waiting at all, just the CPU counting down), run four ways:

```python
import time, threading, multiprocessing

N = 20_000_000

def count_down(n):
    while n > 0:
        n -= 1

# 1. one call, one thread — the baseline unit of work
start = time.perf_counter()
count_down(N)
print(f"single call, one thread: {time.perf_counter()-start:.2f}s")

# 2. two calls, back to back, one thread — the real baseline to beat
start = time.perf_counter()
count_down(N); count_down(N)
print(f"two calls, sequential, one thread: {time.perf_counter()-start:.2f}s")

# 3. two calls, two threads
start = time.perf_counter()
t1 = threading.Thread(target=count_down, args=(N,))
t2 = threading.Thread(target=count_down, args=(N,))
t1.start(); t2.start()
t1.join(); t2.join()
print(f"two calls, two threads:        {time.perf_counter()-start:.2f}s")

# 4. two calls, two processes
start = time.perf_counter()
p1 = multiprocessing.Process(target=count_down, args=(N,))
p2 = multiprocessing.Process(target=count_down, args=(N,))
p1.start(); p2.start()
p1.join(); p2.join()
print(f"two calls, two processes:      {time.perf_counter()-start:.2f}s")
```

Real output (2-core machine):
```
single call, one thread: 0.51s
two calls, sequential, one thread: 0.97s
two calls, two threads:        1.00s
two calls, two processes:      0.56s
```

Sit with that for a second, because it's the entire point of this doc: **two threads took exactly as long as doing the same two calls sequentially in one thread (1.00s ≈ 0.97s) — threading bought nothing.** Two *processes*, on the other hand, finished in almost the same time as a *single* call (0.56s ≈ 0.51s) — genuinely running both at once, on separate cores, cutting the total time roughly in half. That gap is the GIL, made visible: threads inside one Python process are still fighting over that one microphone, so two threads doing pure CPU work run no faster than one thread doing both jobs one after another. Processes have no such lock to share — each process gets its own Python interpreter, its own GIL, its own everything — so they really do run in parallel.

**Worth pausing on `start()` and `join()` themselves, since every demo in this doc leans on them.** `t.start()` actually creates the OS-level thread and tells it to begin running its target function *right now, in the background* — then returns **immediately**, without waiting for that function to finish. That's why `t1.start(); t2.start()` above fires off both threads almost instantly, one right after the other, rather than waiting for the first one to complete before starting the second. `t.join()` does the opposite job: it **blocks the calling thread** (here, the main thread doing the timing) until that specific thread has completely finished running. `t1.join(); t2.join()` is what makes the `time.perf_counter()` measurement honest — without those two lines, `print(...)` would run immediately after `start()`, while both threads were still busy computing, and you'd measure something close to 0 seconds instead of the real elapsed time. The same two-method pattern (`start()` to kick something off without waiting, `join()` to actually wait for it) reappears with `multiprocessing.Process` right below, for exactly the same reason.

**A genuine Windows-specific gotcha, worth flagging before you run this yourself:** on Windows, `multiprocessing.Process(...)` code needs to sit inside a `if __name__ == "__main__":` guard. Windows has no `fork()`, so Python starts new processes with the `spawn` method instead — the new process re-imports your script from scratch to set itself up. Without the guard, that re-import re-executes your top-level `Process(...).start()` line too, which spawns *another* process, which re-imports the script again, and so on — either a runtime error or runaway process spawning, depending on exactly what's at module level. (This doc's code was run on Linux, where `fork()` is the default and the guard isn't required — but always add it anyway, since it's required on Windows and harmless everywhere else.)

---

## 2. Why does this lock exist at all?

It's tempting to assume the GIL is just a historical mistake nobody's fixed — it isn't, and understanding *why* it's there is itself a real interview question. CPython manages memory for every object (lists, dicts, your own class instances, even small integers) with **reference counting** — a plain integer on the object itself, incremented every time something else starts referencing it, decremented every time a reference goes away; when it hits zero, the object is freed. That counter gets touched *constantly* — practically every line of Python code increments or decrements a refcount somewhere behind the scenes.

If two threads could truly run Python bytecode at the exact same instant, two threads could increment/decrement the *same* object's refcount at the exact same instant — a classic race condition (exactly the kind you'll see reproduced in §4), except this time corrupting Python's own memory-management bookkeeping, leading to objects being freed while still in use, or never being freed at all. The GIL is CPython's blunt, simple solution: instead of putting a separate, fine-grained lock around every single object's refcount (which would be correct, but catastrophically slow — one lock acquisition per refcount change, everywhere, all the time), just use **one big lock** around the entire interpreter. It's a genuinely reasonable trade-off for a single-threaded-by-default language runtime: it keeps single-threaded code fast (the common case) at the cost of preventing true multi-core parallelism for multi-threaded CPU-bound code (§6 covers the ongoing, real effort to finally remove this trade-off).

---

## 3. Where the GIL actually gets released — threads and I/O-bound work

Section 1 showed threads doing *nothing* for CPU-bound work. Now do the same experiment with I/O-bound work instead — the same kind of "waiting, not computing" task the asyncio doc built its entire case around:

```python
import time, threading

def fetch(name, delay):
    print(f"{name}: starting")
    time.sleep(delay)     # stand-in for a blocking network call
    print(f"{name}: done")

# sequential
start = time.perf_counter()
fetch("a", 1); fetch("b", 1); fetch("c", 1); fetch("d", 1)
print(f"sequential took: {time.perf_counter()-start:.2f}s")

# threaded
start = time.perf_counter()
threads = [threading.Thread(target=fetch, args=(name, 1)) for name in "abcd"]
for t in threads: t.start()
for t in threads: t.join()
print(f"threaded took:   {time.perf_counter()-start:.2f}s")
```

Real output:
```
a: starting
a: done
b: starting
b: done
c: starting
c: done
d: starting
d: done
sequential took: 4.00s

a: starting
b: starting
c: starting
d: starting
a: done
b: done
c: doned: done

threaded took:   1.00s
```

Four seconds, sequentially, collapses to about one second with four threads — a real speedup this time, unlike §1. **`time.sleep()` (and, underneath, every genuinely blocking I/O call — a socket read, a file read, a database driver waiting on a network reply) is implemented in C, and CPython's C-level implementation of blocking calls like this one explicitly releases the GIL before it starts waiting, then reacquires it once it's done.** That's the mic being handed back the instant someone says "I'm just going to go wait outside for a bit" — everyone else in the room is now free to talk. This is exactly the same underlying release-the-lock-while-waiting idea `asyncio`'s `await` relies on, just achieved with OS threads and a lock instead of coroutines and an event loop.

(Notice the genuinely unplanned bonus proof sitting right there in the real output: `c: doned: done` — that's `c`'s `"c: done"` and `d`'s `"d: done"` print calls landing on the terminal at almost the same instant and getting interleaved character-by-character, because two separate threads really were writing to stdout close enough in time that the OS-level line buffering caught them mid-write. You could not get that garbled line from truly sequential code — it's live evidence that these threads were genuinely running independently, not just an illusion.)

---

## 4. The GIL stops parallel bytecode execution — it does *not* make your code thread-safe

This is the single most commonly misunderstood consequence of the GIL, and it's worth being precise about it, because "there's a global lock, so my code can't have race conditions" is a **wrong** conclusion many people draw from everything said so far.

The GIL guarantees only one thread runs Python bytecode *at a time* — but a single line of Python, like `counter += 1`, is not *one* bytecode instruction. It's several: roughly, **load** the current value of `counter`, **add** 1 to it, then **store** the result back into `counter`. The GIL can switch to a different thread *between* any of those steps — it does not guarantee that "read, modify, write" happens as one uninterruptible unit. Prove it, by forcing that switch to land in exactly the worst possible spot on purpose:

```python
import threading, time

counter = 0
TIMES = 2000

def inc_racy(times):
    global counter
    for _ in range(times):
        temp = counter        # READ
        time.sleep(0)          # deliberately hand the GIL to the other thread right here
        counter = temp + 1     # WRITE, based on whatever `temp` was BEFORE the handoff

t1 = threading.Thread(target=inc_racy, args=(TIMES,))
t2 = threading.Thread(target=inc_racy, args=(TIMES,))
t1.start(); t2.start()
t1.join(); t2.join()
print(f"expected: {TIMES*2}, actual (racy): {counter}")
```

Real output:
```
expected: 4000, actual (racy): 2000
```

Exactly half the increments got lost — every single one, in fact, in this run. `time.sleep(0)` is a real, if extreme, way of saying "yield the GIL right now" — and forcing that yield to sit exactly between the READ and the WRITE guarantees the worst case every single time:

```
TIMELINE — two threads, one shared `counter`, no lock
=========================================================
counter = 0

t1: temp = counter          -> t1's temp is 0
t1: time.sleep(0)           -> t1 hands the GIL to t2, right here, mid-increment
t2: temp = counter          -> t2's temp is ALSO 0 (t1 hasn't written anything back yet)
t2: time.sleep(0)           -> t2 hands the GIL back to t1
t1: counter = temp + 1      -> counter becomes 0 + 1 = 1
t2: counter = temp + 1      -> counter becomes 0 + 1 = 1 (OVERWRITES t1's update — using
                                t2's own stale temp, not the 1 that t1 just wrote)

net effect: TWO increments happened, but counter only went up by ONE.
This is a lost update — and it happened even though the GIL guarantees
only one thread was ever running bytecode at any instant. The GIL
protects individual bytecode instructions; it says nothing about
sequences of several instructions across two threads.
```

The fix is the same one you'd reach for in any language with real threads: an explicit lock around the whole read-modify-write sequence, so no other thread can interleave in the middle of it:

```python
counter = 0
lock = threading.Lock()

def inc_locked(times):
    global counter
    for _ in range(times):
        with lock:
            temp = counter
            time.sleep(0)
            counter = temp + 1

t1 = threading.Thread(target=inc_locked, args=(TIMES,))
t2 = threading.Thread(target=inc_locked, args=(TIMES,))
t1.start(); t2.start()
t1.join(); t2.join()
print(f"expected: {TIMES*2}, actual (locked): {counter}")
```

Real output:
```
expected: 4000, actual (locked): 4000
```

`with lock:` guarantees the entire read-modify-write happens as one block — if a thread tries to enter the `with lock:` body while the other thread is already inside it, it blocks (genuinely waits, not "does something else") until the lock is free. The GIL switching threads mid-block no longer matters, because no *other* thread holding the same lock can act on `counter` until the first one is completely done with it. **The GIL and a `threading.Lock` are solving two different problems that sound similar: the GIL protects the interpreter's own internals (refcounts, etc.) at the single-bytecode level; a `Lock` protects *your* multi-step logic at whatever level *you* define as one unit of work.**

---

## 5. Threading vs. multiprocessing vs. asyncio — three tools, three different jobs

Everything above points to one decision table, and it's a genuinely common interview question phrased as "how would you speed this up?":

```
                  |  helps CPU-bound?  |  helps I/O-bound?  |  true parallelism?  |  overhead
------------------|--------------------|---------------------|----------------------|------------------------------
threading         |  No (GIL, §1)      |  Yes (§3)           |  No — one GIL, one   |  low-ish; shared memory,
                  |                    |                     |  process             |  but races need locks (§4)
------------------|--------------------|---------------------|----------------------|------------------------------
multiprocessing   |  Yes (§1)          |  Yes, but wasteful  |  Yes — separate      |  high; separate interpreters/
                  |                    |  (heavy for this)   |  processes, own GILs |  memory, slow to start, needs
                  |                    |                     |                      |  IPC/pickling to share data
------------------|--------------------|---------------------|----------------------|------------------------------
asyncio           |  No (still one     |  Yes (prev. doc)    |  No — one thread,    |  very low; no OS threads/
                  |  thread, §0 of the |                     |  cooperative only    |  processes at all, but every
                  |  asyncio doc)      |                     |                      |  library in the chain must
                  |                    |                     |                      |  cooperate (be async-aware)
```

The rule of thumb this table collapses to: **CPU-bound → multiprocessing** (you need genuinely separate interpreters running on separate cores, so pay the process-startup and data-sharing overhead for it). **I/O-bound, and you're stuck with blocking libraries → threading** (cheaper than processes, and blocking calls release the GIL anyway, so you get real overlap). **I/O-bound, and you control the whole stack (or can use async-native libraries like `aiohttp`) → `asyncio`** (cheapest of all — no OS-level threads or processes, just one thread cooperatively juggling many waiting operations, exactly as the previous doc covered end to end).

---

## 6. The free-threaded build — is Python actually removing the GIL?

Worth being current on this, since it's a real, ongoing change rather than a hypothetical: **starting with Python 3.13, CPython officially ships an optional "free-threaded" build that disables the GIL entirely**, tracked as [PEP 703](https://docs.python.org/3/howto/free-threading-python.html). It's a real, officially supported build option — not a forgotten experiment — available as separate installers on python.org (look for the `3.13t` / `3.14t` "t" suffix, for "threaded"/free-threaded) or via `./configure --disable-gil` building from source; it continues to exist in 3.14 as well, still opt-in rather than the project-wide default build. With the GIL genuinely disabled, threads running pure CPU-bound Python code can execute truly in parallel across cores — the exact "two threads, ~1.00s, no speedup" result from §1 would instead look much closer to the two-*process* result, without needing `multiprocessing` at all.

It isn't free, though, which is exactly why it isn't the default yet: independently reported benchmarks put single-threaded code roughly **1-8% slower** on a free-threaded build (the machinery that used to be "just don't worry about it, the GIL protects you" now has to do real, finer-grained locking work per-object instead), plus meaningfully higher memory use (larger per-object headers, since every object now needs its own thread-safe refcounting machinery instead of relying on the GIL for that). C extensions that haven't been explicitly updated to declare themselves free-threading-safe will silently force the GIL back on at import time (with a warning) — so the ecosystem-wide migration is still very much in progress, tracked at community sites like the [Python Free-Threading Guide](https://py-free-threading.github.io/).

You can check, for real, whether any given Python you're running is a free-threaded build:

```python
import sys, sysconfig
print("version:", sys.version)
print("Py_GIL_DISABLED:", sysconfig.get_config_var("Py_GIL_DISABLED"))
print("has _is_gil_enabled:", hasattr(sys, "_is_gil_enabled"))
```

Real output, on this machine:
```
version: 3.11.15 (main, Mar  3 2026, 09:26:23) [GCC 13.3.0]
Py_GIL_DISABLED: None
has _is_gil_enabled: False
```

This is an entirely ordinary, standard-GIL build (3.11, well before the free-threaded option even existed as of 3.13) — every demo in this doc, including §1's "threads don't help CPU-bound work" result, is exactly what you'd expect from the GIL as described throughout. A free-threaded 3.13+/3.14 build would report an actual `True`/`False` from `sys._is_gil_enabled()` instead of that attribute simply not existing, and `Py_GIL_DISABLED` would be `1` for a build that *supports* free-threading at all (with the GIL itself separately re-enable-able at runtime via `python -X gil=1` or `PYTHON_GIL=1`, even on such a build — the option to fall back exists precisely because of that C-extension-compatibility gap).

Sources: [Python docs — free-threading HOWTO](https://docs.python.org/3/howto/free-threading-python.html), [Python Free-Threading Guide](https://py-free-threading.github.io/), [What's new in Python 3.14](https://docs.python.org/3/whatsnew/3.14.html).

---

## 7. Interview-distilled

"What is the GIL, in one sentence?" — a lock inside CPython that only lets one thread execute Python bytecode at a time, for the whole process, no matter how many CPU cores exist.

"Why does the GIL exist?" — CPython's memory management (reference counting) touches an object's refcount on nearly every operation; the GIL is a single coarse lock that makes that safe across threads without needing a separate, much slower fine-grained lock on every individual object.

"Does threading help in Python?" — depends entirely on whether the work is CPU-bound or I/O-bound. No speedup for CPU-bound work (§1 — the GIL means only one thread computes at a time). Real speedup for I/O-bound work (§3 — blocking calls release the GIL while waiting, so other threads can run).

"Does the GIL prevent race conditions?" — no, and this is the trap: it only guarantees one *bytecode instruction* runs at a time, not one *line* or one *multi-step operation*. `counter += 1` is several bytecode instructions, and the GIL can switch threads between any of them (§4) — you still need real locks for shared mutable state.

"How do you actually get parallelism in Python, if threads can't?" — `multiprocessing`: separate OS processes, each with its own interpreter and its own GIL, genuinely running on separate cores at the same time — at the cost of process-startup overhead and needing to explicitly share data between processes (pickling, queues, shared memory) instead of just sharing variables.

"Is the GIL ever going away?" — actively in progress, not hypothetical: PEP 703's free-threaded build has been an official (opt-in) CPython build option since 3.13, continuing into 3.14, disabling the GIL at the cost of a small single-thread performance penalty and an ecosystem still catching up on C-extension compatibility (§6).

---

## Practice questions

1. **Reproduce the CPU-bound non-speedup, and the multiprocessing fix, yourself.** Write a genuinely CPU-bound function (a counting loop is fine, like §1's). Time one call. Time two calls run sequentially. Time two calls run on two `threading.Thread`s. Time two calls run on two `multiprocessing.Process`es. Confirm the threaded time is close to the sequential time, and the multiprocessing time is close to half of it.

2. **Reproduce the I/O-bound speedup.** Using `time.sleep()` as your stand-in blocking call (same as §3), time four "1-second" calls run sequentially, then time the same four run on four threads. Confirm threading gets you close to a 4x speedup here, unlike Q1.

3. **Reproduce the lost-update race, then fix it with a lock.** Build the exact shared-counter race from §4 (two threads, no lock, `temp = counter` / `time.sleep(0)` / `counter = temp + 1`, repeated a couple thousand times each). Confirm the final count comes up short of the expected total. Then add a `threading.Lock()` around the read-modify-write and confirm the count comes out exactly right every time.

4. **Explain it back, as a comment.** In your own words, as a comment on your Q3 code, explain *why* the GIL — a lock whose whole job is to stop two threads from running Python code at the same instant — still allowed your counter to end up wrong. Tie it back to the "several bytecode instructions per line" point in §4.

5. **Check your own installed Python.** Run the two-line check from §6 (`sys.version`, `sysconfig.get_config_var("Py_GIL_DISABLED")`, `hasattr(sys, "_is_gil_enabled")`) on whatever Python you have installed locally. Note in a comment whether it's a standard or free-threaded build, and — if you can install a free-threaded build (`3.13t`/`3.14t`) to compare — what you'd expect to change about your Q1 timings if you reran them there.

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for type hints and `mypy` — the next item in the Advanced group.*
