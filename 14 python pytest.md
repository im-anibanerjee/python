# Topic 14 — `pytest`, Deep Dive

*Phase 1, Advanced group — item 4 of 5 (asyncio, GIL, type hints/mypy, pytest, logging/profiling). Every practice question you've answered across this whole series so far has been graded by hand — pasting output, comparing it by eye. `pytest` is how that entire process gets automated: write down what "correct" means once, as a plain `assert`, and let a tool run it and tell you exactly what broke, forever, without you ever eyeballing terminal output again. Every snippet below was actually run through `pytest` for real.*

---

## 0. The picture to hold in your head before any code

Imagine you've written down a recipe, and you want to check a batch of dishes against it — is the soup salty enough, is the cake fully baked. One way: taste and inspect every dish yourself, every single time, and keep it all in your head. That's what you've been doing all series — running a script, reading the printed output, deciding by eye whether it matches what you expected.

`pytest` is hiring a taste-tester who has actually memorized your exact recipe. You write down the check once — "the soup should taste like 2 teaspoons of salt, not more, not less" — and hand it to them. From then on, they run through the whole batch of dishes, taste every one, and hand you back a precise report: which dishes passed, which failed, and for each failure, **exactly what was off** ("this soup tasted like 3 teaspoons, not 2") — not just "something's wrong with dish #4." You never have to personally taste anything again, and you can rerun the exact same check on tomorrow's batch for free.

That "exactly what was off" part is the whole reason `pytest` is the standard over just sprinkling `assert` statements through a script yourself, as §1 proves directly.

---

## 1. Why `pytest`, not just a plain `assert`?

Python already has a built-in `assert` statement — you've used it throughout this series. Here it is, completely on its own, no `pytest` involved:

```python
def add(a, b):
    return a + b

assert add(2, 3) == 6
```

Real output, running it as a plain script:
```
Traceback (most recent call last):
  File "plain_assert.py", line 4, in <module>
    assert add(2, 3) == 6
           ^^^^^^^^^^^^^^
AssertionError
```

**`AssertionError`. That's it. No detail about *why*.** It doesn't tell you what `add(2, 3)` actually returned, or what it was compared against — you'd have to go add a `print()` yourself to find out. Now, the exact same `assert`, inside a function `pytest` recognizes as a test, run through `pytest` instead of plain `python`:

```python
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 6
```

Real `pytest` output:
```
test_plain_assert.py::test_add FAILED                                    [100%]

=================================== FAILURES ===================================
___________________________________ test_add ___________________________________

    def test_add():
>       assert add(2, 3) == 6
E       assert 5 == 6
E        +  where 5 = add(2, 3)

test_plain_assert.py:5: AssertionError
=========================== short test summary info ============================
FAILED test_plain_assert.py::test_add - assert 5 == 6
```

Same exact `assert` statement, same exact bug — but now you get `assert 5 == 6` and `where 5 = add(2, 3)`, spelled out automatically. **`pytest` doesn't run your file normally at all — it intercepts every `assert` inside a test and rewrites it, at import time, to capture the actual value of every sub-expression before deciding pass or fail**, so a failure report shows you the real numbers without you ever having to write a custom message yourself. This single feature — called **assert rewriting** — is the main reason plain `assert` inside `pytest` is preferred over the older `unittest` style (`self.assertEqual(add(2, 3), 6)`), which requires memorizing a different method name for every kind of comparison (`assertEqual`, `assertTrue`, `assertRaises`, ...) to get a decent failure message at all. With `pytest`, `assert` is the *only* keyword you ever need — it's smart enough to produce a good message no matter what you write after it.

---

## 2. Test discovery — how `pytest` finds your tests at all

You never told `pytest` which functions were tests by name in a config file — it found them by **convention**. Two rules, both provable:

```python
# not_a_test_helper.py -- filename does NOT start with test_
def test_looking_but_not_discovered():
    assert False
```

Running `pytest` in that directory (alongside a real, correctly-named test file) — real output:
```
collecting ... collected 1 item

test_uses_conftest.py::test_shared PASSED                                [100%]

============================== 1 passed in 0.00s ===============================
```

Only **1 item** collected — `test_looking_but_not_discovered`, despite its very test-like name, was never even looked at, because it lives in a file called `not_a_test_helper.py`, which doesn't match `pytest`'s discovery pattern. **The rule is genuinely just filename- and function-name-based**, by default: files named `test_*.py` or `*_test.py`, and inside them, functions named `test_*` (or methods on a class named `Test*`). Nothing about the *content* of a function makes it a test — nothing stops you from writing `def test_add(): pass` (a test that always passes, silently, because it never asserts anything) — discovery is purely a naming convention, so getting the name wrong (misspelling `tset_add`, or leaving off the `test_` prefix entirely) is a genuinely common way for a test to silently never run at all.

```
FLOW -- what happens when you run `pytest` with no arguments
=================================================================
1. pytest walks the current directory (and subdirectories) looking
   for files matching test_*.py or *_test.py
2. inside each matching file, it looks for functions starting with
   test_ (and classes starting with Test, methods starting with test_)
3. each match becomes one "test item" -- collected, but not yet run
4. pytest runs every collected item, one at a time, capturing pass/fail
5. a summary line reports totals: "N passed, M failed, ..."
```

---

## 3. Fixtures — reusable setup, injected by name

A **fixture** is a function decorated with `@pytest.fixture` that provides something a test needs — data, a connection, a temp file — and `pytest` hands it to any test that simply *asks for it by parameter name*:

```python
import pytest

@pytest.fixture
def sample_list():
    print("\n[fixture setup]")
    data = [1, 2, 3]
    yield data
    print("[fixture teardown]")

def test_uses_fixture(sample_list):
    assert sum(sample_list) == 6
```

Real output (`pytest -v -s`, `-s` so the `print()`s actually show):
```
test_features.py::test_uses_fixture
[fixture setup]
PASSED[fixture teardown]
```

Notice `test_uses_fixture(sample_list)` never calls `sample_list()` anywhere — `pytest` sees the parameter name `sample_list`, matches it against the fixture of the same name, calls it *for* the test, and hands the test whatever it produces. **`yield` splits the fixture into a before-half and an after-half**: everything before `yield` runs first (setup — here, building `data`), the `yield`ed value is what the test actually receives as `sample_list`, and everything *after* `yield` runs once the test finishes, pass or fail (teardown — here, just the print, but this is exactly where you'd close a file or a database connection). That's the direct fixture-shaped cousin of the context-manager doc's `__enter__`/`__exit__` split, and of the generator-based context managers from that same doc — same "pause here, resume later to clean up" shape.

Fixtures defined in a file called **`conftest.py`** are automatically available to every test file in that same directory (and subdirectories) — no import needed at all:

```python
# conftest.py
import pytest

@pytest.fixture
def shared_data():
    return {"user": "ani"}
```
```python
# test_uses_conftest.py
def test_shared(shared_data):
    assert shared_data["user"] == "ani"
```

Real output: `test_uses_conftest.py::test_shared PASSED`. `test_uses_conftest.py` never imports anything from `conftest.py` — `pytest` itself finds `conftest.py`, loads it, and makes every fixture defined there available by name across the whole directory, which is exactly why `conftest.py` is where teams put shared setup (a database connection, sample data, common mocks) instead of copy-pasting the same fixture into every test file.

---

## 4. Fixture scope — how often does setup actually run?

By default a fixture reruns fresh for *every single test that asks for it*. That's controllable with `scope=`:

```python
import pytest

@pytest.fixture(scope="function")   # default -- reruns for every test
def func_scoped():
    print("\n  [function-scoped setup]")
    return "x"

@pytest.fixture(scope="module")     # runs ONCE for the whole file
def module_scoped():
    print("\n  [module-scoped setup]")
    return "y"

def test_one(func_scoped, module_scoped):
    assert func_scoped == "x"

def test_two(func_scoped, module_scoped):
    assert module_scoped == "y"
```

Real output (`pytest -v -s`):
```
test_scope.py::test_one
  [module-scoped setup]

  [function-scoped setup]
PASSED
test_scope.py::test_two
  [function-scoped setup]
PASSED
```

`[module-scoped setup]` prints **once**, right before `test_one` — the first test in the file that needed it — and never again, even though `test_two` also asks for `module_scoped`. `[function-scoped setup]` prints **twice**, once per test, because that fixture's default scope reruns for every consumer. This matters for real performance and correctness: something genuinely expensive to set up (a database connection, a populated test database) is a great candidate for `scope="module"` or `scope="session"` (once for the *entire* test run) — but only for things that are safe to *share* across tests; anything a test might mutate belongs at the default `function` scope, so each test gets a clean, independent copy.

---

## 5. `@pytest.mark.parametrize` — one test function, many cases

```python
import pytest

@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (2, 2, 4), (0, 0, 0)])
def test_add_parametrized(a, b, expected):
    assert a + b == expected
```

Real output:
```
test_features.py::test_add_parametrized[1-2-3] PASSED
test_features.py::test_add_parametrized[2-2-4] PASSED
test_features.py::test_add_parametrized[0-0-0] PASSED
```

One function definition, **three separate test items** — `pytest` ran `test_add_parametrized` three times, once per tuple in the list, substituting `a`, `b`, `expected` each time, and reporting each run as its own pass/fail line (visible in the `[1-2-3]`-style suffix on each name). This directly replaces the "write the same test body five times with different numbers" pattern — one definition, one assertion, and a data table of cases instead of five near-duplicate functions.

---

## 6. `pytest.raises` — testing that an exception actually happens

```python
import pytest

def divide(a, b):
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b

def test_divide_raises():
    with pytest.raises(ValueError, match="cannot divide by zero"):
        divide(1, 0)
```

Real output: `test_divide_raises PASSED`. `pytest.raises(ValueError, ...)` is a context manager (the same `with` syntax from the context-managers doc) that expects the code inside its block to raise exactly that exception type — **the test passes *because* `divide(1, 0)` raised `ValueError`**, and would *fail* if `divide` raised nothing at all, or raised some other exception type. `match="cannot divide by zero"` additionally checks the exception's message against that regular expression, so this test would also fail if the code raised the right exception type but with unexpected wording. This is the direct, correct replacement for the old habit of wrapping code in a manual `try/except` and asserting inside it — `pytest.raises` states directly "an exception is the expected, correct outcome here."

---

## 7. Marks — `skip` and `xfail`

```python
import pytest

@pytest.mark.skip(reason="demonstrating skip")
def test_skipped():
    assert False

@pytest.mark.xfail(reason="demonstrating xfail")
def test_expected_to_fail():
    assert 1 == 2
```

Real output:
```
test_features.py::test_skipped SKIPPED (demonstrating skip)
test_features.py::test_expected_to_fail XFAIL (demonstrating xfail)
...
5 passed, 1 skipped, 1 xfailed in 0.02s
```

**`@pytest.mark.skip`** means "don't even run this" — useful for a test that depends on something not available right now (a service, a platform). **`@pytest.mark.xfail`** ("expected fail") means "run it, but a failure here is *known and expected*, don't count it as a real failure" — useful for a genuinely known bug you haven't fixed yet, so the test suite stays green while still keeping a record of the broken behavior. The crucial difference from simply deleting or commenting out a failing test: both marks still show up explicitly in the summary line (`1 skipped, 1 xfailed`), so nothing quietly disappears from the report — if `test_expected_to_fail` ever started *passing* unexpectedly, `pytest` would flag that too (as `XPASS`), telling you the known bug might be fixed now.

---

## 8. `monkeypatch` — safely faking things for one test

```python
import os

def get_api_key():
    return os.environ["API_KEY"]

def test_get_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "fake-key-123")
    assert get_api_key() == "fake-key-123"
```

Real output: `test_get_api_key PASSED`. `monkeypatch` is itself a built-in fixture (same injection mechanism as §3) that lets a test temporarily override environment variables, object attributes, dictionary items, or `sys.path`, **and automatically undoes every change once the test finishes** — pass or fail. That automatic cleanup is the entire point: without it, one test setting `API_KEY` to a fake value could leak into the *next* test if you did it by hand (`os.environ["API_KEY"] = ...` with no corresponding cleanup), causing a failure that has nothing to do with the second test's actual logic — one of the most confusing categories of bug in a real test suite (a test that only fails when run *after* another specific test).

---

## 9. Interview-distilled

"Why `pytest` over plain `assert` or `unittest`?" — plain `assert` gives a bare `AssertionError` with no detail (§1); `pytest` rewrites every `assert` in a test to capture and report the actual values involved, so you never need a custom message. Over `unittest`, it also avoids memorizing a different assertion method per comparison type (`assertEqual`, `assertTrue`, ...) — `assert` alone covers everything.

"How does `pytest` find tests?" — pure naming convention: files `test_*.py`/`*_test.py`, functions `test_*` inside them (§2). Nothing about a function's content marks it as a test — a misnamed function silently never runs.

"What's a fixture?" — a function providing setup (and, via `yield`, teardown) that a test receives just by naming it as a parameter — `pytest` matches by name and injects it automatically (§3). `conftest.py` fixtures are shared across a whole directory without any import.

"What does fixture `scope` control?" — how often the fixture's setup code actually reruns: `function` (default, every test) vs `module`/`session` (once, shared) — proven directly in §4 by a fixture that printed once vs. one that printed per-test.

"How do you test that code raises an exception?" — `with pytest.raises(SomeException):` around the code that should raise; the test *passes* because the exception happened, and fails if it doesn't, or if a different exception type is raised (§6).

"What's the difference between `skip` and `xfail`?" — `skip` never runs the test at all; `xfail` runs it but doesn't count a failure against the suite, because the failure is already known and expected — and if it unexpectedly starts passing, `pytest` flags that as `XPASS` (§7).

---

## Practice questions

1. **Reproduce the assert-rewriting difference, yourself.** Write a small function and a deliberately wrong assertion about it. Run it as a plain Python script first (confirm you get a bare `AssertionError`, no detail). Then wrap the same assertion in a `def test_...():` function and run it with `pytest` — confirm the failure report now shows the actual values, without you writing any custom message.

2. **Write a fixture with setup and teardown, and prove teardown runs.** Write a `@pytest.fixture` using `yield` that prints a setup message before `yield` and a teardown message after it. Write a test that uses it. Run with `pytest -s` and confirm both prints appear, in the right order, around the test itself.

3. **Parametrize a test over at least 4 cases**, including one case you expect to fail on purpose. Run it and confirm the failure report identifies exactly which parameter combination failed (via the `[params]` suffix in the test name), while the others still pass.

4. **Test an exception with `pytest.raises`, including the message.** Write a function that raises a specific exception with a specific message under some condition. Write a test using `pytest.raises(YourException, match="...")` that both confirms the exception type and checks part of the message. Then deliberately break the `match` string and confirm the test now fails, explaining in a comment why.

5. **Fixture scope, proven side by side.** Write two fixtures identical except for `scope` (one `function`, one `module` or `session`), each printing a setup message. Write two or more tests that both use both fixtures. Run with `pytest -s` and confirm, from the real print output, which fixture reran per test and which one ran only once.

---

*Same as always — write real code, run it, and paste your answers when ready. Say "next" and I'll build the doc for logging & profiling — the last topic in the Advanced group.*
