# Topic 13 — Type Hints & `mypy`, Deep Dive

*Phase 1, Advanced group — item 3 of 5 (asyncio, GIL, type hints/mypy, pytest, logging/profiling). Where the last two docs were about runtime behavior (how `asyncio` and threads actually execute), this one is almost the opposite: it's about a promise written into your code that the interpreter itself completely ignores — and a separate tool that reads that promise and checks it for you, without ever running your program. Every snippet below was actually run through both Python and `mypy` for real, with the real output pasted underneath.*

---

## 0. The picture to hold in your head before any code

Imagine every drawer and jar in a kitchen has a label on it: "flour," "sugar," "knives." The labels don't physically stop you from putting sugar in the flour jar — nothing about the jar itself enforces it. But a kitchen inspector can walk through, read every label, look at what's actually supposed to go where based on your recipe cards, and flag "your recipe says add flour here, but the jar you're reaching for is labeled sugar" — **without cooking a single dish**. They're reading the labels and the recipe on paper, catching the mismatch before anyone's hands ever touch an ingredient.

That's the entire relationship in this doc. **A type hint (`name: str`) is the label on the jar — pure documentation, physically enforcing nothing.** `mypy` is the inspector — a separate tool that reads your labels and your code and tells you about mismatches, entirely on paper, before you ever run anything. And, as §7 covers, some libraries (Pydantic, FastAPI) are like a smart auto-sorting shelf that actually reads the labels *while you're cooking* and rejects or converts the wrong ingredient on the spot — real runtime enforcement, which is the exception, not the rule.

---

## 1. The single most important fact: Python itself does not enforce type hints

```python
def add(a: int, b: int) -> int:
    return a + b

print(add("2", "3"))
```

Real output:
```
23
```

**No error. No warning. Nothing.** `add("2", "3")` calls the function with two strings, completely violating the `int, int -> int` hint — and Python runs it anyway, doing exactly what `+` does for two strings: concatenation. `"2" + "3"` is `"23"`, and that's what gets printed. The type hint `a: int` did not check, coerce, or reject anything; the interpreter treated it as if it wasn't even there.

This is the fact everything else in this doc builds on: **type hints in plain Python are metadata, not validation.** They exist to be *read* — by you, by your editor, by a separate tool like `mypy` — not to be *enforced* by the language itself. Proof that they're just stored, inert data:

```python
def add(a: int, b: int) -> int:
    return a + b

print(add.__annotations__)
```

Real output:
```
{'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}
```

That's it — a plain dictionary, sitting on the function object, exactly like any other attribute. Nothing in the language ever reads this dictionary to reject a bad call; it's just there for something else (your editor, `mypy`, a library like Pydantic in §7) to go look at if it chooses to.

```
THE THREE MOMENTS A TYPE HINT PASSES THROUGH
================================================
1. WRITE TIME  -- you write `a: int`. Python parses it, stores it in
                  `add.__annotations__`. Nothing is checked. Nothing runs.

2. CHECK TIME  -- (optional, separate step) you run `mypy your_file.py`.
                  mypy reads the hints and the code TEXT, reasons about
                  what types flow where, and reports mismatches. Your
                  program never actually executes during this step.

3. RUN TIME    -- you run `python your_file.py`. The interpreter runs
                  your code completely ignoring the hints -- `add("2","3")`
                  above proves this. UNLESS some library (not bare Python)
                  explicitly reads `__annotations__` itself and decides to
                  validate or coerce based on it (§7).
```

---

## 2. Basic syntax — the vocabulary you'll actually use

```python
# variables
age: int = 27
name: str = "Ani"
scores: list[int] = [90, 85, 100]
lookup: dict[str, int] = {"a": 1, "b": 2}

# function signatures
def greet(name: str, times: int = 1) -> str:
    return (name + " ") * times
```

`list[int]` and `dict[str, int]` — square brackets after the container type, naming what's *inside* it — are the modern syntax (Python 3.9+; this environment is 3.11, well within range). Before 3.9, you had to write `from typing import List, Dict` and use `List[int]`, `Dict[str, int]` instead — you'll still see that older form constantly in existing codebases and tutorials, so recognize both, but prefer the plain built-in form (`list[int]`) in anything you write today.

Two more pieces of vocabulary you'll see everywhere: **`Optional[X]`** means "an `X`, or `None`" — shorthand for `Union[X, None]`. **`Union[X, Y]`** means "an `X` or a `Y`." Since Python 3.10, there's also a plain operator form for unions — `X | Y` — which reads more like ordinary Python and is now the preferred style:

```python
def show(value: int | str) -> None:
    print(f"got: {value}")

show(5)
show("hello")
show(3.14)   # a float -- neither int nor str
```

Running this with plain Python does nothing surprising (§1 already proved the interpreter won't stop you) — but running it through `mypy`, which is the entire subject of the next section, does:

Real `mypy` output:
```
t4.py:6: error: Argument 1 to "show" has incompatible type "float"; expected "int | str"  [arg-type]
Found 1 error in 1 file (checked 1 source file)
```

---

## 3. `mypy` — reading your code without running it

**`mypy` is a static type checker: it reads your source code as text, reasons about what type flows through every variable and function call based on your hints, and reports mismatches — without ever executing a single line of your program.** That "without executing" part is worth sitting with: `mypy t4.py` above never actually called `show(3.14)`; it never ran the file at all. It statically traced through the code and concluded, on paper, that the third call's argument type doesn't match the hint — the exact same conclusion you'd eventually get by running it and (if the function actually misused the wrong-typed value) hitting a real crash, except `mypy` gets there in a fraction of a second, without side effects, and catches it even for code paths you haven't happened to run yet.

Go back to §1's `add("2", "3")` — Python ran it happily and printed `"23"`. Here's what `mypy` says about the exact same file:

```python
def add(a: int, b: int) -> int:
    return a + b

print(add("2", "3"))
```

Real `mypy` output:
```
t0.py:4: error: Argument 1 to "add" has incompatible type "str"; expected "int"  [arg-type]
t0.py:4: error: Argument 2 to "add" has incompatible type "str"; expected "int"  [arg-type]
Found 2 errors in 1 file (checked 1 source file)
```

Two genuinely different tools, looking at the exact same file, reaching genuinely different conclusions — because they're doing genuinely different things. `python t0.py` *executes* the file and reports what actually happened (nothing went wrong at runtime, because `+` works fine on two strings). `mypy t0.py` *reads* the file and reports what the hints promise versus what the code actually does (a clear mismatch) — entirely independent of whether that mismatch happens to blow up when you run it.

```
FLOW -- running the same file two different ways
====================================================
python t0.py:
  interpreter starts -> executes add("2","3") for real -> "2"+"3" -> "23"
  -> prints 23. Hints were never consulted. No error.

mypy t0.py:
  mypy starts -> parses the file into a syntax tree, WITHOUT running it
  -> sees add's signature says (int, int) -> int
  -> sees the call site passes ("2", "3") -- both str
  -> str != int -> reports a mismatch, one error per mismatched argument
  -> never once calls add(). The program never runs.
```

---

## 4. Where this actually catches real bugs — `Optional` and `None`

This is the single most common real-world category of bug `mypy` catches, so it's worth a full example. A function that might not find anything, returning `Optional[str]`:

```python
from typing import Optional

def find_user(user_id: int) -> Optional[str]:
    users = {1: "ani", 2: "priya"}
    return users.get(user_id)

name = find_user(3)
print(name.upper())
```

Real output, running it with plain Python:
```
Traceback (most recent call last):
  File "t2.py", line 8, in <module>
    print(name.upper())
          ^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'upper'
```

`user_id=3` isn't in the dictionary, `.get()` returns `None`, and `None.upper()` genuinely crashes — a completely real, common bug (the "I forgot this could come back empty" bug). Here's the important part: `mypy` catches this **without ever needing `user_id` to actually be `3`** — it doesn't run the code at all, it just reasons "this function's return type says `Optional[str]`, meaning it *can* be `None`, and this next line calls `.upper()` on it with no check in between":

Real `mypy` output:
```
t2.py:8: error: Item "None" of "str | None" has no attribute "upper"  [union-attr]
Found 1 error in 1 file (checked 1 source file)
```

The fix is called **narrowing** — explicitly checking for `None` first, which both `mypy` and a human reader can see rules out the `None` case for everything inside the `if`:

```python
name = find_user(3)
if name is not None:
    print(name.upper())
else:
    print("no user found")
```

Real output (Python): `no user found` — no crash. Real `mypy` output: `Success: no issues found in 1 source file`. Inside the `if name is not None:` block, `mypy` narrows `name`'s type from `str | None` down to just `str` for that block only — it's smart enough to know the check you just wrote rules out the `None` branch, so `.upper()` inside it is provably safe.

---

## 5. Generics — one function, many types, with the relationship preserved

```python
from typing import TypeVar, Sequence

T = TypeVar("T")

def first(items: Sequence[T]) -> T:
    return items[0]

n: int = first([1, 2, 3])
s: str = first(["a", "b"])
bad: str = first([1, 2, 3])   # first([1,2,3]) is inferred as int, not str
```

Real `mypy` output:
```
t5.py:10: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
Found 1 error in 1 file (checked 1 source file)
```

`TypeVar("T")` declares a placeholder type, not a fixed one — `first`'s signature `Sequence[T] -> T` says "whatever type of thing is *inside* the sequence you hand me, that's exactly the type I hand back," without committing to any specific type up front. Each *call site* fills in `T` for itself: `first([1, 2, 3])` fills `T` with `int` (so the return type is `int` for that call), `first(["a", "b"])` fills `T` with `str`. `mypy` tracks this per-call, which is exactly why line 10 is flagged — `first([1, 2, 3])` is inferred as returning `int` for that specific call, and assigning an `int` into a variable annotated `str` is the mismatch. Remove that one bad line and `mypy` reports success — the first two lines were correct all along.

This is the typed version of something you already know from the comprehensions/decorators docs: a genuinely reusable function shouldn't have to hardcode one specific type to be useful, and `TypeVar` is how you tell `mypy` "reusable, but still type-checked — the input and output types are linked, even though neither is fixed."

---

## 6. Gradual typing and `--strict` — how much checking do you actually get?

`mypy`'s design philosophy is called **gradual typing**: you can add hints to a codebase incrementally, file by file, function by function, and by default `mypy` treats anything *unannotated* as the special type `Any` — meaning "could be anything, don't check calls involving this too strictly" — rather than refusing to run at all. Proof:

```python
def add(a, b):
    return a + b

print(add(2, 3))
```

Real `mypy` output (default settings):
```
Success: no issues found in 1 source file
```

Completely unannotated, and `mypy` says nothing — by default, it's lenient about code that hasn't opted in to typing yet, exactly so you *can* add hints gradually without a giant wall of errors on day one. Turn on `--strict`, and the same file gets a very different answer:

Real `mypy --strict` output:
```
t6.py:1: error: Function is missing a type annotation  [no-untyped-def]
t6.py:4: error: Call to untyped function "add" in typed context  [no-untyped-call]
Found 2 errors in 1 file (checked 1 source file)
```

`--strict` (a bundle of stricter flags mypy ships together) now demands every function be annotated, and flags even *calling* an untyped function from typed code. Add the hints back and it's clean again:

```python
def add(a: int, b: int) -> int:
    return a + b

print(add(2, 3))
```

Real `mypy --strict` output: `Success: no issues found in 1 source file`. In a real project, this configuration usually lives in a `mypy.ini` or a `[tool.mypy]` table in `pyproject.toml`, rather than being typed out as a flag every time — but the underlying idea is the same either way: how strict you want the inspector to be is a dial you turn, not an all-or-nothing switch.

---

## 7. Where a type hint actually gets enforced at runtime — Pydantic and FastAPI

Section 1 was unambiguous: bare Python does not enforce hints at runtime. But you're heading toward FastAPI later in this roadmap, and it's worth knowing *now* that FastAPI's whole request-validation story is built on a library — **Pydantic** — that is the deliberate exception to §1's rule. Pydantic reads a model's type hints via reflection (the same `__annotations__` dictionary from §1) and actually **validates and coerces** incoming data against them, for real, at runtime:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

u = User(name="ani", age="27")   # "27" is a string, not an int
print(u)
print(type(u.age))

bad = User(name="ani", age="not a number")
```

Real output:
```
name='ani' age=27
<class 'int'>
Traceback (most recent call last):
  ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for User
age
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not a number', input_type=str]
```

Look closely at what happened: `age="27"` (a string) was silently **coerced into the actual integer `27`** — `type(u.age)` really is `<class 'int'>`, not `str` — because Pydantic looked at the `age: int` hint and decided a numeric string is close enough to convert. `age="not a number"` can't be coerced, so it raises a real `ValidationError` — a genuine runtime exception, not a `mypy`-only, paper-only complaint. This is exactly what happens every time a FastAPI endpoint receives a request body: the hints on your Pydantic model aren't documentation there, they're the actual validation logic, read and enforced live, on every request. It's the one place in this whole doc where "just a label on the jar" stops being true.

One more genuinely worth running: what does `mypy` itself make of this same file? Real `mypy` output:
```
t7.py:7: error: Argument "age" to "User" has incompatible type "str"; expected "int"  [arg-type]
t7.py:11: error: Argument "age" to "User" has incompatible type "str"; expected "int"  [arg-type]
Found 2 errors in 1 file (checked 1 source file)
```

`mypy` flags *both* calls — including `User(name="ani", age="27")`, the one that actually worked fine at runtime. This is worth being precise about: `mypy` only knows the *declared* field type (`int`); it has no built-in awareness that Pydantic will coerce a numeric string at runtime, so from a pure static-typing standpoint, passing a `str` where an `int` is declared is a mismatch, full stop. `mypy` and Pydantic are genuinely looking at this differently — one reasoning from the annotation alone, the other reasoning from what it can actually do with the value at runtime. This is exactly why real Pydantic projects install a separate `mypy` plugin (`pydantic.mypy`), which teaches `mypy` about Pydantic's specific coercion and validation behavior instead of flagging every gently-typed call site as an error.

---

## 8. Interview-distilled

"Does Python enforce type hints at runtime?" — no. They're stored as plain metadata (`__annotations__`) and the interpreter never checks them; `add("2", "3")` running to completion and printing `"23"` despite `def add(a: int, b: int) -> int` proves it (§1).

"What does `mypy` actually do?" — statically reads your source code and its type hints and reports mismatches, without ever executing the program. It can catch a bug on a code path you've never actually run (§3, §4).

"What's `Optional[X]`?" — shorthand for `Union[X, None]` — "an `X`, or `None`." The classic bug it catches: calling a method on something typed `Optional[str]` without first checking it isn't `None` (§4). The fix is narrowing — an explicit `is not None` check, which `mypy` is smart enough to track.

"What is gradual typing?" — the philosophy that you can add type hints incrementally; by default `mypy` treats unannotated code as `Any` and doesn't demand it be typed. `--strict` (or a config file) turns that leniency off, function by function, project by project (§6).

"Do type hints ever actually get enforced?" — not by bare Python, but yes by libraries that deliberately read `__annotations__` themselves and act on it — Pydantic (and therefore FastAPI) being the most important example: it validates and even coerces data against your hints at real runtime (§7).

---

## Practice questions

1. **Prove hints aren't enforced, yourself.** Write any small function with `int` parameter hints and an `int` return hint. Call it with the wrong types on purpose (strings, say) and confirm Python runs it anyway, with no error — print what it actually returns. Then run the same file through `mypy` and confirm it reports the mismatch that plain Python didn't care about.

2. **Reproduce the `Optional`/`None` bug, then fix it with narrowing.** Write a function that returns `Optional[str]` (e.g., a dictionary lookup that can miss). Call it with an input that returns `None`, then immediately call a string method on the result without checking — confirm both the real Python crash (`AttributeError`) and that `mypy` flags it (`union-attr`) even before you run it. Then add an `if x is not None:` check and confirm both the crash and the `mypy` error are gone.

3. **Write a generic function with `TypeVar`.** Write a function like `first()` or `last()` that works on a `Sequence[T]` and returns `T`. Call it with a `list[int]` and a `list[str]`, assigning each result to a correctly-typed variable — confirm `mypy` is clean. Then deliberately assign one result to a variable of the *wrong* type and confirm `mypy` catches exactly that line.

4. **Compare plain `mypy` to `mypy --strict`.** Write a completely unannotated function. Confirm plain `mypy` says nothing about it. Then run `mypy --strict` on the same file and note in a comment which specific errors show up that didn't before. Add full annotations and confirm `--strict` goes clean too.

5. **Contrast hint documentation vs. real enforcement.** Using Pydantic's `BaseModel` (or just describing it if you don't have Pydantic installed), define a small model with an `int` field, construct it once with a numeric string for that field and print the resulting value's actual type, then construct it again with a non-numeric string and confirm you get a real `ValidationError`. In a comment, explain why this is different from what §1 proved about plain Python functions.

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for `pytest` — how to actually turn all these practice-question checks into real, automated, repeatable tests instead of eyeballing printed output.*
