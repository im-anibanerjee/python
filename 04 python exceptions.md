# Topic 3b — Exceptions: try/except/else/finally & Custom Exceptions

*Phase 1, Beginner group — item 4 of 4 (the one that got skipped — filling the gap now before Intermediate continues). Same drill: type the examples, do the practice questions.*

---

## 1. Why exceptions exist

Without exceptions, every function that could fail would need to signal failure through its return value — a special code, `None`, a sentinel — and every caller would need to remember to check for it, every time, or bugs slip through silently. Exceptions separate "the normal path" from "something went wrong" into two distinct channels: your main code reads top to bottom assuming things work, and error handling lives in one clearly marked place instead of being tangled through every `if` check.

```python
# without exceptions — every caller must remember to check
def divide(a, b):
    if b == 0:
        return None
    return a / b

result = divide(10, 0)
if result is None:            # easy to forget this check
    print("can't divide by zero")

# with exceptions — the failure can't be silently ignored
def divide(a, b):
    return a / b              # raises ZeroDivisionError automatically if b == 0

try:
    result = divide(10, 0)
except ZeroDivisionError:
    print("can't divide by zero")
```

### Running both versions for real

**Real, verified output**, running both versions back to back:

```
can't divide by zero
can't divide by zero
```

Both versions print the same thing here — which is exactly the point being made: *when the caller remembers to check*, both approaches look equivalent from the outside. The difference only shows up when a caller **forgets**:

**Flow diagram — the actual failure mode the exceptions version prevents:**

```
Without exceptions:
    result = divide(10, 0)     →  result is None
    print(result * 2)          →  TypeError: unsupported operand type(s)
                                   for *: 'NoneType' and 'int'
    (crashes LATER, far from the actual root cause — the division —
     with an error message that doesn't even mention division. If
     the caller had forgotten the `if result is None:` check, this
     is the confusing crash they'd actually hit, possibly several
     function calls away from where the real problem happened.)

With exceptions:
    result = divide(10, 0)     →  raises ZeroDivisionError IMMEDIATELY,
                                   right at the actual division — Python
                                   refuses to let execution continue
                                   with a nonsensical result at all.
    (crashes IMMEDIATELY, at the exact line responsible, with an
     error name that directly describes what went wrong. If nothing
     catches it, the traceback points straight at "division by zero,"
     not at some unrelated line three functions later.)
```

That's the core value proposition, stated plainly: a forgotten `if result is None:` check produces a confusing, delayed failure; a forgotten `except ZeroDivisionError:` produces an immediate, self-explanatory one (the program crashes with a traceback naming the exact problem, rather than continuing to run on bad data). Exceptions make it structurally harder for an error to be silently ignored.

## 2. Basic try/except

```python
try:
    risky_thing()
except SomeSpecificError:
    handle_it()
```

Python runs the `try` block. If a matching exception is raised anywhere inside it, execution jumps immediately to the matching `except` — the rest of the `try` block is skipped entirely, even code that looked like it had nothing to do with the error.

**Always catch specific exception types, never a bare `except:`.**

```python
try:
    x = int(user_input)
except ValueError:          # specific — you know exactly what went wrong and why
    print("that's not a number")
```

```python
try:
    x = int(user_input)
except:                       # BAD — catches literally everything
    print("something went wrong")
```

A bare `except:` catches `KeyboardInterrupt` (Ctrl+C), `SystemExit`, and every possible bug in your own code — a typo that raises `NameError`, a logic error raising `TypeError` — all get silently swallowed and reported as the same vague "something went wrong." You lose the ability to tell a user-input mistake apart from a real bug in your program. This is one of the most common things interviewers flag in a code review question.

### Multiple exception types

```python
try:
    value = int(data["amount"])
except KeyError:
    print("missing 'amount' field")
except ValueError:
    print("'amount' isn't a valid number")

# or, if you want to handle both the same way:
except (KeyError, ValueError) as e:
    print(f"bad data: {e}")
```

`as e` captures the exception object itself, so you can inspect its message — `str(e)` gives you the human-readable description Python attached to it.

### Running the specific-vs-bare examples for real

**Real, verified output**, both `except ValueError` and bare `except:` run against the exact same failing input (`int("abc")`):

```
that's not a number
something went wrong
```

They print near-identical messages here — which is exactly what makes bare `except:` deceptively tempting to write. The difference is invisible in this toy example and only becomes dangerous in real code, traced below:

**Flow diagram — the hidden danger of bare `except:`, using a realistic near-miss:**

```
try:
    x = int(user_input)
except:
    print("something went wrong")

Now imagine a typo three lines later in the SAME try block, e.g.:
    printt("done")     # <- typo: NameError: name 'printt' is not defined

Because the bare except: catches EVERYTHING, that NameError — a real
bug in the code that has NOTHING to do with parsing user input — gets
silently swallowed too, and the program just prints "something went
wrong" as if the USER had made a mistake. The actual bug (the typo)
never surfaces at all; you'd have no idea your own code was broken.

except ValueError: only catches ValueError specifically — that same
NameError would propagate up uncaught, crash loudly, and point you
straight at the typo.
```

This is the concrete version of "you lose the ability to tell a user-input mistake apart from a real bug in your program" — it's not an abstract style complaint, it's a genuine debugging trap: bare `except:` doesn't just catch too much conceptually, it actively hides your own future mistakes from you.

### Running the multiple-exception-types example for real

**Real, verified output**, testing both the separate-`except` form and the tuple form, each against a missing key and an invalid value:

```python
def lookup(data):
    try:
        value = int(data["amount"])
    except KeyError:
        print("missing 'amount' field")
    except ValueError:
        print("'amount' isn't a valid number")

lookup({})
lookup({"amount": "not a number"})

def lookup2(data):
    try:
        value = int(data["amount"])
    except (KeyError, ValueError) as e:
        print(f"bad data: {e}")

lookup2({})
lookup2({"amount": "abc"})
```

```
missing 'amount' field
'amount' isn't a valid number
bad data: 'amount'
bad data: invalid literal for int() with base 10: 'abc'
```

**How Python picks which `except` block runs, mechanically:** when an exception is raised inside a `try`, Python checks the `except` clauses **in the order they're written, top to bottom**, and runs the *first* one whose type matches (using the same `isinstance`-style "is this exception this type, or a subclass of it" check from the fundamentals doc). It never runs more than one — the moment a match is found, that block executes and the rest are skipped entirely, even if a later clause would also have matched. That's why `lookup({})` — where `data["amount"]` itself raises `KeyError` because the key is missing — is caught by the *first* `except KeyError:`, never reaching the `int(...)` call at all; while `lookup({"amount": "not a number"})` successfully finds the key (no `KeyError`), but then `int("not a number")` raises `ValueError`, which is caught by the second clause instead.

**Why `str(e)` (via the f-string) looks so different for the two error types:** `bad data: 'amount'` for the `KeyError` case looks almost cryptic at first glance — that's because `KeyError`'s string representation is just the missing key itself, wrapped in quotes (`repr()`-style), not a full sentence. `ValueError`'s message, by contrast, is a full descriptive sentence Python's own `int()` constructs internally. Both are legitimate, well-formed exception messages — they just come from different exception types with different conventions for what "the message" should contain, which is exactly why interview-quality error handling often logs `type(e).__name__` alongside `str(e)`, so the *kind* of error is never ambiguous even when the message text is terse.

## 3. `else` and `finally` — the two blocks people forget exist

```python
try:
    value = risky_computation()
except ValueError:
    print("computation failed")
else:
    print(f"succeeded: {value}")     # runs ONLY if the try block raised NOTHING
finally:
    print("cleanup, always runs")     # runs NO MATTER WHAT — success, failure, even a return/break inside try
```

**Why use `else` instead of just putting that code after the `try/except` block entirely?** Because code placed inside `try` is "protected" by the `except` — if *that* code itself raises the same kind of error, it gets caught too, which can hide a bug in code that had nothing to do with the original risky operation. `else` only runs after `try` has already succeeded cleanly, so anything you put there is *not* protected by the `except` above it — a genuine, if subtle, correctness difference:

```python
try:
    value = risky_computation()      # this can raise ValueError
    print(1 / value)                  # this can ALSO raise, e.g. ZeroDivisionError — but we only meant to catch the FIRST kind of error
except ValueError:
    print("computation failed")
```

Here, if `risky_computation()` succeeds but returns `0`, the `print(1 / value)` line raises `ZeroDivisionError` — which this `except ValueError` won't catch, so it propagates up uncaught, which is arguably correct (that's a different bug), but the point is: code inside `try` beyond the "risky" line is still exposed to whatever's listed in `except`. Moving `print(1/value)` into `else` keeps intent clear: "only run this if the risky part truly succeeded, and don't let it be mistaken for that same kind of failure."

`finally` runs **unconditionally** — success, exception caught, exception not caught, even if there's a `return` inside the `try`. It's the right place for cleanup that must happen no matter what (closing a network connection, releasing a lock). In practice, for *files* specifically you'll almost always use `with` instead (Topic 3) since it does this automatically — but `finally` is the general-purpose version for any kind of cleanup, not just files.

### Running the full try/except/else/finally block for real, both branches

**Real, verified output**, running a version of `risky_computation` that succeeds for `5` and raises for `-1`, through the *entire* four-block structure:

```python
def risky_computation(x):
    if x < 0:
        raise ValueError("negative input")
    return x * 2

for val in [5, -1]:
    try:
        value = risky_computation(val)
    except ValueError:
        print("computation failed")
    else:
        print(f"succeeded: {value}")
    finally:
        print("cleanup, always runs")
```

```
succeeded: 10
cleanup, always runs
computation failed
cleanup, always runs
```

**Flow diagram — tracing exactly which blocks ran, for each of the two values:**

```
val = 5  (succeeds)

    try:      risky_computation(5) -> returns 10, no exception raised
    except:   SKIPPED — nothing was raised, so there's nothing to catch
    else:     RUNS — try block completed with no exception
                  -> prints "succeeded: 10"
    finally:  RUNS — always, regardless of what happened above
                  -> prints "cleanup, always runs"

val = -1  (fails)

    try:      risky_computation(-1) -> raises ValueError("negative input")
                  execution jumps OUT of the try block immediately, at
                  the exact point of the raise — any code after that
                  point inside try is SKIPPED (there wasn't any here,
                  but this matters more in longer try blocks)
    except:   RUNS — ValueError matches -> prints "computation failed"
    else:     SKIPPED — the try block did NOT complete cleanly, so
                  else never runs, no matter what except did
    finally:  RUNS — always
                  -> prints "cleanup, always runs"
```

The one-sentence summary worth memorizing cold: **`else` runs exactly when `except` doesn't, and `finally` runs no matter what either of them did.**

### Verifying the "why `else` matters" example for real

**Real, verified output**, deliberately reproducing the scenario the doc describes — `risky_computation` returns `0`, and the follow-up division raises a *different* exception type than the one being caught:

```python
def risky_computation(x):
    if x < 0:
        raise ValueError("negative input")
    return x

try:
    value = risky_computation(0)
    print(1 / value)
except ValueError:
    print("computation failed")
```

```
Traceback (most recent call last):
  ...
ZeroDivisionError: division by zero
```

This confirms the doc's claim exactly: the program **crashes**, uncaught, with `ZeroDivisionError` — it does *not* print `"computation failed"`, even though that `except` block is right there, because `except ValueError` only matches `ValueError`, and `ZeroDivisionError` is a completely different exception type (both happen to be direct subclasses of `Exception`, but neither is a subclass of the other — see §5's hierarchy). The fact that `print(1 / value)` was physically sitting inside the same `try` block as the genuinely risky line is what let this happen; moving it into an `else` block wouldn't suppress the `ZeroDivisionError` either (it would still propagate, which is correct — it's a real, separate bug), but it *would* make the code's intent unambiguous: "this division was never meant to be protected by the `except ValueError` above it," removing any doubt about which failures that `except` is actually meant to guard against.

## 4. Raising your own exceptions

```python
def withdraw(balance, amount):
    if amount > balance:
        raise ValueError(f"insufficient funds: balance is {balance}, tried to withdraw {amount}")
    return balance - amount
```

`raise` immediately stops normal execution and starts the exception propagating up the call stack, looking for a matching `except` somewhere in a caller. If nothing catches it, the program crashes and prints a traceback.

You can also re-raise inside an `except` — useful when you want to log something but still let the error propagate:

```python
try:
    risky_thing()
except ValueError as e:
    log_error(e)
    raise              # re-raises the SAME exception, preserving the original traceback
```

### Running both `raise` and re-`raise` for real

**Real, verified output:**

```python
def withdraw(balance, amount):
    if amount > balance:
        raise ValueError(f"insufficient funds: balance is {balance}, tried to withdraw {amount}")
    return balance - amount

try:
    withdraw(100, 500)
except ValueError as e:
    print("caught:", e)

def log_error(e):
    print("logged:", e)

def risky_thing():
    raise ValueError("boom")

try:
    try:
        risky_thing()
    except ValueError as e:
        log_error(e)
        raise
except ValueError as e:
    print("re-caught at outer level:", e)
```

```
caught: insufficient funds: balance is 100, tried to withdraw 500
logged: boom
re-caught at outer level: boom
```

**Flow diagram — where control goes on `raise`, and why bare `raise` inside an `except` re-throws the *same* exception object rather than creating a new one:**

```
withdraw(100, 500)
    amount (500) > balance (100)?  yes
    -> raise ValueError("insufficient funds...")
    -> execution INSIDE withdraw() stops immediately, right there —
       the `return balance - amount` line never runs at all
    -> the exception propagates UP to whoever called withdraw()
    -> caught by the surrounding try/except ValueError, prints "caught: ..."

Nested try/except with bare `raise`:

    outer try:
        inner try:
            risky_thing()  -> raises ValueError("boom")
            (this is the SAME exception object throughout — it is
             never recreated or copied)
        inner except ValueError as e:
            log_error(e)          -> prints "logged: boom"
            raise                 -> re-raises THIS SAME exception
                                      object, with its ORIGINAL
                                      traceback still attached, as if
                                      the inner except had never
                                      caught it at all — just re-launches
                                      it upward
    outer except ValueError as e:
        -> catches the SAME re-raised object
        -> prints "re-caught at outer level: boom"
```

The reason bare `raise` (no arguments) is specifically useful here, rather than writing `raise e` or `raise ValueError(str(e))`: `raise` alone preserves the exception's **original traceback** — the full record of exactly where, in the call stack, it first occurred — which is invaluable for debugging. `raise e` re-raises the same object too but can reset part of that traceback context in some cases; writing a brand new `raise ValueError(...)` would lose the original traceback entirely and look like a completely different error occurred at the `raise` line instead of at its true origin. The pattern "log it, then bare `raise`" is exactly how you get visibility into an error (via the log) without changing how or where it ultimately gets handled.

## 5. The exception hierarchy (and why bare `except:` is dangerous)

Every exception in Python inherits from `BaseException`. Almost everything you'll ever catch inherits from `Exception` specifically — but `KeyboardInterrupt` and `SystemExit` inherit directly from `BaseException`, *bypassing* `Exception`. That's a deliberate design choice: it means `except Exception:` (a slightly less bad, but still usually wrong, alternative to bare `except:`) won't accidentally swallow a user's Ctrl+C or a deliberate `sys.exit()`. Bare `except:` catches everything in `BaseException`, including those — which is exactly why it's discouraged.

Common built-ins you'll catch constantly, all inheriting from `Exception`:

| Exception | When it's raised |
|---|---|
| `ValueError` | right type, wrong value — `int("abc")` |
| `TypeError` | wrong type entirely — `"a" + 5` |
| `KeyError` | dict key doesn't exist |
| `IndexError` | list index out of range |
| `FileNotFoundError` | file doesn't exist (subclass of `OSError`) |
| `ZeroDivisionError` | division by zero |
| `AttributeError` | `.method()` or `.attribute` doesn't exist on that object |

### Verifying the hierarchy claims for real, with `issubclass()`

**Real, verified output** — checking the actual inheritance relationships directly, rather than taking the doc's word for it, plus proving the "`except Exception:` doesn't catch `KeyboardInterrupt`" claim with a real `try`/`except`:

```python
print(issubclass(ValueError, Exception))
print(issubclass(KeyboardInterrupt, Exception))
print(issubclass(KeyboardInterrupt, BaseException))
print(issubclass(SystemExit, Exception))
print(issubclass(SystemExit, BaseException))

try:
    raise KeyboardInterrupt
except Exception:
    print("caught by except Exception")
except BaseException:
    print("caught by except BaseException")
```

```
True
False
True
False
True
caught by except BaseException
```

**Flow diagram — the actual shape of the hierarchy, drawn out:**

```
                    BaseException
                    ┌──────┬───────────┬──────────────┐
                    │      │           │              │
           KeyboardInterrupt  SystemExit    GeneratorExit   Exception
                                                              │
                                    ┌─────────────┬───────────┼─────────────┬───────────┐
                                    │             │           │             │           │
                               ValueError    TypeError    KeyError     IndexError   ZeroDivisionError
                                                                                          ...

`except Exception:` walks UP from the raised exception's actual type,
looking for Exception anywhere in that chain. KeyboardInterrupt's
chain is: KeyboardInterrupt -> BaseException (it skips Exception
entirely) — so `except Exception:` genuinely cannot match it, no
matter how it's written. Only `except BaseException:` (or bare
`except:`, which is secretly `except BaseException:`) reaches high
enough up the tree to catch it.
```

In the code above, `except Exception:` is listed *first*, purely to make the point vivid: Python still skips right past it and falls through to `except BaseException:`, because `KeyboardInterrupt` genuinely does not match `Exception` — proving this isn't just a documentation claim, it's how the actual class hierarchy is wired. This is precisely why interrupting a program stuck in a bad `except Exception:`-only loop with Ctrl+C still works the way you'd expect — the language was deliberately designed so that the "catch nearly everything" convenience classes (`Exception`, and by extension well-behaved code that catches it) can never accidentally block you from stopping your own program.

## 6. Custom exceptions

Once your program has real domain logic, generic `ValueError` stops being descriptive enough — especially in a larger codebase where a caller wants to catch *your specific* error condition without accidentally also catching every other `ValueError` in the system. Define your own by subclassing `Exception`:

```python
class InsufficientFundsError(Exception):
    """Raised when a withdrawal would take the balance negative."""
    pass

class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def withdraw(self, amount):
        if amount > self.balance:
            raise InsufficientFundsError(
                f"{self.owner} has {self.balance}, cannot withdraw {amount}"
            )
        self.balance -= amount

acc = BankAccount("Ani", 100)
try:
    acc.withdraw(500)
except InsufficientFundsError as e:
    print(f"blocked: {e}")
```

Now a caller can catch `InsufficientFundsError` specifically, without also catching an unrelated `ValueError` from somewhere else in the same `try` block. This is a small pattern but a genuinely important one for any real backend codebase — including the FastAPI service you'll build in Phase 3, where different custom exceptions typically map to different HTTP status codes.

### Running this for real, and confirming exactly what subclassing `Exception` buys you

**Real, verified output:**

```python
acc = BankAccount("Ani", 100)
try:
    acc.withdraw(500)
except InsufficientFundsError as e:
    print(f"blocked: {e}")

print(isinstance(InsufficientFundsError("x"), Exception))
print(issubclass(InsufficientFundsError, ValueError))
```

```
blocked: Ani has 100, cannot withdraw 500
True
False
```

**What `class InsufficientFundsError(Exception): pass` actually gives you, mechanically — this is a genuinely minimal class (you won't formally build up class/inheritance mechanics until the OOP doc, but this is worth previewing narrowly, since it's such a common, small pattern):** writing `(Exception)` after the class name means `InsufficientFundsError` **inherits** everything `Exception` already knows how to do — accepting a message in its constructor, storing it, being convertible to a string with `str(e)`, being catchable by `except Exception:` — all of that comes for free, with zero code written by you (the `pass` body means "no additional behavior beyond what's inherited"). `isinstance(InsufficientFundsError("x"), Exception)` printing `True` confirms exactly that inherited relationship. `issubclass(InsufficientFundsError, ValueError)` printing `False` confirms the flip side: it does *not* automatically relate to `ValueError` just because it represents "a bad value" conceptually — it only inherits from whatever you explicitly wrote in the parentheses. If a caller wanted `except ValueError:` to *also* catch this custom exception, they'd need to write `class InsufficientFundsError(ValueError):` instead — the choice of what to inherit from is a real design decision, not a formality.

**Flow diagram — why catching `InsufficientFundsError` specifically is strictly better than catching `ValueError` in a larger program:**

```
A larger function might have SEVERAL risky operations in one try:

try:
    acc.withdraw(amount)          # could raise InsufficientFundsError
    quantity = int(user_input)    # could ALSO raise ValueError (unrelated!)
except ValueError:
    print("something about a value went wrong")   # ⚠ AMBIGUOUS — which one failed?

vs.

try:
    acc.withdraw(amount)
    quantity = int(user_input)
except InsufficientFundsError:
    print("not enough money")                     # unambiguous
except ValueError:
    print("that quantity isn't a valid number")    # unambiguous
```

This is the direct payoff of defining a custom, specific exception type instead of just reusing `ValueError` everywhere: each `except` clause can now say precisely which failure it's responding to, rather than lumping unrelated problems into one vague bucket — exactly the same principle as catching specific built-in exceptions instead of a bare `except:`, just applied one level up, to your own domain logic.

## 7. EAFP vs LBYL — a Python-specific philosophy worth knowing by name

Two styles for handling "this might not work":

- **LBYL** — "Look Before You Leap" — check conditions first, then act:
  ```python
  if "amount" in data and isinstance(data["amount"], (int, float)):
      value = data["amount"]
  ```
- **EAFP** — "Easier to Ask Forgiveness than Permission" — just try it, catch the failure:
  ```python
  try:
      value = data["amount"]
  except KeyError:
      value = None
  ```

**Python culture strongly favors EAFP.** It's not just style — checking first (`"amount" in data`) and then using it is technically two separate operations, and in concurrent/multi-threaded code, the data could theoretically change between the check and the use (a "race condition"). EAFP does the check and the use as one atomic attempt. It's also often simply more readable once you're used to it. Knowing this term and being able to say "Python favors EAFP" is a small but real signal in an interview that you've absorbed the language's idioms, not just its syntax.

### Running both styles for real, success and failure cases

**Real, verified output:**

```python
data = {"amount": 42}

if "amount" in data and isinstance(data["amount"], (int, float)):
    value = data["amount"]
print("LBYL:", value)

try:
    value = data["amount"]
except KeyError:
    value = None
print("EAFP:", value)

data2 = {}
try:
    value2 = data2["amount"]
except KeyError:
    value2 = None
print("EAFP missing:", value2)
```

```
LBYL: 42
EAFP: 42
EAFP missing: None
```

**Flow diagram — the race condition LBYL is exposed to, made concrete (this is the part that's easy to nod along to without really feeling it):**

```
LBYL, in a hypothetical multi-threaded program:

    Thread A: checks  "amount" in data        -> True
    Thread B: (running concurrently) deletes data["amount"]
    Thread A: now reads  data["amount"]        -> KeyError anyway!
              (the check already passed, but the world changed
               between the check and the use — two separate steps,
               two separate opportunities for something else to
               interfere in between)

EAFP, same scenario:

    Thread A: tries  value = data["amount"]  directly, as ONE step
              -> either it succeeds (got the value before deletion)
                 or it raises KeyError (deletion happened first) —
                 there is no gap in between for anything else to
                 sneak into, because there's only one operation total,
                 not two
```

You don't need multithreading experience to take the point: LBYL is structurally two operations (`check`, then `use`) with a gap between them; EAFP collapses that into one operation (`try to use it, handle failure if it happens`) with no gap at all. Even outside of concurrency, this is *also* just less code and, once you're fluent in reading `try`/`except`, more direct about what's actually being attempted — which is the other half of why the language leans this way.

---

## Practice questions

1. **`safe_divide(a, b)`** — write a function that returns `a / b`, but catches `ZeroDivisionError` and returns `None` instead of crashing. Then write a second version that also catches `TypeError` (for when `a` or `b` isn't a number at all) and returns `None` for that case too.

2. **Custom exception, applied to your own code.** Go back to your `BankAccount` class from the OOP doc. Define an `InsufficientFundsError(Exception)` and change `withdraw()` to raise that instead of a generic `ValueError`. Write a small script that tries to overdraw the account and catches your new exception specifically, printing a friendly message.

3. **Trace the execution.** Predict what prints, in order, for each of these two calls — then verify by running it:
   ```python
   def process(n):
       try:
           result = 10 / n
       except ZeroDivisionError:
           print("A: caught zero division")
       else:
           print(f"B: got {result}")
       finally:
           print("C: cleanup")

   process(2)
   print("---")
   process(0)
   ```

4. **Explain in your own words**: why is `except: pass` (catching everything and doing nothing with it) considered a serious anti-pattern, even though it technically prevents your program from crashing? What's the actual cost of writing code that way, and what should you do instead?

---

*As always — write real code, paste it when ready, I'll check it. Once this is done, Phase 1's Beginner group is genuinely complete. Say "next" and we'll go back to checking your OOP practice answers from Topic 4.*
