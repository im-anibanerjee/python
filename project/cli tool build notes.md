# Wknd 1-3 capstone: Transaction Ledger CLI — build notes

This file is the running transcript of the live-coding build, logged piece by piece as we go (see `cli tool spec.md` for the fixed assignment spec this build is working toward). Each section below is one piece of the tool: the code as it was written, the explanation of what/why/how, a pointer back to whichever earlier topic doc first covered the underlying idea, and the real questions that came up in chat while working through that piece, with their answers - not the tidy final version, the actual sticking points.

Nothing appears here until it's been explained in chat and typed by hand - this file is a record of what was already understood, not a preview of what's coming next.

---

## Piece 1: `InvalidTransactionError` — the custom exception

Before anything can validate a transaction, there needs to be something to raise when validation fails - so this comes first, even though it's the smallest piece.

This goes into a new file, `cli-tool/ledger.py`:

```python
class InvalidTransactionError(Exception):
    """Raised when a CSV row can't be turned into a valid Transaction."""
    pass
```

That's genuinely it for this piece - three lines.

**Why it looks like this:**

`class InvalidTransactionError(Exception):` follows the exact pattern from `04 python exceptions.md` - a custom exception is just a class that inherits from `Exception` (or a subclass of it). Inheriting from `Exception` is what makes Python treat it as a real, raisable, catchable error - it gets a message, a traceback, and the ability to be caught by `except InvalidTransactionError:` or by the broader `except Exception:`, all for free, purely from the inheritance.

The docstring (`"""..."""` right under the class line) is attached to the class itself (shows up via `help(InvalidTransactionError)`) - worth having here specifically because the class body is otherwise empty, so a bare `pass` with no explanation would look like an accident rather than a deliberate choice.

`pass` - no custom `__init__`, no extra fields. The entire reason to make this its own class instead of raising a plain `Exception("bad row")` everywhere is so that later code can write `except InvalidTransactionError:` and know for certain it's catching *only* our own validation failures - not accidentally swallowing an unrelated bug that happens to also raise a plain `Exception`. That specificity is the whole value of a custom exception here; it doesn't need extra data to earn its place.

This exception doesn't get used yet - that happens once the `Transaction` class exists, which is the next piece.

**Questions along the way:** none - understood on the first pass.

---

## Piece 2: the `Transaction` class - constructor only

This gets added below what's already there, still in `ledger.py`:

```python
from datetime import date

class Transaction:
    def __init__(self, txn_date: date, category: str, description: str, amount: float) -> None:
        self.txn_date = txn_date
        self.category = category
        self.description = description
        self.amount = amount
```

**Why it looks like this:**

`from datetime import date` - a real `date` object (not a plain string) is what lets later code do actual date math and comparisons - e.g. "is this transaction in September 2026" for the `filter --month` command - without re-parsing a string every time.

`def __init__(self, ...)` - the constructor, from `05 python oop.md`: the method Python calls automatically the instant you write `Transaction(...)`, whose job is to set up a brand-new object's starting state. `self` is that new object itself, always passed in automatically as the first parameter.

The type hints (`txn_date: date, category: str, description: str, amount: float`, `-> None`) are straight from `13 python type hints mypy.md` - unenforced at runtime, but documentation for a human reader and a real second line of defense if `mypy` is run against this file.

`self.txn_date = txn_date` (and the three lines after) - the actual storing step: each parameter passed in gets attached to `self` as an instance attribute, so it's still there later via `some_transaction.amount` from anywhere else in the program. The parameter is called `txn_date` rather than `date` on purpose, since `date` is already taken by the import at the top of the file - naming the parameter `date` too would shadow it.

**Questions along the way:** none this round - correct on first submission, with two small style notes (not bugs): a leftover commented-out duplicate `# from datetime import date` line right above the class (harmless since it's commented out, but worth deleting - the real import at the top of the file already covers it), and PEP8 spacing on the type hints (`txn_date: date` with a space after the colon, not `txn_date:date` - purely cosmetic, doesn't affect how Python or mypy reads it).

---

## Piece 3: `Transaction.from_row` — where the exception actually gets used

This is the part that ties Piece 1 and Piece 2 together: a classmethod that takes one raw CSV row and either builds a valid `Transaction` or raises `InvalidTransactionError`. It gets added inside the `Transaction` class, right after `__init__`:

```python
    @classmethod
    def from_row(cls, row: dict, row_number: int) -> "Transaction":
        raw_date = row.get("date", "")
        raw_category = row.get("category", "")
        raw_amount = row.get("amount", "")

        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            raise InvalidTransactionError(f"row {row_number}: invalid date {raw_date!r}")

        if not raw_category.strip():
            raise InvalidTransactionError(f"row {row_number}: category is empty")

        try:
            parsed_amount = float(raw_amount)
        except ValueError:
            raise InvalidTransactionError(f"row {row_number}: invalid amount {raw_amount!r}")

        return cls(parsed_date, raw_category, row.get("description", ""), parsed_amount)
```

**Why it looks like this:**

`@classmethod` and `cls` - a regular method (like `__init__`) automatically receives `self`, one specific, already-existing object. A classmethod instead automatically receives `cls`, the class itself, not an instance. This is needed here because the whole point of `from_row` is to build a `Transaction` from scratch - there's no `self` yet, since no object exists until this method finishes. `cls(...)` on the last line means "call `Transaction(...)`" - written as `cls` instead of hardcoding `Transaction` so this still works correctly if the class is ever subclassed.

`row: dict` - one row from the CSV, already read in as a dictionary of column-name to string value (e.g. `{"date": "2026-09-01", "category": "groceries", ...}`) - how that dictionary actually gets produced comes in a later piece, when the CSV-loading code is written.

`-> "Transaction"` - the return type hint is in quotes, unlike `-> None` in `__init__`. At the moment this line is defined, the class `Transaction` isn't fully finished being built yet (still inside its own body), so the name `Transaction` technically doesn't exist as a usable value yet. Writing it as a string is a **forward reference** - it tells type checkers like `mypy` "this refers to the class currently being defined," without Python needing to actually resolve it at that exact moment.

`date.fromisoformat(raw_date)` inside `try`/`except ValueError` - the actual validation for the date column, and exactly the pattern from `04 python exceptions.md`: attempt the risky operation, catch the *specific* exception it can raise, and convert it into our own, more meaningful `InvalidTransactionError` - this is **exception chaining/translation**, and it's why callers of `from_row` only ever need to know about one exception type, not every possible internal failure.

`if not raw_category.strip():` - the empty-category check from the spec. `.strip()` removes leading/trailing whitespace first, so a category of `"   "` (just spaces) correctly counts as empty too, not just `""`.

`float(raw_amount)` in its own `try`/`except ValueError` - same translation pattern as the date, for the amount column.

`f"row {row_number}: invalid date {raw_date!r}"` - the `!r` calls `repr()` on the value instead of `str()`, so an empty `raw_date` shows as `''` (visibly empty) instead of vanishing into nothing in the middle of the sentence.

**Questions along the way:**

Q: Why are we using a classmethod here? Why not a usual method with `self`?
A: `self` only exists once an object has already been built - it *is* that object. `from_row`'s whole job is to build the object in the first place, before any `Transaction` exists, so there's nothing to be `self` yet. `cls` receives the class itself, available the moment the class is defined, long before any instance exists - proven with a small side demo: `Demo.class_method()` works fine with no instance anywhere and prints `got cls = <class '__main__.Demo'>`, while `Demo.instance_method()` (called the same way, no instance) fails with `TypeError: Demo.instance_method() missing 1 required positional argument: 'self'`. That's the exact chicken-and-egg problem a classmethod-based factory avoids.

Q: Brief explanation of the `!r` (repr) format in `f"invalid amount {raw_amount!r}"`, with examples?
A: `{value}` in an f-string calls `str(value)`, the friendly display version. `{value!r}` calls `repr(value)`, the unambiguous/debug version - for a string, that means wrapping it in quotes. Real examples: `raw_amount = ""` prints as nothing at all with plain `{raw_amount}` ("invalid amount ") but as `''` with `{raw_amount!r}` ("invalid amount ''") - visibly empty instead of invisible. Same for whitespace-only input (`"  "`): plain shows two invisible spaces, `!r` shows `'  '` so the spaces are actually visible. For an ordinary value like `"12,00"` it barely matters (`12,00` vs `'12,00'`), but for empty/blank edge cases `!r` is the difference between a debuggable message and a confusing one.

Q: (pasted the `-> "Transaction"` forward-reference explanation) "i did not understand this part" - asked for it to be explained more clearly.
A: Proved it concretely rather than just restating it. Reproducing the same situation - a classmethod inside a class, returning that same class, unquoted:
```python
class Foo:
    @classmethod
    def make(cls) -> Foo:
        pass
```
raises `NameError: name 'Foo' is not defined` immediately, genuinely, while Python is still defining the class - because Python runs a class body top-to-bottom like a small script, and the class object itself only gets created and named *after* the whole body finishes running. So while still inside `def make(...)`, the name `Foo` doesn't exist as a usable value yet, and writing `-> Foo` unquoted asks Python to look it up right then. Quoting it (`-> "Foo2"`) sidesteps this entirely: `"Foo2"` is just a string literal, nothing to look up, so nothing fails - it gets stored as literal text (`Foo2.make.__annotations__` shows `{'return': 'Foo2'}`, the text, not the class object). A tool like `mypy` reads that string later, after the whole file has been read and the class genuinely exists, and checks it as if it were the real type. Plain Python at runtime never resolves that string at all.

Q: "So here from the method from_row you are extracting data from the CSV file, creating a class by passing cls(...), and when you are returning this cls, then it calls the init method and hence creates the transaction object.. is my understanding correct?"
A: Close, but one correction: it's not *returning* `cls` that triggers `__init__` - it's the *call* `cls(parsed_date, raw_category, ...)` itself, and that already happens, fully, before the `return` statement runs at all. Proved with print statements dropped into both `__init__` and `from_row`: the order of real printed output was `[from_row] about to call cls(...)` → `[__init__ running] building the object, amount=42.5` → `[from_row] cls(...) has already returned a real object: <...>` → `[from_row] now returning it`. `__init__` running appears *between* the "about to call" and "already returned" lines - so by the time `from_row` reaches its own `return`, the object is 100% already finished. `return` doesn't cause construction; it just hands back an object that was already built a line earlier.

Q: "What does fromisoformat is doing?"
A: `date.fromisoformat(raw_date)` is a constructor on the `date` class that takes a string and, if it's in exact `YYYY-MM-DD` shape (ISO 8601), turns it into a real `date` object with working `.year`/`.month`/`.day` attributes. It does two things at once: parsing the text apart, and validating the shape was right to begin with - real verified proof: `date.fromisoformat("2026-09-01")` returns a proper `date` object, while `date.fromisoformat("2026/09/01")`, `"01-09-2026"`, `"not-a-date"`, and `""` all raise `ValueError: Invalid isoformat string: '...'` rather than silently guessing or returning `None`. That's exactly why `from_row` catches `ValueError` specifically around this call - it's the one and only documented way this constructor fails.

---

## Piece 4: logging setup

Before `TransactionLedger` can report which rows got skipped, there needs to be somewhere for that report to go - so this small setup piece comes first.

Added near the top of `ledger.py`, right after the existing imports:

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
```

**Why it looks like this:**

`import logging` - Python's built-in logging module, from `15 python logging profiling.md`.

`logging.basicConfig(level=logging.INFO, format=...)` - one-time setup. `level=logging.INFO` means only `INFO` and above (`INFO`, `WARNING`, `ERROR`, `CRITICAL`) actually get emitted - a `.debug()` call anywhere in this file is silently dropped, deliberately; a small CLI tool doesn't need debug noise, but warnings about skipped rows must always show. `format="%(levelname)s: %(message)s"` keeps output simple for a CLI tool (e.g. `WARNING: row 3: invalid date`) rather than the default format, which adds a timestamp and logger name - useful for a server, overkill here.

`logger = logging.getLogger(__name__)` - the object `.warning(...)`/`.info(...)` will actually get called on later. `__name__` holds the current module's name (`"ledger"` when imported, `"__main__"` if run directly) - using it instead of a hardcoded string is the standing convention from the logging doc, so log messages are automatically labeled with where they came from if the project ever grows to multiple files.

This logger isn't used yet - that happens in `TransactionLedger`, the next piece, which is where rows actually get skipped and need to be reported.

**Questions along the way:** none for this piece. One minor recurring habit flagged again, not a bug: another leftover commented-out duplicate line (`# import logging`), same pattern as the earlier `# from datetime import date` - harmless, but worth breaking the habit of leaving a commented-out copy of an import next to its real one.

---

## Piece 5: `TransactionLedger` — the constructor

```python
class TransactionLedger:
    def __init__(self) -> None:
        self.transactions: list[Transaction] = []
        self.skipped_count: int = 0
```

**Why it looks like this:**

`self.transactions: list[Transaction] = []` - where every successfully-parsed `Transaction` will live once loading happens. The type hint `list[Transaction]` says "a list, specifically of `Transaction` objects," not just `list` on its own, which would tell a reader (and `mypy`) nothing about what's inside it. Starting it empty is the same pattern as any "collector" object - nothing's been loaded yet, so there's nothing to hold yet.

`self.skipped_count: int = 0` - a running tally of how many rows failed validation and got skipped, per the spec's requirement that loading reports how many rows loaded successfully and how many were skipped. Starts at `0` for the same reason.

Unlike `Transaction`, which needs data handed to it immediately to mean anything, a `TransactionLedger` starts out genuinely empty and only fills up once a loading method is called on it - which is the next piece.

**Questions along the way:** none.

---

## Piece 6: `load_csv` — the method that actually reads a file

This is the piece where `Transaction.from_row`, `InvalidTransactionError`, and `logger` all finally get used together. Added inside `TransactionLedger`, right after `__init__`, along with one new top-of-file import (`import csv`):

```python
    def load_csv(self, path: str) -> None:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row_number, row in enumerate(reader, start=1):
                try:
                    transaction = Transaction.from_row(row, row_number)
                except InvalidTransactionError as e:
                    logger.warning(str(e))
                    self.skipped_count += 1
                else:
                    self.transactions.append(transaction)

        logger.info(
            f"loaded {len(self.transactions)} transactions, skipped {self.skipped_count}"
        )
```

**Why it looks like this:**

`with open(path, newline="") as f:` - the context-manager pattern from `09 python context managers.md`: `open()` returns a file object, `with` guarantees it gets closed automatically once the block ends, even if something inside raises. `newline=""` is a real, documented requirement when reading CSV files in Python, not optional boilerplate - without it, the csv module can misread line endings inside quoted fields on some systems.

`reader = csv.DictReader(f)` - turns raw text lines into the per-row `dict` that `from_row` expects. It reads the first line as column headers, and every line after that becomes a dict keyed by those headers.

`for row_number, row in enumerate(reader, start=1):` - `enumerate(..., start=1)` pairs each row with a running count starting at 1, and that `row_number` threads straight through to `from_row`'s error messages.

`try: ... except InvalidTransactionError as e: ... else: ...` - the heart of the spec's "skip bad rows, keep going" requirement. `else` runs only if the `try` block did *not* raise, so `self.transactions.append(transaction)` only happens for rows that genuinely succeeded - a more precise shape than putting the append inside the `try` block itself.

`logger.warning(str(e))` - a failing row gets logged as a warning and the loop moves on; `str(e)` pulls the actual message text out of the caught `InvalidTransactionError`.

`logger.info(...)` after the loop - one final summary line reporting how many loaded vs. skipped, matching the spec's requirement exactly.

**Questions along the way:**

Q: (asked for a diagram) how does the raw CSV actually become the row-dicts `from_row` expects?
A: Answered with a real small CSV and a diagram showing the header line becoming `reader.fieldnames` (the dict keys every row uses), and each following line becoming one dict, verified against real `csv.DictReader` output: `{'date': '2026-09-01', 'category': 'groceries', 'description': 'Big Bazaar', 'amount': '-54.20'}` etc.

Q: "for row_number, row in enumerate(reader, start=1):, Explain enumerate again. And why not simply using -> for row_number, row in reader?"
A: `enumerate(iterable, start=N)` turns each item into a `(number, item)` pair counting up from `N`. Real demo:
```python
print(list(enumerate(["apple", "banana", "cherry"], start=1)))
```
```
[(1, 'apple'), (2, 'banana'), (3, 'cherry')]
```
Without `enumerate`, tried exactly the alternative asked about:
```python
with open("demo.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row_number, row in reader:
        print(row_number, row)
```
```
ValueError: too many values to unpack (expected 2)
```
`reader` hands out one row-dict at a time, not a `(number, item)` pair - `for row_number, row in reader:` tries to unpack that single dict (4 keys: `date`, `category`, `description`, `amount`) directly into 2 loop variables. Python unpacks a dict by iterating its keys, so it genuinely tries to fit 4 keys into 2 variables and fails. `enumerate` is what wraps each row-dict together with a running count first, so there's an actual `(number, dict)` pair to unpack.

Confirmed the exact shape afterward:
```python
with open("demo.csv", newline="") as f:
    reader = csv.DictReader(f)
    pairs = list(enumerate(reader, start=1))
    print(pairs)
    for row_number, row in pairs:
        print(type(row_number), type(row))
```
```
[(1, {'date': '2026-09-01', 'category': 'groceries', 'description': 'Big Bazaar', 'amount': '-54.20'}), (2, {'date': '2026-09-03', 'category': 'salary', 'description': 'September salary', 'amount': '2500.00'})]
<class 'int'> <class 'dict'>
<class 'int'> <class 'dict'>
```
`enumerate(reader, start=1)` really does produce `[(1, {row1 dict}), (2, {row2 dict}), ...]`, with the number going into `row_number` and the dict into `row` - exactly the shape needed for `Transaction.from_row(row_number, row)` to work.

Q: can the `for` loop move outside the `with` block, since `reader` already holds the CSV's content?
A: No - corrected with real proof, not just an explanation. Tried exactly that:
```python
with open("demo.csv", newline="") as f:
    reader = csv.DictReader(f)
# for loop moved OUTSIDE the with block here

for row_number, row in enumerate(reader, start=1):
    print(row_number, row)
```
```
ValueError: I/O operation on closed file.
```
`csv.DictReader` is lazy: it doesn't read anything from the file upfront, only when the loop actually asks for the next row - `reader` is really just a thin recipe that says "go pull the next line from `f`," not a container holding real content. The moment the `with` block ends, `f.__exit__` runs and closes the file (`f.closed` confirmed `True` right after, checked directly) - exactly the guarantee from `09 python context managers.md`. Since `reader` never held real data, only a live connection to `f`, asking it for the next row after `f` is closed means asking a closed file for more bytes, which Python correctly refuses. So the loop has to stay *inside* the `with` block - not a style preference, required for the reading to actually happen while the file is open.

Q: "But what if I want to read it all at once? Is that possible?"
A: Yes, genuinely possible - the trick is `list(reader)`, verified for real:
```python
with open("demo.csv", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)   # pulls everything into memory NOW, while the file is still open

# genuinely outside the with block, file already closed
for row_number, row in enumerate(rows, start=1):
    print(row_number, row)
```
```
f.closed: True
type(rows): <class 'list'>

1 {'date': '2026-09-01', 'category': 'groceries', 'description': 'Big Bazaar', 'amount': '-54.20'}
2 {'date': '2026-09-03', 'category': 'salary', 'description': 'September salary', 'amount': '2500.00'}
```
`f.closed` is still `True` here, same as before - but the loop works fine this time, because `list(reader)` forces every row to actually be read and converted to a dict *right then, while `f` is still open*, collecting them all into a real, ordinary Python list with no connection to the file at all anymore. Once you have that list, it can be iterated, saved, or passed around completely independent of whether the file is still open.

Trade-off flagged: `list(reader)` reads the *entire* file into memory at once - completely fine for a small transactions CSV, but for a genuinely huge file (millions of rows) this is the real reason the lazy, one-row-at-a-time version (what `load_csv` actually uses) is usually preferred: it only ever holds one row in memory at a time, not the whole file. This exact "read it all upfront vs. stream it" trade-off comes back properly in Wknd 8-9 (pandas/ETL, "chunking large data") - `load_csv` deliberately keeps the streaming version as the better habit to build now, even though the sample file here is tiny.

---

## Piece 7: `log_execution_time` — the decorator

This is the second of the four required concepts (after the custom exception): a decorator that wraps `load_csv` so every call to it automatically gets timed and logged, without changing `load_csv`'s own code at all. Two new imports go at the top of `ledger.py`, and the decorator itself goes above `TransactionLedger`, before `load_csv` gets `@log_execution_time` placed directly above it:

```python
import functools
import time

def log_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} took {elapsed:.4f}sec")
        return result
    return wrapper
```

```python
class TransactionLedger:
    ...
    @log_execution_time
    def load_csv(self, path: str) -> None:
        ...
```

**Why it looks like this:**

`def log_execution_time(func):` - the outer function. Its only job is to receive the function being decorated (`load_csv`, though it never hardcodes that name - `func` could be anything) and hand back a replacement for it. `@log_execution_time` above `load_csv` is really just shorthand for `load_csv = log_execution_time(load_csv)`.

`def wrapper(*args, **kwargs):` - the actual replacement function, defined *inside* `log_execution_time` so it can still see `func` even after `log_execution_time` itself has finished running (a closure). `*args, **kwargs` matter specifically because `load_csv` is an instance method - called as `some_ledger.load_csv(path)`, which under the hood is really `load_csv(some_ledger, path)`. `wrapper` doesn't know in advance it'll be handed `self` plus a `path`; `*args`/`**kwargs` scoop up whatever arguments actually show up and pass them straight through to `func`, so the same decorator works on any function regardless of its signature.

`@functools.wraps(func)` above `wrapper` - without this, `load_csv.__name__` would become `"wrapper"` after decoration, and the log line would misleadingly say `wrapper took ...` instead of `load_csv took ...`. `functools.wraps` copies `func`'s real name (and docstring) onto `wrapper`.

`time.perf_counter()` rather than `time.time()` - `perf_counter` is monotonic (never jumps backward, e.g. if the system clock adjusts) and higher-resolution, which is what makes it the correct tool specifically for measuring elapsed duration rather than reporting wall-clock time.

`result = func(*args, **kwargs)` then `return result` at the end of `wrapper` - `wrapper` has to actually run the real function and capture what it returns, then hand that same value back to whoever called `load_csv`, so that from the outside, calling the decorated `load_csv` looks and behaves identically to calling the original - just with timing added invisibly around it.

`return wrapper` at the end of `log_execution_time` - the outer function must hand `wrapper` back; that's the actual replacement for `load_csv`.

**Questions along the way:**

Q: "So what is the essence of this decorator here? What writing it above @load_csv will do"
A: `load_csv` itself never changes. Every time anyone calls `some_ledger.load_csv(path)`, Python quietly runs it through the wrapper first - start a stopwatch, run the real `load_csv` exactly as written, stop the stopwatch, log how long it took, then hand back whatever `load_csv` returned, as if the decorator was never there. The decorator bolts "measure and log duration" on from the outside, as a reusable layer - if the same timing behavior were ever wanted on another method, `@log_execution_time` could go above that one too, with zero copy-pasted stopwatch code. Concretely, this means a log line like `INFO: load_csv took 0.0139sec` should appear right after the usual "loaded X transactions, skipped Y" line.

**Bug found and fixed (real bug, not style):** first submission was missing `return wrapper` at the end of `log_execution_time` entirely. Verified concretely - running the tool for real raised:
```
TypeError: 'NoneType' object is not callable
```
Because `log_execution_time` never returned `wrapper`, it implicitly returned `None` - so `load_csv = log_execution_time(load_csv)` silently set `load_csv` to `None` on the class, and calling `some_ledger.load_csv(...)` meant calling `None(...)`. A second, smaller issue caught in the same pass: `wrapper` computed `result = func(*args, **kwargs)` but never `return result`ed it - harmless today only because `load_csv` doesn't return anything meaningful anyway, but it would silently discard a return value if this same decorator were ever reused on a function that does return something. Both fixed: `return wrapper` added at the end of `log_execution_time`, `return result` added at the end of `wrapper`.

---

## Piece 8: `ReportWriter` — the context manager

This is the last of the four required concepts. `ReportWriter` opens the report output file, writes a header on entry, and guarantees a footer gets written on the way out - even if something raises while the report body is being written. One new import, alongside the existing `date` import at the top of `ledger.py`:

```python
from datetime import date, datetime

class ReportWriter:
    """ Context manager: opens a report file, writes a header on entry, and
    guarantees a footer is written on exit - even if the body raises """

    def __init__(self, path: str, title: str, transaction_count: int) -> None:
        self.path = path
        self.title = title
        self.transaction_count = transaction_count
        self.file = None

    def __enter__(self) -> "ReportWriter":
        self.file = open(self.path, "w")
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.file.write(f"{self.title}\n")
        self.file.write(f"generated: {timestamp}\n")
        self.file.write("\n")
        return self

    def write_line(self, text: str) -> None:
        self.file.write(text + "\n")

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.file.write("\n")
        self.file.write(f"transactions considered {self.transaction_count}\n")
        self.file.write("-- end of report --\n")
        self.file.close()
        return False
```

**Why it looks like this:**

`with open(...)` (used everywhere else so far) already guarantees the file gets *closed* no matter what - but it doesn't guarantee any specific content gets *written* if a crash happens before that line runs. `ReportWriter` exists specifically to add that second guarantee for the footer, which a plain `open()`/`write()`/`close()` sequence can't provide.

`self.file = None` in `__init__`, actually opened in `__enter__` - deliberate split. `__init__` only remembers *what* to do later (path, title, count); `__enter__` is *when* the file actually opens, at the moment the `with` block starts.

`def __enter__(self) -> "ReportWriter":` - runs once, right when `with ReportWriter(...) as report:` executes. Opens the file, writes the header (title + a `datetime.now()` generation timestamp), and returns `self` so the caller gets a `ReportWriter` to call `write_line` on.

`write_line` - a small convenience method so calling code never has to reach into `report.file.write(...)` directly or remember the trailing `\n` itself.

`def __exit__(self, exc_type, exc_value, traceback) -> bool:` - this exact three-parameter signature is required by the `with` protocol. Runs once, unconditionally, when the block ends - whether it ended normally or via a crash. Writes the footer (transaction count + `-- end of report --`) and closes the file either way. `return False` means "I'm not suppressing whatever exception happened - let it keep propagating after I've cleaned up," which is what makes the guarantee real: `ReportWriter` cleans up and still lets the original bug surface.

**Questions along the way:**

Q: "Am not understanding what is the report manager context is used/essential for, also please explain in short detail again what is entry and exit, use of write_line, and what is file.write and file.close"
A: Answered with two real demos rather than more words. First, a minimal `Demo` class with nothing but print statements in `__enter__`/`__exit__`, run twice - once with nothing going wrong, once with a `raise ValueError` inside the `with` block:
```
--- normal case, nothing goes wrong ---
[enter] running - opening things up
[body] doing normal work
[exit] running - cleaning up, no matter what
  exc_type passed in: None

--- crash case, something goes wrong inside the block ---
[enter] running - opening things up
[body] about to crash
[exit] running - cleaning up, no matter what
  exc_type passed in: <class 'ValueError'>
caught outside the with block: something broke
```
`[body] this line never runs` never printed in the crash case (the crash stopped the body immediately), but `[exit]` printed anyway in both cases - proof that `__enter__` runs once at the start of the block and `__exit__` runs once at the end, always, regardless of how the block ended. Second, `file.write`/`file.close` proven directly:
```python
f = open("demo.txt", "w")
print("is file closed right after opening?", f.closed)
f.write("first line\n")
f.write("second line\n")
f.close()
print("is file closed after f.close()?", f.closed)
print(open("demo.txt").read())
```
```
is file closed right after opening? False
is file closed after f.close()? True
first line
second line
```
`open(path, "w")` returns a live file object; `f.write(text)` appends into its internal buffer (no automatic `\n`, which is exactly why `write_line` adds one); `f.close()` flushes to disk and is what actually flips `f.closed` to `True` - the same thing `with open(...)` was doing automatically all along, now being done by hand inside `ReportWriter.__exit__`. `write_line` itself is just a wrapper around `self.file.write(...)` so calling code doesn't need to know `ReportWriter` is holding a real file object at all.

Q: "why can't we simply use with to write the report? why use this specifically this context manager"
A: Proved the actual difference rather than just restating it. Plain `with open(...)`, deliberately crashing partway through the body:
```python
with open("report_plain.txt", "w") as f:
    f.write("MY REPORT\n")
    f.write("generated: 2026-09-20\n\n")
    f.write("total income: 2500.00\n")
    raise ValueError("something broke while computing by-category totals")
    f.write("total expenses: -800.00\n")   # never reached
    f.write("-- end of report --\n")        # never reached
```
Real content that landed on disk:
```
MY REPORT
generated: 2026-09-20

total income: 2500.00
```
File genuinely closed (`f.closed` → `True`), but no footer at all - the crash jumped straight out of the block, skipping every line after it. Same crash, through `ReportWriter` instead:
```python
with ReportWriter("report_via_reportwriter.txt", "MY REPORT", 5) as report:
    report.write_line("total income: 2500.00")
    raise ValueError("something broke while computing by-category totals")
    report.write_line("total expenses: -800.00")   # never reached
```
Real content on disk:
```
MY REPORT
generated: 2026-09-20

total income: 2500.00

transactions considered: 5
-- end of report --
```
Footer's there. `open()`'s built-in `__exit__` only knows how to close a file; `ReportWriter`'s own `__exit__` closes the file *and* writes the footer first, unconditionally - a guarantee `with open()` alone was never built to provide.

**Bugs found and fixed (real bugs, not style) - took three rounds of "done" to actually land:**

Round 1 ("done"): pulling the file showed no changes had been saved at all - same file as before any fixes, same pattern as Piece 5's "missed to save." Flagged plainly with no guessing.

Round 2 ("done" again): two real, crashing bugs in the first submission's `__exit__`:
```python
def __exit__(self, exc_type, exc_value, traceback) -> bool:
    self.write('\n')                                            # bug
    self.file.write(f'transactions considered {self.transaction_count}\n')
    self.file.write('--end report --\n')
    file.close()                                                # bug
    return False
```
Running it for real against a test report crashed immediately:
```
CRASHED: AttributeError 'ReportWriter' object has no attribute 'write'
```
`self.write(...)` doesn't exist as a method (only `write_line` does, and that's not what was wanted here) - needed to be `self.file.write(...)`, matching the pattern of the two lines right after it. `file.close()` would have failed too (`file` is not a defined name - `NameError`), needing to be `self.file.close()`; never reached because the line above it crashed first. Both fixed on this round. Two more issues flagged in the same message, not yet fixed: header typo `f'genrated {timestamp}\n'` (missing "e", missing colon) and footer text `'--end report --\n'` not matching the spec's literal `-- end of report --`.

Round 3 ("check now"): footer text fixed to `-- end of report --` correctly; header typo fixed to "generated" but still missing its colon (`f'generated {timestamp}\n'`). Flagged the one remaining character.

Round 4 ("done"): colon added - `f'generated: {timestamp}\n'`. All four issues genuinely resolved.

One more instance of the same recurring habit, not yet cleaned up: `# from datetime import date, datetime` left commented out directly above `class ReportWriter`, alongside the real import at the top of the file - fifth occurrence of this pattern across the build.

`ReportWriter` is genuinely done: all four required concepts (custom exception, decorator, context manager, and the class-based design running through all of it) now exist and work in `ledger.py`.

**Addendum to Piece 8 - design question: why not a custom context manager for reading too?**

Q: "Another question from previous topic, why while writing we are using self made context manager and while reading we are using with as context manager? Could we have written self made context manager for reading the file also? If so then how would it be? And why we did not use self made context manager if we could have self made context manager for reading"
A: Reading's entire job is "open this file, make sure it gets closed when done, even if a row crashes while parsing" - and that's exactly and completely what `open()`'s own `__enter__`/`__exit__` already does, for free. Writing needed a custom `ReportWriter` because the job there is more than open/close - a specific header must be written on entry and a specific footer on exit, guaranteed, and `open()` has no idea what a header or footer is; that's business logic only our own class can provide.

Yes, a custom context manager for reading could genuinely have been written - proven for real rather than just described:
```python
import csv

class TransactionReader:
    def __init__(self, path):
        self.path = path
        self.file = None

    def __enter__(self):
        self.file = open(self.path, newline='')
        reader = csv.DictReader(self.file)
        return reader   # hand back the DictReader, not self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()
        return False

# using the custom context manager
with TransactionReader('demo.csv') as reader:
    rows_via_custom = list(reader)

# using plain with open(), the way load_csv actually does it
with open('demo.csv', newline='') as f:
    reader2 = csv.DictReader(f)
    rows_via_plain = list(reader2)

print('via custom TransactionReader:', rows_via_custom)
print('via plain with open():      ', rows_via_plain)
print('identical result?', rows_via_custom == rows_via_plain)
```
```
via custom TransactionReader: [{'date': '2026-09-01', 'category': 'groceries', 'description': 'Big Bazaar', 'amount': '-54.20'}, {'date': '2026-09-03', 'category': 'salary', 'description': 'September salary', 'amount': '2500.00'}]
via plain with open():       [{'date': '2026-09-01', 'category': 'groceries', 'description': 'Big Bazaar', 'amount': '-54.20'}, {'date': '2026-09-03', 'category': 'salary', 'description': 'September salary', 'amount': '2500.00'}]
identical result? True
```
Both approaches produce byte-for-byte identical results, so `TransactionReader` would genuinely work. It wasn't used because it would add a whole extra class that does *nothing* `open()` doesn't already do on its own: `TransactionReader.__enter__` opens the file and wraps it in `DictReader` - no extra work beyond what one line inside a `with` block already does. `TransactionReader.__exit__` just closes the file - literally identical to what `open()`'s own `__exit__` already does. A custom `__enter__`/`__exit__` earns its place only when it guarantees some *extra* behavior beyond plain open/close (like `ReportWriter`'s header/footer guarantee); when plain open/close is genuinely all that's needed, wrapping it in another class is just extra ceremony with no new guarantee behind it. One place this calculus would change: if "open a CSV and get a `DictReader`" were a recipe repeated in several different places across the codebase, a small reader class could be worth it purely to avoid retyping those two lines everywhere - here it's used exactly once, in `load_csv`, so there's no duplication to eliminate either.

---

## Piece 9: `TransactionLedger` summarizing methods

Before `cli.py` can wire up any commands, `TransactionLedger` needs to actually be able to answer "what's my total income," "what did I spend by category," and "what happened in a given month." Five small, reusable methods, added inside `TransactionLedger`, after `load_csv`:

```python
    def total_income(self) -> float:
        return sum(t.amount for t in self.transactions if t.amount > 0)

    def total_expenses(self) -> float:
        return sum(t.amount for t in self.transactions if t.amount < 0)

    def net(self) -> float:
        return self.total_income() + self.total_expenses()

    def by_category(self) -> dict:
        totals = {}
        for t in self.transactions:
            totals[t.category] = totals.get(t.category, 0.0) + t.amount
        return totals

    def filter_by_month(self, month: str) -> "TransactionLedger":
        filtered = TransactionLedger()
        filtered.transactions = [
            t for t in self.transactions if t.txn_date.strftime("%Y-%m") == month
        ]
        filtered.skipped_count = self.skipped_count
        return filtered
```

**Why it looks like this:**

`sum(t.amount for t in self.transactions if t.amount > 0)` - a **generator expression**: like a list comprehension but with `()` instead of `[]`, producing values one at a time instead of building a whole list first. `sum()` only needs to add numbers one at a time, so the generator form is the leaner tool here. `t.amount > 0` is the income filter (spec's convention: positive means money in); `total_expenses` is the same shape with `< 0`.

`net(self)` - calls the two methods above and adds them. Since expenses are already negative numbers, "income + expenses" correctly gives the net, with no subtraction needed anywhere.

`by_category(self)` - `totals.get(t.category, 0.0) + t.amount` is the same `.get()` pattern as `row.get("date", "")` from Piece 3: "give me the running total for this category, or `0.0` if it hasn't been seen yet," then store the updated total back.

`filter_by_month(self, month: str) -> "TransactionLedger":` - rather than writing separate month-aware totaling logic, this builds a *second*, smaller `TransactionLedger` containing only the matching month's transactions and hands it back. `t.txn_date.strftime("%Y-%m")` turns a real `date` object back into a string like `"2026-09"` for comparison against `month`. Once that filtered ledger exists, `filtered.total_income()`, `filtered.by_category()`, etc. all just work, unmodified - the payoff of having written those as methods on the class instead of loose functions.

One-line docstrings were also requested and added for `load_csv`, `total_income`, `total_expenses`, `net`, and `by_category`, `filter_by_month` (matching the lowercase, one-line comment style already used across the file) - `__init__` didn't get one, left as-is, not blocking.

**Questions along the way:** none.

---

## Piece 10: `cli.py` - the `argparse` parser

First piece of `cli.py`, the `argparse` entry point. Before touching the three-command structure, the concept: whatever gets typed after `python cli.py`, Python hands to the script as a raw list of text strings (`sys.argv`) - no structure, no idea what's a flag or what value belongs to it. `argparse` (Python's built-in module for this) is what turns that flat list into something usable: you describe what arguments your program accepts, and it parses, validates, and generates `--help` text for you. This CLI needs three different "verbs" (`summary`, `by-category`, `filter`), each with its own flags - `argparse` has **subparsers** built for exactly this shape, where each subcommand gets its own mini-parser nested inside the main one.

Code to type, a new file `cli.py` alongside `ledger.py`:

```python
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cli.py", description="Transaction Ledger CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--input", required=True)
    summary_parser.add_argument("--report", required=True)

    by_category_parser = subparsers.add_parser("by-category")
    by_category_parser.add_argument("--input", required=True)
    by_category_parser.add_argument("--report", required=True)

    filter_parser = subparsers.add_parser("filter")
    filter_parser.add_argument("--input", required=True)
    filter_parser.add_argument("--report", required=True)
    filter_parser.add_argument("--month", required=True)

    return parser
```

**Why it looks like this:**

`def build_parser() -> argparse.ArgumentParser:` - wrapped in its own function so the parser-building logic is a clean, separate, reusable piece, nothing about it depends on actually running the program yet.

`parser = argparse.ArgumentParser(prog="cli.py", description=...)` - the top-level parser. `prog="cli.py"` is just what shows up in auto-generated `--help`/error text.

`subparsers = parser.add_subparsers(dest="command", required=True)` - creates the subcommand system. `dest="command"` means "whichever subcommand name was used, store it on `args.command`." `required=True` means running `python cli.py` with no subcommand at all is itself an error.

`summary_parser = subparsers.add_parser("summary")` then `.add_argument("--input", required=True)` - each subcommand gets its own mini-parser; flags get added to that specific one, not the top-level `parser`. `required=True` on each flag means `argparse` itself rejects the call with a clear error if the flag is missing - no `if` statements needed.

`filter_parser` gets the extra `--month` flag the other two don't have - each subcommand only accepts what actually makes sense for it.

**Questions along the way:**

Q: "Did not understand: Right now, if you ran python cli.py summary --input sample_data/transactions.csv --report out.txt, Python would just hand your script a raw list of text: ['summary', '--input', 'sample_data/transactions.csv', '--report', 'out.txt'] (that's sys.argv[1:], literally just strings, no structure). You could parse that by hand — check argv[0] equals "summary", hunt for "--input" and grab the next item — but that gets messy fast, and it's exactly the kind of tedious, error-prone parsing argparse (Python's built-in module for this) exists to handle: you describe what arguments your program accepts, and it does the parsing, validation, and even the --help text generation for you. And this: Real proof: parser.parse_args([...]) turns that flat list of strings into a Namespace object — a plain object where args.command, args.input, args.report, args.month all exist as real attributes you can read directly, no manual string-hunting needed. dest='command' is what makes the which subcommand was used show up as args.command; each subparser (summary_parser, filter_parser) only knows about its own flags, so filter's --month doesn't even exist as an option under summary"
A: Slowed down with real proof instead of restating it. A tiny throwaway script printing `sys.argv` directly, run as `python manual_demo.py summary --input sample_data/transactions.csv --report out.txt`:
```
raw sys.argv: ['manual_demo.py', 'summary', '--input', 'sample_data/transactions.csv', '--report', 'out.txt']
```
That's genuinely all Python gives natively - six plain strings, no idea `--input` is a flag. Then what parsing that by hand actually looks like:
```python
argv = sys.argv[1:]
command = argv[0]
input_path = None
report_path = None
i = 1
while i < len(argv):
    if argv[i] == "--input":
        input_path = argv[i + 1]
        i += 2
    elif argv[i] == "--report":
        report_path = argv[i + 1]
        i += 2
    else:
        i += 1
```
Works fine when everything's given correctly, even out of order:
```
--- manual parsing, by hand ---
command: summary
input_path: sample_data/transactions.csv
report_path: out.txt

--- what happens if flags are given in a DIFFERENT order? ---
command: summary
input_path: sample_data/transactions.csv
report_path: out.txt
```
But the moment `--report` is simply forgotten:
```
--- what happens if --report is simply forgotten? ---
command: summary
input_path: sample_data/transactions.csv
report_path: None
```
No error - just silently continues with `None`, a bug waiting to surface somewhere confusing later. Same missing flag through `argparse` instead:
```
usage: cli.py summary [-h] --input INPUT --report REPORT
cli.py summary: error: the following arguments are required: --report
exit code: 2
```
Refuses immediately with a clear message, before anything bad happens - the entire value of `argparse`, for free, just from `required=True`. `Namespace` is just the clean result object it hands back once parsing succeeds, instead of a loose list of strings to keep hunting through.

Q: "Is it necessary all parameters has to be given or set as true? Can't we keep false here for anything?"
A: No, `required=True` isn't mandatory - real proof of an optional argument with a fallback:
```python
parser.add_argument("--input", required=True)
parser.add_argument("--top-n", required=False, default=5, type=int)   # optional, with a fallback
parser.add_argument("--verbose", action="store_true")                  # optional, defaults to False on its own
```
```
call 1 -> Namespace(input='x.csv', top_n=5, verbose=False)
call 2 -> Namespace(input='x.csv', top_n=10, verbose=True)
```
When `--top-n` isn't given, it quietly becomes `5` (whatever `default=` says) instead of erroring; `--verbose` uses `action="store_true"` instead - a flag with no value after it, `False` unless present. For this CLI specifically though, `--input`/`--report`/`filter`'s `--month` are genuinely required on purpose - there's no sensible default input file, output path, or month, so skipping any of them means the command literally can't do its job. Same reasoning as `Transaction.from_row` raising on a missing `category` instead of quietly defaulting it.

Q: "Here we are creating subparsers under each parser, how we will pass the arguments can you show or give example it will help me understand."
A: Real, full demo running all three subcommands for real:
```python
parser = argparse.ArgumentParser(prog="cli.py")
subparsers = parser.add_subparsers(dest="command", required=True)
summary_parser = subparsers.add_parser("summary")
summary_parser.add_argument("--input", required=True)
summary_parser.add_argument("--report", required=True)
by_category_parser = subparsers.add_parser("by-category")
by_category_parser.add_argument("--input", required=True)
by_category_parser.add_argument("--report", required=True)
filter_parser = subparsers.add_parser("filter")
filter_parser.add_argument("--input", required=True)
filter_parser.add_argument("--report", required=True)
filter_parser.add_argument("--month", required=True)
args = parser.parse_args()
print(args)
```
```
--- python cli.py summary --input transactions.csv --report out.txt ---
Namespace(command='summary', input='transactions.csv', report='out.txt')

--- python cli.py by-category --input transactions.csv --report cat.txt ---
Namespace(command='by-category', input='transactions.csv', report='cat.txt')

--- python cli.py filter --input transactions.csv --report sep.txt --month 2026-09 ---
Namespace(command='filter', input='transactions.csv', report='sep.txt', month='2026-09')
```
The first word (`summary`/`by-category`/`filter`) tells `argparse` which subparser handles everything after it; from that point only that subparser's own flags are recognized. Proof a subcommand genuinely can't see another's flags - passing `--month` to `summary`:
```
--- python cli.py summary --input transactions.csv --report out.txt --month 2026-09 ---
usage: cli.py [-h] {summary,by-category,filter} ...
cli.py: error: unrecognized arguments: --month 2026-09
exit code: 2
```
Rejected outright - `summary_parser` was never told `--month` exists.

Q: "Not related to this code but in general, can we just use parsers and not subparsers? Or subparsers are always to be created? If only parsers can be given then give me an example code where only parsers are provided in argparse without subparsers"
A: No, subparsers aren't mandatory - they only exist for a program with multiple distinct verbs needing different flags. A program that only ever does one job is fine with a single flat parser:
```python
import argparse

parser = argparse.ArgumentParser(prog="word_counter.py")
parser.add_argument("--input", required=True)
parser.add_argument("--top-n", required=False, default=5, type=int)

args = parser.parse_args()
print(args)
```
```
--- python word_counter.py --input notes.txt ---
Namespace(input='notes.txt', top_n=5)

--- python word_counter.py --input notes.txt --top-n 10 ---
Namespace(input='notes.txt', top_n=10)
```
No `command`, no `subparsers.add_parser(...)` anywhere - `add_argument(...)` goes directly on the one top-level parser. Rule of thumb: reach for subparsers when a program needs more than one distinct thing with more than one distinct set of flags (like this CLI); skip them when the program only ever does one job.

Q: "Here u are giving summary as arg in 1 and by-category in 2nd and filter in 3rd, so what happens to by-category and filter in 1st, summary, filter in 2nd and so on respectively for the other case."
A: Each of those three demo blocks was a completely separate *run* of the program, not one continuous execution handling all three. `python cli.py summary ...` is the entire program starting fresh, running once, and finishing - there's no leftover session where `by-category`/`filter` are waiting or getting skipped; they simply never got invoked this run, because only one command word was typed. To actually run `by-category`, the script runs *again*, as a brand new, separate execution: `python cli.py by-category --input transactions.csv --report cat.txt`. Each `python`/`python3 ...` line in the demos was its own fresh run from the top - exactly how a CLI tool is used day to day, once per command.

Q: "Also i see Namespace(...) where is that coming from? I never saw namespace in any part of code or traching, or in this code particular, am i missing something? why it is being passed"
A: `Namespace` is a real class living inside the `argparse` module itself, not something written or appearing from nowhere. Real proof:
```python
args = parser.parse_args(['summary', '--input', 'transactions.csv', '--report', 'out.txt'])
print(type(args))
print(isinstance(args, argparse.Namespace))
```
```
type(args): <class 'argparse.Namespace'>
is it an instance of argparse.Namespace? True
```
And it's not magic - buildable by hand, exactly like any class:
```python
ns = argparse.Namespace(x=1, y='hello')
print(ns)        # Namespace(x=1, y='hello')
print(ns.x)       # 1
print(ns.y)       # hello
```
So `parser.parse_args()` internally creates a `Namespace()` object, then for every flag it parsed, does the equivalent of `setattr(that_object, flag_name, value)` - exactly why `args.command`/`args.input`/`args.report` work, ordinary attributes on an ordinary object, same as `self.amount` on a `Transaction`. Never seen before simply because this is the first piece to use `argparse` at all. Printing as `Namespace(command='summary', ...)` is the same `repr()` concept from Piece 3's `!r` discussion - every object type has its own way of displaying itself.

Q: "Can you explain: [the three Namespace outputs from the subparser demo] What we are passsing in each case and what will be taken as input in each case and for each case what will be triggered and how? how passing these values as arguments gets into this ledger.py and calls the respective methods? Will be helpful if explained with code examples and flow diagram"
A: Traced the full pipeline with a preview `main()` - explicitly flagged as a preview run in a scratch copy, not yet in the real file - built and run for real end to end:
```python
def main():
    parser = build_parser()
    args = parser.parse_args()

    ledger = TransactionLedger()
    ledger.load_csv(args.input)

    if args.command == "summary":
        with ReportWriter(args.report, "Transaction Ledger CLI", len(ledger.transactions)) as report:
            report.write_line(f"total income: {ledger.total_income():.2f}")
            report.write_line(f"total expenses: {ledger.total_expenses():.2f}")
            report.write_line(f"net: {ledger.net():.2f}")

    elif args.command == "by-category":
        totals = ledger.by_category()
        with ReportWriter(args.report, "Transaction Ledger CLI", len(ledger.transactions)) as report:
            for category, total in sorted(totals.items(), key=lambda kv: kv[1]):
                report.write_line(f"{category}: {total:.2f}")

    elif args.command == "filter":
        filtered = ledger.filter_by_month(args.month)
        with ReportWriter(args.report, "Transaction Ledger CLI", len(filtered.transactions)) as report:
            report.write_line(f"total income: {filtered.total_income():.2f}")
            report.write_line(f"total expenses: {filtered.total_expenses():.2f}")
            report.write_line(f"net: {filtered.net():.2f}")

    print(f"report written to {args.report}")
```
Run for real against the sample CSV, all three commands, actual report files:
```
=== python cli.py summary --input transactions.csv --report out.txt ===
report written to out.txt
--- out.txt content ---
Transaction Ledger CLI
generated: 2026-09-20T14:19:38

total income: 2500.00
total expenses: -54.20
net: 2445.80

transactions considered: 2
-- end of report --

=== python cli.py by-category --input transactions.csv --report cat.txt ===
report written to cat.txt
--- cat.txt content ---
Transaction Ledger CLI
generated: 2026-09-20T14:19:38

groceries: -54.20
salary: 2500.00

transactions considered: 2
-- end of report --

=== python cli.py filter --input transactions.csv --report sep.txt --month 2026-09 ===
report written to sep.txt
--- sep.txt content ---
Transaction Ledger CLI
generated: 2026-09-20T14:19:38

total income: 2500.00
total expenses: -54.20
net: 2445.80

transactions considered: 2
-- end of report --
```
`sorted(totals.items(), key=lambda kv: kv[1])` sorts `(category, total)` pairs ascending by total - since expenses are negative and income positive, ascending order naturally puts the biggest expense first, matching the spec's "most negative first." The `filter` branch calls `ledger.filter_by_month(args.month)` to get a smaller ledger, then reuses the exact same `total_income()`/`total_expenses()`/`net()` calls as `summary` on that filtered ledger - the payoff from Piece 9 of having written those as reusable methods.

---

## Piece 11: `cli.py` - `main()`, the dispatch logic

The piece that actually wires everything together: load the CSV, look at which subcommand was used, and call the already-built `TransactionLedger`/`ReportWriter` methods accordingly. Added to `cli.py`, below `build_parser()`, plus one new import at the top:

```python
from ledger import TransactionLedger, ReportWriter


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    ledger = TransactionLedger()
    ledger.load_csv(args.input)

    if args.command == "summary":
        with ReportWriter(args.report, "Transaction Ledger CLI", len(ledger.transactions)) as report:
            report.write_line(f"total income: {ledger.total_income():.2f}")
            report.write_line(f"total expenses: {ledger.total_expenses():.2f}")
            report.write_line(f"net: {ledger.net():.2f}")

    elif args.command == "by-category":
        totals = ledger.by_category()
        with ReportWriter(args.report, "Transaction Ledger CLI", len(ledger.transactions)) as report:
            for category, total in sorted(totals.items(), key=lambda kv: kv[1]):
                report.write_line(f"{category}: {total:.2f}")

    elif args.command == "filter":
        filtered = ledger.filter_by_month(args.month)
        with ReportWriter(args.report, "Transaction Ledger CLI", len(filtered.transactions)) as report:
            report.write_line(f"total income: {filtered.total_income():.2f}")
            report.write_line(f"total expenses: {filtered.total_expenses():.2f}")
            report.write_line(f"net: {filtered.net():.2f}")

    print(f"report written to {args.report}")


if __name__ == "__main__":
    main()
```

**Why it looks like this:**

`from ledger import TransactionLedger, ReportWriter` - goes at the top of `cli.py`, alongside `import argparse`. This is the line that actually connects the two files; without it `cli.py` has no idea `TransactionLedger`/`ReportWriter` exist.

`if __name__ == "__main__":` - new pattern for this build. `__name__` is a special variable every Python file automatically has; it equals `"__main__"` specifically when the file is run directly (`python cli.py ...`), but equals the module's own name if the file is ever *imported* by something else instead. The guard means "only actually call `main()` if this file was run directly" - so if `cli.py` is ever imported elsewhere (e.g. by a test file, just to reuse `build_parser()`), it won't accidentally try to run the whole program at import time.

The rest (`if args.command == ...`/`elif ...`) is purely wiring already-verified pieces together - `TransactionLedger.load_csv`/`total_income`/`total_expenses`/`net`/`by_category`/`filter_by_month` from Piece 5-9, `ReportWriter` from Piece 8 - based on which subcommand `args.command` says was used.

**Questions along the way:**

Q: "there is no transactions.csv file, also a question where is this args.command, args.report or other args.?? am not able to understand, when am typing args.rep am not getting suggestion for report or command or others"
A: Two separate things. First, the missing file was a path mix-up, not a real problem - the real CSV genuinely exists, at `sample_data/transactions.csv` inside `cli_tool` (confirmed by pulling it directly), but a couple of the preceding demo messages used a shortened `transactions.csv` path because those ran in a separate scratch folder with the CSV copied directly alongside the script - that shortcut doesn't apply to the real project, where the full path `sample_data/transactions.csv` is needed.

Second, the autocomplete question - genuinely no suggestions, and for a real reason, not a setup problem. Proof:
```python
empty = argparse.Namespace()
print("a brand new, empty Namespace:", empty)
print("does it have a .report attribute yet?", hasattr(empty, "report"))

args = parser.parse_args(["summary", "--input", "x.csv", "--report", "out.txt"])
print("after parse_args():", args)
print("does it have .report NOW?", hasattr(args, "report"))
```
```
a brand new, empty Namespace: Namespace()
does it have a .report attribute yet? False

after parse_args(): Namespace(command='summary', input='x.csv', report='out.txt')
does it have .report NOW? True
args.report: out.txt
```
An empty `Namespace()` genuinely has no `.report` at all - it's `parse_args()` running, at actual runtime, that attaches `.command`/`.input`/`.report` onto it, based on strings (`"--input"`, `"--report"`) passed to `add_argument(...)` calls buried inside `build_parser()`. Contrast with `Transaction`, where autocomplete *does* work for `some_transaction.txn_date`: `self.txn_date = txn_date` sits directly in `__init__`'s source code, so the editor can read it via static analysis (understanding code without running it) and know ahead of time that a `Transaction` will have `.txn_date`. `argparse.Namespace` starts as a deliberately empty container whose attribute names are decided by string values threaded through `argparse`'s own internal code at runtime - editors generally don't trace that deeply through a whole library, so there's no autocomplete safety net for `args.report`/`args.input`/`args.month`/`args.command` the way there is for a class's own declared attributes. Naming rule to remember: whatever's passed to `add_argument("--something", ...)` becomes `args.something` (a dash in the flag name becomes an underscore, e.g. a hypothetical `--top-n` becomes `args.top_n`).

---

## Spec change: no feature branch / PR, direct push to `main`

With the code side of the build done, a deliberate change to the fixed spec: the original plan called for a feature branch pushed and merged into `main` via a real pull request (tied to the branching/remotes/PR docs from the Git series). Decided instead to commit and push directly to `main`, no branch, no PR, for this project.

`cli tool spec.md` updated in three places to match: "Where it lives" no longer mentions a feature branch; the concepts list's "A real branch -> PR" line is now "A real commit and push - to `main` on your actual GitHub repo, not simulated"; and the "Definition of done" checklist's branch/PR line is now "The work is committed and pushed directly to `main` on your GitHub repo." This is a genuine, deliberate change to the spec, not a quiet drift - logged here per the spec's own rule that changes are made together, on purpose.

---

## Piece 12: `tests/test_ledger.py` - `Transaction` tests

First pytest piece, and the last required concept for the spec. pytest works by convention, not registration: any file named `test_*.py` gets scanned, and inside it any function named `test_*` is treated as one test - no special import needed to "register" a test, no wrapping in a class, just plain `assert` statements. Demonstrated for real first with a throwaway `add()` function - one passing test, one deliberately failing:
```
test_demo.py::test_add_passes PASSED                                     [ 50%]
test_demo.py::test_add_fails_on_purpose FAILED                           [100%]

=================================== FAILURES ===================================
__________________________ test_add_fails_on_purpose ___________________________

    def test_add_fails_on_purpose():
>       assert add(2, 3) == 6
E       assert 5 == 6
E        +  where 5 = add(2, 3)
```
pytest shows both sides of a failed comparison automatically (`assert 5 == 6`, `where 5 = add(2, 3)`), not just "assertion failed."

For the spec's `InvalidTransactionError` tests specifically, checking that code *raises* needs `pytest.raises(...)` instead of a plain `assert` (there's nothing left to compare once code has already crashed) - demonstrated with a throwaway `risky()` function before touching real code.

Also verified for real, since `tests/test_ledger.py` needs to import from `ledger.py` one folder up: running `python -m pytest` from inside `cli_tool` works (`python -m` adds the current folder to Python's import path), but running the bare `pytest` command failed with `ModuleNotFoundError: No module named 'ledger'` - so tests must be run as `python -m pytest` / `python3 -m pytest` from inside `cli_tool`, not just `pytest`.

Code to type, a new file `tests/test_ledger.py`:

```python
import pytest

from ledger import Transaction, InvalidTransactionError


def test_transaction_from_row_valid():
    row = {"date": "2026-09-01", "category": "groceries", "description": "Big Bazaar", "amount": "-54.20"}
    txn = Transaction.from_row(1, row)
    assert txn.category == "groceries"
    assert txn.amount == -54.20
    assert txn.description == "Big Bazaar"
    assert str(txn.txn_date) == "2026-09-01"


def test_transaction_from_row_bad_date():
    row = {"date": "01-09-2026", "category": "groceries", "description": "", "amount": "-10"}
    with pytest.raises(InvalidTransactionError):
        Transaction.from_row(1, row)


def test_transaction_from_row_empty_category():
    row = {"date": "2026-09-01", "category": "   ", "description": "", "amount": "-10"}
    with pytest.raises(InvalidTransactionError):
        Transaction.from_row(1, row)


def test_transaction_from_row_bad_amount():
    row = {"date": "2026-09-01", "category": "groceries", "description": "", "amount": "abc"}
    with pytest.raises(InvalidTransactionError):
        Transaction.from_row(1, row)
```

**Why it looks like this:**

`import pytest` then `from ledger import Transaction, InvalidTransactionError` - pulls in pytest itself plus the two real pieces being tested.

`test_transaction_from_row_valid` - builds a `row` dict shaped exactly like what `csv.DictReader` hands `from_row` (same structure from Piece 6's diagram), calls `Transaction.from_row(1, row)` directly - no CSV file, no `TransactionLedger`, just the one method in isolation - and asserts each field landed correctly.

The three bad-row tests each build a `row` with exactly one thing wrong (bad date shape, whitespace-only category, non-numeric amount) and wrap the call in `with pytest.raises(InvalidTransactionError):` - the direct pytest equivalent of the real `AttributeError`/`ValueError` demos already proven by hand back in Piece 3, now captured as a permanent, automatically-runnable check instead of a one-off terminal experiment.

**Questions along the way:**

Q: "You mentioned: `for category, total in sorted(totals.items(), key=lambda kv: kv[1]):` what is the lambda function here, am not able to understand"
A: `lambda x: x ** 2` is a tiny, unnamed function written inline - genuinely identical to a normal `def`. Real proof both give the same result:
```python
square = lambda x: x ** 2
def square_normal(x): return x ** 2
```
```
square(5): 25
square_normal(5): 25
```
No `return` keyword needed - the expression after `:` is automatically what gets returned. Applied to the real code: `totals.items()` gives `(category, amount)` tuples:
```
totals.items(): [('groceries', -54.2), ('salary', 2500.0), ('rent', -800.0)]
```
`sorted()` needs to know *what* to compare - `key=` tells it "run this function on each item first, sort by that result instead." `lambda kv: kv[1]` means "given one `(category, amount)` tuple, give back just the amount." Real proof of what `kv` actually is each time:
```
kv: ('groceries', -54.2)   kv[0] (category): groceries   kv[1] (amount): -54.2
kv: ('salary', 2500.0)   kv[0] (category): salary   kv[1] (amount): 2500.0
kv: ('rent', -800.0)   kv[0] (category): rent   kv[1] (amount): -800.0
```
So `sorted()` sorts the pairs by amount, ascending:
```
sorted by kv[1] (the amount): [('rent', -800.0), ('groceries', -54.2), ('salary', 2500.0)]
```
`rent` (most negative) comes first - matching the spec's "most negative first." `lambda` was used here (instead of a separate named `def`) purely because it's small and used in exactly one place.

Q: "with pytest.raises(InvalidTransactionError): not able to understand this. What is being done here? Can we raise exceptions from context managers? Is with being used as context manager here?"
A: Yes - `pytest.raises(...)` genuinely is a context manager, using the exact same `with` mechanism as `ReportWriter`/`open()`, but its `__exit__` does something deliberately unusual with whatever exception it receives. Three real scenarios run to prove it:
```python
def test_expected_exception_raised():
    with pytest.raises(InvalidTransactionError):
        raises_it()             # raises InvalidTransactionError

def test_nothing_raised_at_all():
    with pytest.raises(InvalidTransactionError):
        does_not_raise()        # just returns 42, no exception

def test_wrong_exception_type_raised():
    with pytest.raises(InvalidTransactionError):
        raises_wrong_thing()    # raises ValueError instead
```
```
tests::test_expected_exception_raised PASSED
tests::test_nothing_raised_at_all FAILED
  Failed: DID NOT RAISE <class '...InvalidTransactionError'>
tests::test_wrong_exception_type_raised FAILED
  ValueError: not the right kind of error
```
Scenario 1: the exception happened, `__exit__` received it, saw it matched, and swallowed it - the test finishes normally, counted as a pass. Scenario 2 (the actual answer to "can we raise exceptions from context managers?" - yes, real proof of it): nothing was raised inside the block, so `__exit__` itself raised a brand-new exception (pytest's own `Failed`) to fail the test - a context manager's `__exit__` isn't limited to quietly cleaning up, it can raise its own exception when what it expected didn't happen. Scenario 3: the real `ValueError` propagates straight through uncaught, failing the test with that actual error - `__exit__` only swallows the *specific* exception type it was told to expect, same as `ReportWriter.__exit__`'s `return False` lets everything else through after cleanup.

---

## Piece 13: `TransactionLedger` summarizing tests

Tests `total_income`, `total_expenses`, `net`, `by_category`, and `filter_by_month` - the methods that operate across a *list* of transactions, not the single-row parsing tested in Piece 12. These are built and tested directly against hand-built `Transaction` objects, deliberately bypassing `load_csv` entirely, so a failure here can only mean the summarizing math is wrong - not that CSV parsing broke.

```python
import pytest
from datetime import date

from ledger import Transaction, InvalidTransactionError, TransactionLedger
```

```python
def test_ledger_totals_and_category_breakdown():
    """ total_income, total_expenses, net, and by_category are correct for a known set of transactions """
    ledger = TransactionLedger()
    ledger.transactions = [
        Transaction(date(2026, 9, 1), 'groceries', 'Big Bazaar', -54.20),
        Transaction(date(2026, 9, 3), 'salary', 'September salary', 2500.00),
        Transaction(date(2026, 9, 5), 'rent', 'September rent', -800.00),
        Transaction(date(2026, 10, 1), 'groceries', 'October shop', -30.00),
    ]

    assert ledger.total_income() == 2500.00
    assert ledger.total_expenses() == -884.20
    assert ledger.net() == 1615.80
    assert ledger.by_category() == {
        'groceries': -84.20,
        'salary': 2500.00,
        'rent': -800.00,
    }


def test_ledger_filter_by_month():
    """ Filter_by_month returns only the transactions from the given month, unchanged otherwise """
    ledger = TransactionLedger()
    ledger.transactions = [
        Transaction(date(2026, 9, 1), 'groceries', 'Big Bazaar', -54.20),
        Transaction(date(2026, 9, 3), 'salary', 'September salary', 2500.00),
        Transaction(date(2026, 10, 1), 'groceries', 'October shop', -30.00),
    ]

    september = ledger.filter_by_month('2026-09')

    assert len(september.transactions) == 2
    assert all(t.txn_date.strftime('%Y-%m') == '2026-09' for t in september.transactions)
```

**Why it looks like this:**

`from datetime import date` and `TransactionLedger` are both new imports this piece - Piece 12 only needed `Transaction` and `InvalidTransactionError`, but building `Transaction` objects by hand (instead of via `from_row`) means passing a real `date` object directly, and testing ledger-level methods means importing `TransactionLedger` itself.

`test_ledger_totals_and_category_breakdown` builds a `TransactionLedger`, assigns a known list of four transactions straight to `ledger.transactions` (skipping `load_csv` on purpose), and asserts each summarizing method against numbers worked out by hand ahead of time: total income (the one positive amount, `2500.00`), total expenses (the three negative amounts summed, `-884.20`), net (income + expenses, `1615.80`), and the per-category breakdown (`groceries` appears twice, across two different months, and its two amounts get summed into one total).

`test_ledger_filter_by_month` builds a smaller list spanning two different months, calls `filter_by_month('2026-09')`, and checks two things: the right *count* came back (2, not 3), and every transaction that came back genuinely belongs to that month.

Real proof this behaves as expected, run before either test was typed:
```
total_income: 2500.0
total_expenses: -884.2
net: 1615.8
by_category: {'groceries': -84.2, 'salary': 2500.0, 'rent': -800.0}
filter_by_month 2026-09 descriptions: ['Big Bazaar', 'September salary', 'September rent']
```

---

## Piece 14: `ReportWriter` footer test - `tmp_path` and nested context managers

The last test required by the spec: proving `ReportWriter`'s footer is written even when the body-writing step raises. This needs `tmp_path` - a built-in pytest fixture: naming it as a parameter is enough for pytest to hand the test a fresh, empty, automatically-cleaned-up temporary directory, no manual setup/teardown needed. Demonstrated standalone first:

```python
def test_shows_tmp_path(tmp_path):
    print('tmp_path is:', tmp_path)
    file = tmp_path / 'hello.txt'
    file.write_text('hi')
    print('file exists after write:', file.exists())
    print('file contents:', file.read_text())
```
```
tmp_path is: /.../pytest-0/test_shows_tmp_path0
file exists after write: True
file contents: hi
```
`tmp_path` is a real `pathlib.Path` object; `/` here is `Path`'s own path-joining operator, not division, and `.write_text()`/`.read_text()` are `Path` shortcuts for open-write-close/open-read-close.

Then a real demo of `ReportWriter` itself surviving a crash, run before the test was typed:
```
exception propagated out of the with block: something went wrong mid-body

--- file contents after the crash ---
demo report
generated: 2026-09-20T15:43:28

some body line

transactions considered 3
-- end of report --
```

Code to type, at the bottom of `tests/test_ledger.py`. Import line updated:

```python
from ledger import Transaction, InvalidTransactionError, TransactionLedger, ReportWriter
```

New test:

```python
def test_report_writer_footer_written_even_if_body_raises(tmp_path):
    """ ReportWriter's footer is written even when the body-writing step raises """
    report_path = tmp_path/'report.txt'

    with pytest.raises(ValueError):
        with ReportWriter(str(report_path), 'demo report', 3) as report:
            report.write_line('some body line')
            raise ValueError('something went wrong mid-body')

    contents = report_path.read_text()
    assert 'transactions considered 3' in contents
    assert '-- end of report --' in contents
```

**Why it looks like this:**

`with pytest.raises(ValueError):` wrapping `with ReportWriter(...) as report:` - two context managers, nested. The outer one is expecting an exception to happen; the inner one is the actual thing under test - the real reason this test can prove the footer guarantee at all. `str(report_path)` because `ReportWriter.__init__` calls `open(self.path, 'w')`, which needs a string/path-like - `open()` genuinely accepts a `Path` directly too, but `str()` here is explicit and matches how `cli.py` calls it with a plain string.

**Questions along the way:**

Q: "Explain please, Inside with we are adding another with, please explain the mechanism, flow with a flow diagram and the working of this code."
A: Two context managers stacked - the inner one (`ReportWriter`) always gets first crack when an exception fires inside it, the outer one (`pytest.raises`) gets the next crack. Demonstrated with two stand-in classes mirroring the real shapes, each printing on enter/exit:
```
--- starting ---
[Outer.__enter__] getting ready to expect an exception
  [Inner.__enter__] opening file, writing header
  [Inner.write_line] writing: some body line
  about to raise ValueError
  [Inner.__exit__] received exc_type=<class 'ValueError'>
  [Inner.__exit__] writing footer anyway, closing file
[Outer.__exit__] received exc_type=<class 'ValueError'>
[Outer.__exit__] this IS the expected type -> swallowing it, returning True
--- after the outer with block, execution continues normally ---
```
Flow: `raise ValueError` fires inside the innermost block → Python calls the *nearest* enclosing context manager's `__exit__` first (`ReportWriter.__exit__`, which writes the footer, closes the file, and returns `False` - "not handled, keep propagating") → the exception then reaches the next enclosing context manager's `__exit__` (`pytest.raises`' real `__exit__`, which checks whether the exception type matches what it expected, and returns `True` - "handled, stop here") → because it returned `True`, execution resumes normally right after the outer `with` block, which is why `report_path.read_text()` and the two `assert`s run fine with no exception surfacing as a test failure. If `ReportWriter.__exit__` had returned `True` instead, the exception would be swallowed one layer too early and `pytest.raises` would never see it - the test would fail with `Failed: DID NOT RAISE`, same as Piece 12's second demo scenario.

---

## Running the tool and tests

Q: "okay, but the question is how to run this? what commands to give for checking this application etc"
A: Two separate things get run, both from inside `cli_tool` (`D:\interview prep\python\project\cli_tool`).

Running the tests (checks the code is still correct):
```
python -m pytest tests/test_ledger.py -v
```
`python -m pytest` specifically, not bare `pytest` (Piece 12's import-path requirement); `-v` is optional, shows each test name individually rather than just a pass/fail count.

Running the tool itself:
```
python cli.py <command> --input <path to csv> --report <path to output file> [--month YYYY-MM]
```
Real examples against the actual sample data:
```
python cli.py summary --input sample_data/transactions.csv --report out_summary.txt
python cli.py by-category --input sample_data/transactions.csv --report out_category.txt
python cli.py filter --input sample_data/transactions.csv --report out_filter.txt --month 2026-09
```
`--month` only exists on `filter` - the other two reject it (Piece 10's subparser behavior). On screen: `load_csv`'s logging lines (`WARNING` per skipped row, then an `INFO` summary), then `report written to <path>` - the actual report content lands in the `--report` file, not on screen.

**Decided: both.** A `reports/` folder now exists in `cli_tool` as the conventional place to point `--report` at (e.g. `--report reports/summary.txt`), and the README's example command uses it - but `--report` is just an ordinary argument, so it still accepts any path, including straight into `cli_tool` if that's ever wanted for a one-off check.

Q: "Give example of commands using both report folder and cli, or folder path outside report, then what about the Namespace command, earlier you gave passing Namespace, when asked how to give the commands but you are not passing now"
A: Two real commands run to show both, plus the `Namespace` each one actually produces underneath:
```
python cli.py summary --input sample_data/transactions.csv --report reports/summary.txt
```
Namespace: `Namespace(command='summary', input='sample_data/transactions.csv', report='reports/summary.txt')`
```
python cli.py by-category --input sample_data/transactions.csv --report category_check.txt
```
Namespace: `Namespace(command='by-category', input='sample_data/transactions.csv', report='category_check.txt')`

On why the `Namespace` wasn't shown alongside every command example since Piece 10: every command line genuinely does go through `build_parser().parse_args()` first, turning `--report reports/summary.txt` into `args.report = 'reports/summary.txt'` - that conversion happens invisibly every time `main()` runs, and the terminal itself never displays the `Namespace`, only `cli.py`'s own `print(f'report written to {args.report}')` does. It wasn't repeated in later examples only because Piece 10 already established that step happens every time; shown again here specifically to make that connection explicit again.

---

## `README.md`

The last file the spec requires: what the tool does, how to run it, one real example command and its output. Documentation, not logic - so it went straight in rather than being typed line-by-line the way the code pieces were, at the user's request.

```markdown
# Transaction Ledger CLI

A command-line tool that reads a CSV of bank-style transactions and produces spending reports from it.

## Commands

- `summary` - total income, total expenses, and net across every loaded transaction.
- `by-category` - the same totals, broken down per category, sorted by total spent (most negative first).
- `filter --month YYYY-MM` - same as summary, but restricted to transactions in a given month.

Each command reads a CSV, validates every row (skipping and logging any row with a bad date, bad amount, or empty category), and writes the result to a report file.

## How to run it

Run from inside this folder:

​```
python -m pytest tests/test_ledger.py -v
python cli.py <command> --input <csv path> --report <output path> [--month YYYY-MM]
​```

`--report` can point anywhere, including the `reports/` folder in this project.

## Example

​```
python cli.py summary --input sample_data/transactions.csv --report reports/summary.txt
​```

Terminal output:
​```
WARNING: row 3: invalid date: '01-09-2026'
WARNING: row 4: catgory is empty
WARNING: row 5: invalid amount: 'abc'
INFO: loaded 2 transactions, skipped 3
INFO: load_csv took 0.0284sec
report written to reports/summary.txt
​```

`reports/summary.txt`:
​```
Transaction Ledger CLI
generated: 2026-09-20T16:18:07

total income: 2500.00
total expenses: -54.20
net: 2445.80

transactions considered 2
-- end of report --
​```
```

Created directly at `cli_tool/README.md` and verified against the real file on disk - matches exactly. Only item left per the spec: a real commit and push directly to `main`.

---
