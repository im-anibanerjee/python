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
