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

### Writing

```python
with open("output.txt", "w") as f:
    f.write("line one\n")
    f.write("line two\n")

with open("output.txt", "a") as f:
    f.write("appended line\n")     # adds without erasing what's there
```

### Handling a missing file properly (ties back to Topic 1's exceptions)

```python
try:
    with open("maybe_missing.txt") as f:
        content = f.read()
except FileNotFoundError:
    content = ""
    print("File not found — using empty default")
```

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
