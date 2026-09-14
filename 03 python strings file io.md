# Topic 3 — Strings & File I/O

*Phase 1, Beginner group — item 3 of 4. Same drill as always: type the examples, then do the practice questions before checking this off.*

---

## 1. Strings are immutable (this drives everything below)

You already know this from the mutable/immutable discussion — worth restating here because it explains *why* string methods work the way they do:

```python
s = "hello"
s.upper()          # returns "HELLO" — a NEW string
print(s)           # still "hello" — s itself never changed

s = s.upper()      # THIS is how you actually keep the change — reassign
```

**Every string method returns a new string. None of them modify the original.** This trips people up constantly when they write `s.strip()` on its own line and wonder why `s` still has whitespace.

### Running this for real, with proof a new object was created

**Real, verified output**, extending the snippet with `id()` so "a NEW string" isn't just an assertion:

```python
s = "hello"
r = s.upper()
print(r)
print(s)
print("id(s) before:", id(s))
s = s.upper()
print(s)
print("id(s) after:", id(s))
```

```
HELLO
hello
id(s) before: 139975666388656
HELLO
id(s) after: 139975664332912
```

**Flow diagram:**

```
s = "hello"
    ┌─────────┐
    │ "hello" │
    └─────────┘
        ▲
       [s]

r = s.upper()
    s.upper() builds a BRAND NEW string object "HELLO" and returns it.
    s itself is never touched — strings have no "modify in place" method
    at all, unlike list.append() or dict's [] assignment.

    ┌─────────┐      ┌─────────┐
    │ "hello" │      │ "HELLO" │   ← a second, separate object
    └─────────┘      └─────────┘
        ▲                 ▲
       [s]               [r]

s = s.upper()
    s.upper() runs AGAIN, building yet ANOTHER new "HELLO" string
    (a third object — note id(s) really did change between the two
    prints above, confirming this isn't the same object as r's).
    The "=" then REBINDS the name s to point at this new object.

    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │ "hello" │      │ "HELLO" │      │ "HELLO" │   ← now unreferenced
    └─────────┘      └─────────┘      └─────────┘      by anyone but r
        (orphaned)        ▲                 ▲
                          [r]               [s]
```

This is the exact same "name bound to an object, not a box you write into" model from the fundamentals doc — the only thing specific to strings is that *every single string method*, without exception, follows this pattern, because there is no mutating alternative. Contrast this directly with `list.append()`, which changes the existing object in place and returns `None` — strings and lists sit on opposite sides of the mutable/immutable line, and it shows up in exactly this kind of return-value behavior.

## 2. Indexing & slicing — same rules as lists, but read-only

```python
s = "hello world"
s[0]        # "h"
s[-1]       # "d"
s[0:5]      # "hello"
s[6:]       # "world"
s[::-1]     # "dlrow olleh" — reversed, the classic trick

s[0] = "H"  # TypeError — can't assign to a string index, it's immutable
```

### Running this for real, including the error

**Real, verified output:**

```python
s = "hello world"
print(s[0])
print(s[-1])
print(s[0:5])
print(s[6:])
print(s[::-1])
try:
    s[0] = "H"
except TypeError as e:
    print("TypeError:", e)
```

```
h
d
hello
world
dlrow olleh
TypeError: 'str' object does not support item assignment
```

**Why `s[0] = "H"` fails, mechanically, vs. why `nums[0] = 999` would succeed on a list:** indexing syntax (`obj[i] = value`) is Python's sugar for calling a special method, `__setitem__`, on the object. `list` implements `__setitem__` — it reaches into its internal array and overwrites the pointer at that position. `str` simply does not implement `__setitem__` at all (the same category of missing-method error as `frozenset.add()` from the collections doc) — because a string's characters are packed into one fixed, immutable block of memory when it's created; there is no "slot" designed to be overwritten later. The only way to get a "modified" string is what §1 already showed: build an entirely new one. The slicing rules themselves (`s[0:5]`, `s[::-1]`) are identical, mechanically, to the list slicing you already learned in Topic 2 — same fencepost model, same `stop`-is-exclusive rule — the only difference is that a string slice always hands back a new *string* instead of a new *list*.

## 3. The methods you'll actually use

```python
s = "  Hello, World!  "

s.strip()              # "Hello, World!"        — removes leading/trailing whitespace
s.lower()               # "  hello, world!  "
s.upper()               # "  HELLO, WORLD!  "
s.replace(",", ";")     # "  Hello; World!  "    — replaces ALL occurrences
s.split(",")            # ["  Hello", " World!  "]   — splits into a list
s.split()               # splits on ANY whitespace, collapses multiples — very common for cleaning

",".join(["a", "b", "c"])   # "a,b,c" — the REVERSE of split; joins a list into one string

s.startswith("  He")    # True
s.endswith("!  ")       # True
s.find("World")         # 9 — index where it starts, or -1 if not found
s.index("World")        # 9 — same, but raises ValueError if not found (find is safer for "maybe not there")

"42".isdigit()          # True
"abc".isalpha()         # True
"abc123".isalnum()      # True
"".isdigit()            # False — empty string is not digits
```

### Running every one of these for real

**Real, verified output**, running the whole block above through `print()` (with `repr()` on the ones where leading/trailing spaces would otherwise be invisible):

```
'Hello, World!'
'  hello, world!  '
'  HELLO, WORLD!  '
'  Hello; World!  '
['  Hello', ' World!  ']
['Hello,', 'World!']
a,b,c
True
True
9
9
True
True
True
False
```

Every value matches the inline comments exactly — confirmed. Two worth tracing more deeply:

**`s.split(",")` vs `s.split()` — why the outputs differ so much even though it's "the same method":**

```
s = "  Hello, World!  "

s.split(",")   → splits on EXACTLY the character ",", nowhere else.
                 The leading/trailing whitespace around each piece is
                 left completely alone, because whitespace was never
                 the delimiter here.
                 Result: ['  Hello', ' World!  ']
                            ▲              ▲
                       leading spaces   trailing spaces
                       still attached   still attached

s.split()      → with NO argument, split() switches to a special mode:
                 split on ANY run of whitespace (spaces, tabs, newlines),
                 and — critically — silently DISCARD leading/trailing
                 whitespace and collapse multiple consecutive spaces
                 into one delimiter instead of producing empty strings
                 between them.
                 Result: ['Hello,', 'World!']
                            ▲ note: the comma stayed attached to "Hello,"
                              because "," was never a delimiter in THIS
                              call — only whitespace was.
```

This no-argument mode is why `s.split()` is the go-to for "clean up messy user input" — it absorbs tabs, multiple spaces, and leading/trailing whitespace all at once, which is exactly the kind of real-world messiness raw text tends to have.

**`.find()` vs `.index()` — same lookup, different failure behavior, tied directly to the EAFP/LBYL and exceptions material from Topic 1's neighbor doc:**

```
s.find("World")    →  9  (the starting index where "World" begins)
                       if NOT found: returns -1  (a normal value,
                       no exception — you're expected to check it)

s.index("World")   →  9  (identical result when found)
                       if NOT found: raises ValueError immediately
                       (an exception — same "loud failure" philosophy
                       as dict[key] vs dict.get(key) from Topic 2)
```

Use `.find()` when "not present" is a normal, expected outcome you'll branch on (`if s.find(x) == -1: ...`); use `.index()` when you're confident the substring *should* be there and its absence would itself indicate a bug worth crashing loudly on — exactly the same design tradeoff as `dict[key]` (loud) vs `dict.get(key)` (quiet default) from the collections doc.

### Formatting — f-strings are what you should default to

```python
name = "Ani"
amount = 1234.5

f"Hello, {name}! Total: {amount}"          # "Hello, Ani! Total: 1234.5"
f"Total: {amount:.2f}"                      # "Total: 1234.50"  — 2 decimal places
f"Total: {amount:,.2f}"                     # "Total: 1,234.50" — thousands separator too
f"{name!r}"                                  # "'Ani'" — repr instead of str (quotes shown)
```

You'll see two older styles in existing codebases — recognize them, but write f-strings in your own code:

```python
"Hello, {}!".format(name)     # .format() — older, still common
"Hello, %s!" % name           # %-formatting — oldest, mostly legacy code
```

### Running every formatting style for real

**Real, verified output:**

```python
name = "Ani"
amount = 1234.5
print(f"Hello, {name}! Total: {amount}")
print(f"Total: {amount:.2f}")
print(f"Total: {amount:,.2f}")
print(f"{name!r}")
print("Hello, {}!".format(name))
print("Hello, %s!" % name)
```

```
Hello, Ani! Total: 1234.5
Total: 1234.50
Total: 1,234.50
'Ani'
Hello, Ani!
Hello, Ani!
```

**What's actually happening inside an f-string, mechanically.** An f-string is not just a nicer-looking `.format()` — it's evaluated by the Python interpreter *at the point the string literal is created*, which means anything inside `{}` is a real, live Python expression, not just a variable name slot. `f"Total: {amount:.2f}"` breaks down as: evaluate the expression `amount` (giving `1234.5`), then apply the **format spec** after the colon — `.2f` means "format as a fixed-point number (`f`), rounded to 2 decimal places (`.2`)." `,.2f` adds a `,` flag before that, which additionally inserts thousands separators. `!r` is a *conversion*, not a format spec — it tells Python to call `repr(name)` instead of `str(name)` before inserting it, which is why `f"{name!r}"` shows the quotes (`'Ani'`) that a plain `f"{name}"` (`Ani`, no quotes) would not — the exact same `repr()` vs `str()` distinction you saw with `!r` back in the decorators doc's logging example.

### Why string concatenation in a loop is a real performance bug

```python
# BAD — O(n²) — don't do this for large n
result = ""
for word in words:
    result += word + " "

# GOOD — O(n)
result = " ".join(words)
```

Because strings are immutable, `result += word` doesn't extend `result` in place — it builds an **entirely new string** every single iteration, copying everything that came before. Do that `n` times and you've copied roughly `1 + 2 + 3 + ... + n` characters total, which is O(n²). `"".join(list_of_strings)` does it in one pass, O(n), because it knows the total size upfront and allocates once. This is a genuinely common thing to get asked to spot in a code review question.

### Proving the O(n²) claim with a real measurement

Same spirit as the list-vs-set timing measurement in the collections doc — here it is with an actually-measured gap, joining 20,000 words, 5 times each:

```python
import timeit

words = ["word"] * 20000

def bad():
    result = ""
    for word in words:
        result += word + " "
    return result

def good():
    return " ".join(words) + " "

assert bad() == good()

t_bad = timeit.timeit(bad, number=5)
t_good = timeit.timeit(good, number=5)
print(f"result += (5 runs, 20000 words each): {t_bad:.4f}s")
print(f'" ".join (5 runs, 20000 words each): {t_good:.4f}s')
```

**Real, verified output:**

```
result += (5 runs, 20000 words each): 0.0124s
" ".join (5 runs, 20000 words each): 0.0013s
```

Roughly 10x slower here at 20,000 words — and critically, that gap *widens* as the input grows, because O(n²) grows quadratically while O(n) grows linearly. At 200,000 words the gap would be closer to 100x, not 10x. This is the concrete evidence behind the "genuinely common thing to get asked to spot" claim above.

**Flow diagram — why `result += word + " "` is secretly O(n²), copy by copy:**

```
Iteration 1: result = "" + "word " = "word "                    (copies 5 chars)
Iteration 2: result = "word " + "word " = "word word "          (copies 10 chars)
Iteration 3: result = "word word " + "word " = "...word "       (copies 15 chars)
...
Iteration n: copies roughly 5*n chars

Total characters copied across the whole loop:
    5 + 10 + 15 + ... + 5n   =   5 * (1 + 2 + 3 + ... + n)   =   5 * n(n+1)/2

That's proportional to n², because EVERY iteration re-copies ALL the
characters accumulated so far, not just the new word being added —
each += silently discards the old string object and builds a
brand-new one containing the old content PLUS the new piece.

" ".join(words), by contrast, walks the list ONCE, adds up the total
length needed, allocates ONE block of memory of exactly that size,
and copies each word into its final position exactly once — total
work proportional to n, not n².
```

## 4. File I/O

### Always use `with` (a context manager — you met these in Topic 1)

```python
with open("data.txt", "r") as f:
    content = f.read()         # whole file as one string
# file is automatically closed here, even if an exception happened inside the block
```

Without `with`, you'd need `f = open(...)` then remember to call `f.close()` yourself — and if an exception happens in between, `close()` never runs and the file handle leaks. `with` guarantees cleanup no matter what. This is the single most common file-handling mistake interviewers look for: code that opens a file without `with` or without a `try/finally`.

### Modes

| Mode | Meaning |
|---|---|
| `"r"` | read (default) — errors if file doesn't exist |
| `"w"` | write — **overwrites/truncates** the whole file if it exists, creates it if not |
| `"a"` | append — adds to the end, creates the file if not |
| `"r+"` | read and write, file must exist |
| `"rb"` / `"wb"` | binary mode — for non-text files |

### Reading — three ways, pick based on file size

```python
with open("data.txt") as f:
    content = f.read()          # entire file as one string — fine for small files

with open("data.txt") as f:
    lines = f.readlines()       # list of lines, each with its trailing \n

with open("data.txt") as f:
    for line in f:               # iterate line by line — memory-efficient for BIG files
        print(line.strip())      # strip() removes the trailing \n
```

The line-by-line loop is the one to prefer for large files — it doesn't load the whole file into memory at once, which matters a lot once you're doing ETL work on real-sized data in Phase 4.

### Running the three reading styles for real, against an actual file

A real 3-line file was written to disk first (`data.txt`, containing `"line one\nline two\nline three\n"`), then each of the three reading styles above was run against it:

```python
with open("data.txt", "r") as f:
    content = f.read()
print(repr(content))

with open("data.txt") as f:
    lines = f.readlines()
print(lines)

with open("data.txt") as f:
    for line in f:
        print(repr(line.strip()))
```

**Real, verified output:**

```
'line one\nline two\nline three\n'
['line one\n', 'line two\n', 'line three\n']
'line one'
'line two'
'line three'
```

**Flow diagram — what each reading style actually returns, and why the `\n` characters behave the way they do:**

```
File on disk (data.txt), as bytes/characters:
    l i n e   o n e \n l i n e   t w o \n l i n e   t h r e e \n

f.read()
    → reads the ENTIRE remaining file as ONE string, newlines and all,
      exactly as stored on disk. Nothing is split, nothing is removed.

f.readlines()
    → reads the entire file too, but splits it into a LIST of strings,
      one per line — cutting at each \n, but KEEPING the \n on the end
      of every line except possibly the last. This is why every string
      in the list above still ends in '\n' — readlines() doesn't strip
      it for you.

for line in f: ...
    → iterates the file object directly, one line at a time, WITHOUT
      ever holding the whole file in memory at once (unlike read() and
      readlines(), both of which load everything up front). Each `line`
      still carries its trailing \n, same as readlines() — which is
      exactly why the loop calls .strip() on it before printing, to
      drop that trailing newline for clean output.
```

The "memory-efficient for big files" claim is the mechanical reason this loop form is preferred at scale: `f.read()` and `f.readlines()` both require enough RAM to hold the entire file's contents (or every line of it) simultaneously; `for line in f` reads and yields one line at a time from disk, so a 50 GB log file can be processed with only a few bytes of memory in play at any given moment — this is the file-I/O analog of the generator-vs-list memory tradeoff from the comprehensions/generators doc.

### Writing

```python
with open("output.txt", "w") as f:
    f.write("line one\n")
    f.write("line two\n")

with open("output.txt", "a") as f:
    f.write("appended line\n")     # adds without erasing what's there
```

### Running the writing example for real, checking the file's actual contents after each step

```python
with open("output.txt", "w") as f:
    f.write("line one\n")
    f.write("line two\n")

with open("output.txt") as f:
    print(repr(f.read()))

with open("output.txt", "a") as f:
    f.write("appended line\n")

with open("output.txt") as f:
    print(repr(f.read()))
```

**Real, verified output:**

```
'line one\nline two\n'
'line one\nline two\nappended line\n'
```

**Why `"w"` mode didn't need you to manually clear the file first, and why `"a"` mode didn't erase what was already there — traced against the mode table above:** opening a file in `"w"` mode immediately **truncates** it the instant `open()` runs — before a single `.write()` call happens — so the file starts life as empty, ready to be written into from scratch; that's why the first `print(repr(f.read()))` shows only `"line one\nline two\n"`, with no trace of anything that might have existed in `output.txt` before this script ran. `"a"` mode, by contrast, opens the file with its write position already parked at the *end* of the existing content, rather than truncating — so `f.write("appended line\n")` is physically added after everything already there, which is exactly why the second read shows both the original two lines *and* the appended one, in that order. Note also that a fresh `with open("output.txt")` (default `"r"` mode) was needed to read the file back after writing — the same file handle that was just used for writing isn't automatically rewound to the beginning for you.

### Handling a missing file properly (ties back to Topic 1's exceptions)

```python
try:
    with open("maybe_missing.txt") as f:
        content = f.read()
except FileNotFoundError:
    content = ""
    print("File not found — using empty default")
```

### Running this for real, against a file that genuinely does not exist

**Real, verified output**, run in a directory with no `maybe_missing.txt` present:

```
File not found — using empty default
```

(and `content` correctly ends up as `''`, verified by printing `repr(content)` afterward).

**Flow trace — why this is safe, tied directly to the exceptions doc's `try`/`except` mechanics:** `open("maybe_missing.txt")` is the line that actually raises `FileNotFoundError` — the file genuinely doesn't exist on disk, so the OS-level open call fails immediately, before the `with` block's body (`content = f.read()`) ever gets a chance to run at all. Because this `open()` call sits inside a `try`, the exception is caught by `except FileNotFoundError` instead of crashing the program, and execution jumps straight into that handler — setting `content = ""` and printing the friendly message. This is a direct, practical application of the EAFP philosophy from the exceptions doc: rather than checking `Path("maybe_missing.txt").exists()` first (LBYL) and then opening it, the code just *tries* to open it and handles the failure if it happens — fewer moving parts, and immune to a rare race condition where the file could vanish between a check and the actual open.

### The `csv` module — before you ever touch pandas

You'll use pandas for real CSV work starting Phase 4, but you should be able to parse a CSV by hand too — it's a fair interview question, and it's what pandas is doing for you under the hood:

```python
import csv

with open("transactions.csv") as f:
    reader = csv.DictReader(f)     # each row becomes a dict, using the header row as keys
    for row in reader:
        print(row["category"], row["amount"])   # note: values come in as STRINGS, even numbers
```

`csv.DictReader` handles the annoying edge cases yourself-rolled parsing gets wrong — commas inside quoted fields, different line endings — so prefer it over manually calling `.split(",")` on each line once you're dealing with real CSV files. Note that every value comes back as a string, even something that looks like a number — you have to `int()`/`float()` it yourself if you need to do math with it.

### Running this for real, against an actual CSV file on disk

A real `transactions.csv` was written first (header `category,amount`, then two data rows), then read back with `DictReader`:

```python
import csv

with open("transactions.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row, "-- amount type:", type(row["amount"]))
        print(row["category"], row["amount"])
```

**Real, verified output:**

```
{'category': 'food', 'amount': '200'} -- amount type: <class 'str'>
food 200
{'category': 'travel', 'amount': '500'} -- amount type: <class 'str'>
travel 500
```

**Flow diagram — how `DictReader` turns raw CSV text into dicts, row by row:**

```
Raw file contents:
    category,amount
    food,200
    travel,500

DictReader:
    Step 1: reads the FIRST line only, splits it on commas, and stores
            the result as the "field names" — ["category", "amount"].
            This first line is CONSUMED here — it never appears as a
            data row when you iterate.

    Step 2: for each SUBSEQUENT line, split on commas, then zip each
            value up with its corresponding field name from Step 1:
                "food,200"   -> ["food", "200"]
                              -> {"category": "food", "amount": "200"}
                "travel,500" -> ["travel", "500"]
                              -> {"category": "travel", "amount": "500"}
```

`type(row["amount"])` printing `<class 'str'>` (not `int` or `float`) is the detail the doc explicitly warns about — a CSV file is, at the byte level, nothing but text, so `DictReader` has no way to know `"200"` was "meant" to be a number rather than, say, a product code that happens to look numeric. Converting it (`float(row["amount"])`) is always your responsibility, and forgetting it is a very easy real bug — `"200" + "500"` would silently give you `"200500"` (string concatenation) instead of `700` if you tried to "add" two unconverted CSV amounts.

### `pathlib` — the modern way to handle file paths

```python
from pathlib import Path

p = Path("data") / "transactions.csv"    # builds a path — the / operator is overloaded for this
p.exists()                                # True/False
p.name                                    # "transactions.csv"
p.suffix                                  # ".csv"
p.parent                                  # Path("data")

for csv_file in Path("data").glob("*.csv"):   # find all CSVs in a folder
    print(csv_file)
```

`pathlib` is preferred over the older `os.path` string-based approach in new code — it's more readable and less error-prone about slashes and separators across operating systems.

### Running this for real

**Real, verified output** — first checking the path before the file/folder exist, then creating a real `data/` folder with two CSVs in it and globbing for them:

```python
from pathlib import Path

p = Path("data") / "transactions.csv"
print(p)
print(p.exists())
print(p.name)
print(p.suffix)
print(p.parent)

Path("data").mkdir(exist_ok=True)
Path("data/transactions.csv").write_text("category,amount\nfood,200\n")
Path("data/other.csv").write_text("x\n")
for csv_file in Path("data").glob("*.csv"):
    print(csv_file)
print(p.exists())
```

```
data/transactions.csv
False
transactions.csv
.csv
data
data/other.csv
data/transactions.csv
True
```

**Why `p.exists()` printed `False` the first time and `True` the second, and why the `/` operator behaves like division on paths but not on strings:** `Path("data") / "transactions.csv"` overloads Python's division operator (`/`) to mean "join this path segment onto that one" via a special method (`__truediv__` — a dunder method, exactly the kind you'll cover in depth in the OOP doc) — it's building a *description* of a location, `data/transactions.csv`, entirely independent of whether anything actually exists there yet. The first `p.exists()` correctly reports `False` because, at that point in the script, no `data` folder had been created. Only after `Path("data").mkdir(...)` and `Path("data/transactions.csv").write_text(...)` actually created the folder and file on disk did the *second* `p.exists()` call — checking the exact same path object — correctly flip to `True`. This is worth internalizing: a `Path` object is just a structured string with convenience methods; building one never touches the filesystem by itself, only methods like `.exists()`, `.write_text()`, `.mkdir()`, and `.glob()` actually reach out and interact with real files and folders.

---

## Practice questions

1. **Word frequency from a file.** Write a function `word_count(filepath)` that reads a text file and returns a dict mapping each word (lowercased) to how many times it appears. Handle punctuation reasonably (a period stuck to a word shouldn't count as a different word) — don't overthink this, just get numbers to something sensible. This combines file reading, string cleaning, and the counting-with-a-dict pattern from Topic 2.

2. **Explain in your own words**: why does `result += word` in a loop get slower and slower as the loop runs, when `"".join(words)` doesn't have that problem? Tie it back to string immutability specifically.

3. **CSV without pandas.** Given a CSV file with columns `category,amount`, write a function `total_by_category(filepath)` that returns a dict like `{"food": 350.0, "travel": 800.0}` — the same shape as Topic 2's group-by exercise, but now reading from an actual file instead of a Python list. Remember: values from `csv.DictReader` come in as strings, so you'll need to convert `amount` to a `float` before summing.

4. **Predict, then verify** — what happens here, and why?
   ```python
   with open("no_such_file.txt") as f:
       content = f.read()
   print("done")
   ```
   Then rewrite it so `"done"` still prints even when the file doesn't exist, without ever crashing.

---

*As always — attempt for real, paste your code when ready, I'll check it. Say "next" when done and I'll build the doc for OOP (classes, inheritance, dunder methods) — the start of the Intermediate group.*
