# Topic 2 — Collections: Lists, Tuples, Dicts & Sets

*Phase 1, Beginner group — item 2 of 4. Same drill: type the examples yourself, then do the practice questions before checking this off.*

---

## 1. The four collections, at a glance

| Type | Ordered? | Mutable? | Duplicates? | Indexed by | Example |
|---|---|---|---|---|---|
| `list` | Yes | Yes | Yes | position (int) | `[1, 2, 3]` |
| `tuple` | Yes | No | Yes | position (int) | `(1, 2, 3)` |
| `dict` | Yes (insertion order, since 3.7) | Yes | Keys: no. Values: yes | key (any hashable) | `{"a": 1}` |
| `set` | No | Yes | No | — (membership only) | `{1, 2, 3}` |

The decision of which one to reach for is itself an interview-relevant skill — you'll see it woven through the examples below, not just listed once.

## 2. Lists — the workhorse

```python
nums = [3, 1, 4, 1, 5]

nums.append(9)          # [3, 1, 4, 1, 5, 9]        — add to end
nums.insert(0, 100)     # [100, 3, 1, 4, 1, 5, 9]    — insert at index
nums.extend([2, 3])     # adds each element of [2,3] individually (not as a nested list)
nums.remove(1)          # removes the FIRST 1 it finds, by value
popped = nums.pop()     # removes & returns the LAST item
popped = nums.pop(0)    # removes & returns item at index 0
nums.sort()             # sorts in place, returns None
sorted_copy = sorted(nums)  # returns a NEW sorted list, leaves nums untouched
nums.reverse()          # reverses in place
```

**Slicing** — `list[start:stop:step]`, `stop` is exclusive:

```python
nums = [0, 1, 2, 3, 4, 5]
nums[1:4]     # [1, 2, 3]
nums[:3]      # [0, 1, 2]      — omit start = "from the beginning"
nums[3:]      # [3, 4, 5]      — omit stop = "to the end"
nums[::2]     # [0, 2, 4]      — every 2nd element
nums[::-1]    # [5, 4, 3, 2, 1, 0]   — reversed, common trick
```

**List comprehensions** — you'll use these constantly:

```python
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
pairs = [(x, y) for x in range(3) for y in range(3) if x != y]
```

Read it as: `[expression for item in iterable if condition]` — the `if` filters, the expression transforms.

### Copying — the gotcha that connects back to Topic 1

```python
a = [1, 2, 3]
b = a              # NOT a copy — b and a are the same list
c = a.copy()       # a real copy — c is a new list, but...
d = a[:]           # another way to copy — same as .copy()

nested = [[1, 2], [3, 4]]
shallow = nested.copy()
shallow[0].append(99)
print(nested)      # [[1, 2, 99], [3, 4]] — the INNER lists are still shared!
```

`.copy()` is a **shallow copy** — it copies the outer list, but nested mutable objects inside it are still the same shared objects. For a true independent copy of nested structures, use `copy.deepcopy()`. This is the exact same "shared mutable object" trap from the mutable-default-argument bug in Topic 1 — same root cause, different situation.

### Running every list operation for real, step by step

The mutation methods above (`append`, `insert`, `extend`, `remove`, `pop`, `sort`, `reverse`) are easy to misread because most of them return `None` and change `nums` silently — so here's the exact same block, but printing `nums` after every single line so nothing is left to the imagination:

```python
nums = [3, 1, 4, 1, 5]
print("start:", nums)
nums.append(9)
print("after append(9):", nums)
nums.insert(0, 100)
print("after insert(0,100):", nums)
nums.extend([2, 3])
print("after extend([2,3]):", nums)
nums.remove(1)
print("after remove(1):", nums)
popped = nums.pop()
print("popped (no arg):", popped, "| nums now:", nums)
popped = nums.pop(0)
print("popped (0):", popped, "| nums now:", nums)
r = nums.sort()
print("sort() return value:", r, "| nums now:", nums)
sorted_copy = sorted(nums)
print("sorted_copy:", sorted_copy, "| nums unchanged:", nums)
nums.reverse()
print("after reverse():", nums)
```

**Real, verified output:**

```
start: [3, 1, 4, 1, 5]
after append(9): [3, 1, 4, 1, 5, 9]
after insert(0,100): [100, 3, 1, 4, 1, 5, 9]
after extend([2,3]): [100, 3, 1, 4, 1, 5, 9, 2, 3]
after remove(1): [100, 3, 4, 1, 5, 9, 2, 3]
popped (no arg): 3 | nums now: [100, 3, 4, 1, 5, 9, 2]
popped (0): 100 | nums now: [3, 4, 1, 5, 9, 2]
sort() return value: None | nums now: [1, 2, 3, 4, 5, 9]
sorted_copy: [1, 2, 3, 4, 5, 9] | nums unchanged: [1, 2, 3, 4, 5, 9]
after reverse(): [9, 5, 4, 3, 2, 1]
```

**Flow trace — the two lines most likely to trip you up:**

```
nums.remove(1)
    nums BEFORE: [100, 3, 4, 1, 5, 9, 2, 3]
                          ▲
                          └─ there are TWO 1's-worth-of-candidates here?
                             No — only ONE literal value 1 exists in this
                             list (position 3). remove(1) means "remove
                             the value 1", not "remove index 1" — it
                             scans left to right and deletes the FIRST
                             element that equals 1.
    nums AFTER:  [100, 3, 4, 5, 9, 2, 3]

r = nums.sort()
    nums.sort() reorders the list IN PLACE (mutates the existing box,
    same object, same id()) and its return value is always None —
    exactly like list.append() and list.reverse(). This is a real,
    common bug source: writing `nums = nums.sort()` throws away your
    list and replaces it with None.

    sorted(nums), by contrast, does NOT touch nums at all — it builds
    and returns a BRAND NEW list, leaving the original exactly as it
    was. That's why "sorted_copy" and "nums" print as equal VALUES
    above, but they are two separate objects — same pattern as
    Topic 1 §2's a/b vs c (.copy()) distinction.
```

The one-line rule that covers both: **a method named with a verb that just describes an action (`sort`, `reverse`, `append`) usually mutates in place and returns `None`; a builtin function that takes the collection as an argument (`sorted(nums)`, `reversed(nums)`) usually returns a new result and leaves the original untouched.** It's not a hard law of Python, but it holds often enough to be a useful first guess when you hit an unfamiliar method.

### Running the slicing examples for real

**Real, verified output**, running `nums = [0, 1, 2, 3, 4, 5]` through each slice:

```
[1, 2, 3]
[0, 1, 2]
[3, 4, 5]
[0, 2, 4]
[5, 4, 3, 2, 1, 0]
```

**How to read `nums[start:stop:step]`, mechanically — think of the indices as fenceposts *between* the elements, not labels on the elements themselves:**

```
index:     0   1   2   3   4   5
value:   [ 0 , 1 , 2 , 3 , 4 , 5 ]
fence:   0   1   2   3   4   5   6
         ▲                       ▲
      start of list          end of list

nums[1:4]   → start at fencepost 1, stop BEFORE fencepost 4
              → grabs elements at index 1, 2, 3  → [1, 2, 3]

nums[:3]    → start omitted = fencepost 0 (the very beginning)
              → stop before fencepost 3 → [0, 1, 2]

nums[3:]    → start at fencepost 3, stop omitted = run to the very end
              → [3, 4, 5]

nums[::2]   → start/stop omitted = the whole list, step 2 = take every
              OTHER element → indices 0, 2, 4 → [0, 2, 4]

nums[::-1]  → step -1 means "walk backward" — start/stop omitted with a
              negative step means "start from the end, walk to the
              beginning" → the entire list, reversed
```

`stop` being exclusive (never included) is the single most important rule here — it's *why* `nums[1:4]` gives you exactly `4 - 1 = 3` elements, which is a handy sanity check you can run in your head on any slice: `stop - start` (when step is 1) tells you how many elements you'll get back.

### Running the comprehensions for real

**Real, verified output:**

```python
squares = [x**2 for x in range(10)]
print(squares)
evens = [x for x in range(20) if x % 2 == 0]
print(evens)
pairs = [(x, y) for x in range(3) for y in range(3) if x != y]
print(pairs)
```

```
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
[(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]
```

**Flow diagram — a comprehension is a loop with the body written backward.** `[x**2 for x in range(10)]` is exactly equivalent to writing this out longhand:

```python
squares = []
for x in range(10):
    squares.append(x**2)
```

```
comprehension:   [   x**2      for x in range(10)   ]
                     │              │
                     │              └─ the loop: "for each x, in this order..."
                     └─ the body: "...append THIS expression to the result"

longhand:        squares = []
                  for x in range(10):
                      squares.append(x**2)   ← same expression, same order
```

The `pairs` example is the one worth tracing fully, because it has *two* loop variables and a filter — this is a nested loop, read left to right exactly like nested `for` statements would be:

```
[(x, y) for x in range(3) for y in range(3) if x != y]

is equivalent to:

result = []
for x in range(3):        ← OUTER loop (written first)
    for y in range(3):    ← INNER loop (written second)
        if x != y:        ← filter, checked on every (x, y) pair
            result.append((x, y))

Trace:
  x=0: y=0 -> 0!=0? no, skip   | y=1 -> 0!=1? yes -> (0,1) | y=2 -> yes -> (0,2)
  x=1: y=0 -> yes -> (1,0)     | y=1 -> skip               | y=2 -> yes -> (1,2)
  x=2: y=0 -> yes -> (2,0)     | y=1 -> yes -> (2,1)        | y=2 -> skip

  result: [(0,1), (0,2), (1,0), (1,2), (2,0), (2,1)]   ← matches the real output above
```

### Tracing the copying gotcha for real, with proof

**Real, verified output**, extending the exact snippet above with `is` checks and an `id()` comparison on the shared nested list:

```python
a = [1, 2, 3]
b = a
c = a.copy()
d = a[:]
print("a is b:", a is b)
print("a is c:", a is c)
print("a is d:", a is d)
print("c == a:", c == a)

nested = [[1, 2], [3, 4]]
shallow = nested.copy()
shallow[0].append(99)
print(nested)
print("nested[0] is shallow[0]:", nested[0] is shallow[0])
```

```
a is b: True
a is c: False
a is d: False
c == a: True
[[1, 2, 99], [3, 4]]
nested[0] is shallow[0]: True
```

**Flow diagram — why a shallow copy still leaks a shared inner list:**

```
nested = [[1, 2], [3, 4]]

    ┌───────────────────────────┐
    │  outer list                │
    │  ┌──────┐    ┌──────┐      │
    │  │[1,2] │    │[3,4] │      │  ← the OUTER list holds two references
    │  └──────┘    └──────┘      │     (sticky-note style) to two INNER
    └───────────────────────────┘     list objects — it doesn't contain
         ▲                            the inner lists "inside" itself,
        [nested]                      it just points at them.

shallow = nested.copy()

    .copy() makes a NEW outer list/box — but only copies the outer
    box's CONTENTS, which are just the two pointers/references, not
    the inner list objects those pointers point at.

    ┌───────────────────────────┐        ┌───────────────────────────┐
    │  outer list (ORIGINAL)     │        │  outer list (COPY)         │
    │  ┌──────┐    ┌──────┐      │        │  ┌──────┐    ┌──────┐      │
    │  │[1,2] │    │[3,4] │      │        │  │  ●   │    │  ●   │      │
    │  └──────┘    └──────┘      │        │  └──┼───┘    └──┼───┘      │
    └───────────────────────────┘        └─────┼───────────┼──────────┘
         ▲                                       │           │
        [nested]                                [shallow]    │
                                                   │           │
                    both point at the SAME two inner list objects ──┘

shallow[0].append(99)
    → reaches through shallow's pointer into the FIRST inner list —
      which is the SAME object nested[0] also points at — and mutates
      it. Both names now "see" [1, 2, 99], because there was only ever
      one such object.
```

This is precisely why `nested[0] is shallow[0]` prints `True` above — the two *outer* lists are genuinely different objects (`nested is shallow` would be `False`), but their *elements* — the inner lists — are shared. `copy.deepcopy()` is the fix specifically because it recursively copies every nested mutable object too, all the way down, instead of stopping one level in.

## 3. Tuples — lists that can't change

```python
point = (3, 4)
x, y = point        # unpacking
name, age, city = ("Ani", 28, "Hyderabad")   # multiple unpacking
```

Tuples are immutable — you can't append, remove, or reassign an element. Why use them over lists at all?

- **Intent** — signals "this shouldn't change" to anyone reading the code.
- **Hashability** — tuples (of hashable items) can be dict keys or set members; lists can't (see §4).
- **Slight performance edge** — marginal, rarely the real reason to choose one.
- **Function returns** — `return x, y` is really returning a tuple; this is how "multiple return values" work in Python.

```python
def divmod_manual(a, b):
    return a // b, a % b     # returns a tuple (quotient, remainder)

q, r = divmod_manual(17, 5)   # unpacked immediately
```

### Running the unpacking examples for real

**Real, verified output:**

```python
point = (3, 4)
x, y = point
print(x, y)
name, age, city = ("Ani", 28, "Hyderabad")
print(name, age, city)

def divmod_manual(a, b):
    return a // b, a % b

q, r = divmod_manual(17, 5)
print(q, r)
result = divmod_manual(17, 5)
print(result, type(result))
```

```
3 4
Ani 28 Hyderabad
3 2
(3, 2) <class 'tuple'>
```

**Flow diagram — unpacking is positional matching, one slot per name, left to right:**

```
point = (3, 4)
x, y = point

    (3, 4)          ← a tuple of exactly 2 elements
     │  │
     │  └─────► y = 4    (2nd position  →  2nd name)
     └────────► x = 3    (1st position  →  1st name)

    If the number of names didn't match the number of elements,
    Python raises ValueError: too many/not enough values to unpack —
    unpacking is strict about counts, it never silently drops or pads.
```

**What `return a // b, a % b` is actually doing — the part people often don't realize is "just a tuple":** the comma between `a // b` and `a % b` is *tuple construction syntax* — writing `x, y` (with no brackets at all) already builds a tuple. `return a // b, a % b` is exactly the same as `return (a // b, a % b)` — the parentheses are optional here, not required. This is the real mechanism behind "returning multiple values" in Python: there's no special multi-return feature in the language at all, a function can only ever return *one* object, and what you're doing here is packing two values into that one object (a tuple), which the caller then optionally unpacks back into two names (`q, r = ...`) or leaves packed (`result = ...`, then `result[0]`, `result[1]`). The output above proves this directly — `result` prints as `(3, 2)` and `type(result)` is `<class 'tuple'>`.

## 4. Dicts — key/value lookups

```python
person = {"name": "Ani", "role": "SWE"}

person["role"]              # "SWE" — KeyError if missing
person.get("role")          # "SWE" — None if missing, no error
person.get("level", "N/A")  # "N/A" — custom default if missing

person["team"] = "CES"      # add or overwrite a key
person.pop("team")          # remove and return the value
del person["role"]          # remove, no return

for key in person:                    # iterates over KEYS by default
    print(key)
for key, value in person.items():     # the pattern you'll use constantly
    print(key, value)
for value in person.values():
    print(value)
```

**Dict comprehension:**

```python
squares = {x: x**2 for x in range(5)}   # {0:0, 1:1, 2:4, 3:9, 4:16}
```

**Merging** (3.9+): `merged = dict1 | dict2` — keys in `dict2` win on conflict. Older style: `{**dict1, **dict2}`.

### Why dict keys have to be hashable

A dict is built on a hash table — it uses `hash(key)` to find where to store/look up a value, in roughly constant time. That only works if the key's hash never changes, which is why **only immutable types can be dict keys**: strings, numbers, tuples (as long as everything *inside* the tuple is also immutable). A list can't be a key — Python raises `TypeError: unhashable type: 'list'` — because if you mutated the list after using it as a key, its hash would change and the dict's internal bookkeeping would break.

```python
cache = {}
cache[(1, 2)] = "found it"   # fine — tuple of ints is hashable
cache[[1, 2]] = "nope"       # TypeError: unhashable type: 'list'
```

### A pattern worth knowing cold: counting with a dict

```python
words = ["a", "b", "a", "c", "b", "a"]
counts = {}
for w in words:
    counts[w] = counts.get(w, 0) + 1
# {"a": 3, "b": 2, "c": 1}
```

`collections.Counter(words)` does this in one line and is worth knowing exists, but understand the manual version — it's the pattern interviewers actually want to see you reason through.

### Running every dict operation for real

**Real, verified output**, the exact block above with prints inserted after every mutation:

```python
person = {"name": "Ani", "role": "SWE"}
print(person["role"])
print(person.get("role"))
print(person.get("level", "N/A"))
person["team"] = "CES"
print(person)
popped = person.pop("team")
print("popped:", popped, "| now:", person)
del person["role"]
print(person)
```

```
SWE
SWE
N/A
{'name': 'Ani', 'role': 'SWE', 'team': 'CES'}
popped: CES | now: {'name': 'Ani', 'role': 'SWE'}
{'name': 'Ani'}
```

And the three iteration styles, freshly building `person` again first:

```
key: name
key: role
item: name Ani
item: role SWE
value: Ani
value: SWE
```

**Flow diagram — how `person["role"]` and `.get()` differ under the hood, and why one crashes and the other doesn't:**

```
person = {"name": "Ani", "role": "SWE"}

person["role"]
    1. compute hash("role")
    2. jump directly to the internal "bucket" that hash points to
       (this is the O(1)-average part — no scanning key by key)
    3. key found  ->  return "SWE"
       key NOT found -> raise KeyError immediately, no fallback

person.get("level", "N/A")
    1. compute hash("level")
    2. jump to that bucket
    3. key found  -> return its value
       key NOT found -> instead of raising, quietly return the
                         second argument ("N/A"), or None if you
                         didn't supply one
```

`.get()` exists specifically for the case where a missing key is an *expected, normal* possibility, not an error — using it avoids wrapping every lookup in a `try/except KeyError`.

**`counts[w] = counts.get(w, 0) + 1` — the counting idiom, traced value by value:**

```python
words = ["a", "b", "a", "c", "b", "a"]
counts = {}
for w in words:
    counts[w] = counts.get(w, 0) + 1
print(counts)
```

Real, verified output: `{'a': 3, 'b': 2, 'c': 1}` — and for comparison, `collections.Counter(words)` gives `Counter({'a': 3, 'b': 2, 'c': 1})`, the same data in a dict subclass with a couple of extra convenience methods.

```
w="a": counts.get("a", 0) -> "a" not in counts yet -> 0  -> counts["a"] = 0+1 = 1
w="b": counts.get("b", 0) -> not in counts yet     -> 0  -> counts["b"] = 0+1 = 1
w="a": counts.get("a", 0) -> "a" IS in counts now  -> 1  -> counts["a"] = 1+1 = 2
w="c": counts.get("c", 0) -> not in counts yet     -> 0  -> counts["c"] = 0+1 = 1
w="b": counts.get("b", 0) -> "b" IS in counts now  -> 1  -> counts["b"] = 1+1 = 2
w="a": counts.get("a", 0) -> "a" IS in counts now  -> 2  -> counts["a"] = 2+1 = 3

final: {"a": 3, "b": 2, "c": 1}
```

The trick is that `.get(w, 0)` supplies "0 occurrences so far" the *first* time a word is seen (when it's genuinely not in the dict yet), and the dict's own running total every time after that — one line doing double duty as both "initialize" and "increment."

### Verifying dict comprehension and merging for real

**Real, verified output:**

```python
squares = {x: x**2 for x in range(5)}
print(squares)

dict1 = {"a": 1, "b": 2}
dict2 = {"b": 99, "c": 3}
merged = dict1 | dict2
print(merged)
merged2 = {**dict1, **dict2}
print(merged2)
```

```
{0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
{'a': 1, 'b': 99, 'c': 3}
{'a': 1, 'b': 99, 'c': 3}
```

Notice `"b"` in the merged result is `99`, not `2` — confirming "keys in `dict2` win on conflict": the `|` operator (and the equivalent `{**dict1, **dict2}` unpacking form) processes `dict1` first, then lays `dict2`'s keys on top, so any key that exists in both ends up holding `dict2`'s value, exactly like a later assignment overwriting an earlier one to the same key.

### Verifying the hashability error for real

**Real, verified output:**

```python
cache = {}
cache[(1, 2)] = "found it"
print(cache)
try:
    cache[[1, 2]] = "nope"
except TypeError as e:
    print("TypeError:", e)
```

```
{(1, 2): 'found it'}
TypeError: unhashable type: 'list'
```

**Why this specific error, traced:** when Python evaluates `cache[[1, 2]] = "nope"`, before it can even begin the hash-table bucket lookup described above, it must first compute `hash([1, 2])` to know *which* bucket to use. Lists deliberately don't implement `__hash__` at all (it's set to `None` on the list type) *because* they're mutable — if a list could be hashed and used as a key, and you later `.append()`ed to it, its hash would change, but the dict's internal bucket structure was built using the *old* hash, so the entry would become permanently unfindable (a "lost" key sitting in the wrong bucket forever). Rather than allow that silent corruption, Python refuses up front with `TypeError`, the moment you try. Tuples don't have this problem because they can never be mutated after creation — their hash is safe to compute once and rely on forever, which is exactly why `cache[(1, 2)] = ...` on the line above worked without any error.

## 5. Sets — uniqueness and fast membership

```python
s = {1, 2, 3, 2, 1}      # {1, 2, 3} — duplicates silently dropped
s.add(4)
s.remove(1)              # KeyError if not present
s.discard(99)            # no error even if not present

a = {1, 2, 3}
b = {2, 3, 4}
a | b     # union            -> {1, 2, 3, 4}
a & b     # intersection     -> {2, 3}
a - b     # difference       -> {1}
a ^ b     # symmetric diff   -> {1, 4}   (in one but not both)
```

Two big reasons to reach for a set:

1. **Deduplication** — `list(set(my_list))` removes duplicates (but loses order — see the practice questions for how to dedupe *and* keep order).
2. **Fast membership testing** — `x in my_set` is O(1) average case; `x in my_list` is O(n) — it has to scan. This matters a lot once your lists get large, and it's a very common "how would you optimize this" interview follow-up.

`frozenset` is the immutable version of a set — exists mainly so a set can be used as a dict key or inside another set (since regular sets, being mutable, aren't hashable either).

### Running every set operation for real

**Real, verified output:**

```python
s = {1, 2, 3, 2, 1}
print(s)
s.add(4)
print(s)
s.remove(1)
print(s)
s.discard(99)
print(s)

a = {1, 2, 3}
b = {2, 3, 4}
print("union:", a | b)
print("intersection:", a & b)
print("difference:", a - b)
print("symmetric diff:", a ^ b)
```

```
{1, 2, 3}
{1, 2, 3, 4}
{2, 3, 4}
{2, 3, 4}
union: {1, 2, 3, 4}
intersection: {2, 3}
difference: {1}
symmetric diff: {1, 4}
```

**Why `s = {1, 2, 3, 2, 1}` immediately collapses to `{1, 2, 3}`, mechanically:** a set is a hash table with no values attached — just keys (in fact, CPython's `set` is implemented as essentially a `dict` where every value is ignored). When Python builds the literal, it processes each element left to right and computes its hash to decide which bucket it belongs in. The *first* `1` gets inserted into its bucket. When the *second* `1` comes along later in the same literal, Python hashes it, lands in the *same* bucket, and finds a value already sitting there that compares equal (`1 == 1`) — so it's treated as "already present" and simply not added again. There's no error, no warning — duplicates are just silently absorbed, because a set's entire definition is "a bucket can only ever hold one representative of each distinct value."

**Set algebra, visualized as literal circles (the way these are usually drawn on a whiteboard in an interview):**

```
a = {1, 2, 3}          b = {2, 3, 4}

        a           b
     ┌──────┐    ┌──────┐
     │  1   │    │      │
     │   ┌──┼────┼──┐   │
     │   │2,3│    │  │  │
     │   └──┼────┼──┘   │
     │      │    │  4   │
     └──────┘    └──────┘

a | b  (union)         -> everything in EITHER circle  -> {1, 2, 3, 4}
a & b  (intersection)  -> only the OVERLAP              -> {2, 3}
a - b  (difference)    -> in a, with the overlap removed -> {1}
a ^ b  (symmetric diff)-> everything EXCEPT the overlap  -> {1, 4}
```

`s.remove(1)` vs `s.discard(99)` — the distinction is purely about missing elements: `remove` treats "the element wasn't there" as an error worth stopping the program for (`KeyError`), while `discard` treats it as a non-event, a no-op. Use `remove` when the element's presence is something your program logic actually depends on (its absence signals a real bug); use `discard` when you're unconditionally saying "make sure this isn't in here" and don't care whether it already wasn't.

### Proving the O(1) vs O(n) membership claim, with a real timed measurement

The table in §6 states that `x in a_set` is O(1) average case while `x in a_list` is O(n). That's not something to take on faith — here it is measured directly, searching for the *worst possible case* (the very last element, forcing a full scan in the list version) across a 100,000-element collection, 100 times each:

```python
import timeit
big_list = list(range(100000))
big_set = set(range(100000))
target = 99999
t_list = timeit.timeit(lambda: target in big_list, number=100)
t_set = timeit.timeit(lambda: target in big_set, number=100)
print(f"list membership (100 checks): {t_list:.6f}s")
print(f"set membership (100 checks): {t_set:.6f}s")
```

**Real, verified output (your exact numbers will vary by machine, but the *shape* of the gap will not):**

```
list membership (100 checks): 0.093233s
set membership (100 checks): 0.000011s
```

That's roughly an 8,000x difference, for this exact worst-case setup — the list has to walk past all 99,999 earlier elements one at a time before confirming `99999 in big_list`, while the set jumps straight to the right bucket via a hash computation regardless of how many elements it holds. This is the concrete, measured version of "if your code does `if x in some_list:` inside a loop over thousands of items, that's an O(n²) smell" from §6 — converting to a set first isn't a theoretical optimization, it's the difference between milliseconds and something that noticeably drags.

### Verifying `frozenset` for real

**Real, verified output:**

```python
fs = frozenset([1, 2, 3])
print(fs)
try:
    fs.add(4)
except AttributeError as e:
    print("AttributeError:", e)
d = {fs: "a frozenset as a dict key"}
print(d)
```

```
frozenset({1, 2, 3})
AttributeError: 'frozenset' object has no attribute 'add'
{frozenset({1, 2, 3}): 'a frozenset as a dict key'}
```

`frozenset` simply doesn't define mutating methods like `.add()`/`.remove()` at all — trying to call one isn't a runtime permission check, it's `AttributeError` because the method genuinely doesn't exist on the type, the same category of error you'd get calling any made-up method name on any object. Because it's immutable, it's hashable (same reasoning as tuples in §4), which is exactly why the last line above works: a `frozenset` can sit as a dict key, where a regular mutable `set` cannot.

## 6. Time complexity — the table interviewers actually want

| Operation | `list` | `dict` | `set` |
|---|---|---|---|
| Access by index/key | O(1) | O(1) avg | — |
| Search / `in` | O(n) | O(1) avg (key) | O(1) avg |
| Insert at end | O(1) amortized | O(1) avg | O(1) avg |
| Insert at start/middle | O(n) | — | — |
| Delete | O(n) | O(1) avg | O(1) avg |

The one-line version to internalize: **lists are fast to iterate and slow to search; dicts and sets are slow-ish to iterate (they have hashing overhead) but fast to search.** If your code does `if x in some_list:` inside a loop over thousands of items, that's an O(n²) smell — converting `some_list` to a `set` first is a real, defensible optimization to mention in an interview.

---

## Practice questions

1. **Dedupe, preserving order.** `list(set(items))` removes duplicates but scrambles order (sets are unordered). Write a function `dedupe(items)` that removes duplicates from a list while keeping the *first* occurrence of each item, in original order. (Hint: you'll want a `set` to track "have I seen this?" and a `list` to build the result — using both for what each is good at.)

2. **Group by key.** Given a list of dicts like:
   ```python
   transactions = [
       {"category": "food", "amount": 200},
       {"category": "travel", "amount": 500},
       {"category": "food", "amount": 150},
       {"category": "travel", "amount": 300},
   ]
   ```
   write a function that returns a dict mapping each category to the **total** amount spent in it: `{"food": 350, "travel": 800}`. This is directly the shape of thing you'll do constantly in the ETL/pandas phase later — pandas' `groupby` is doing this same operation for you, faster, at scale.

3. **Explain in your own words**: why can a tuple be a dictionary key but a list can't? Tie your answer to *hashability* specifically, not just "because tuples are immutable" — explain *why* immutability is the thing that makes hashing safe.

4. **Predict, then verify:**
   ```python
   original = [[1, 2], [3, 4]]
   copy_a = original.copy()
   copy_b = original[:]

   copy_a[0][0] = 999

   print(original)
   print(copy_b)
   ```
   Explain why both `original` and `copy_b` show the change, even though you only modified `copy_a`.

---

*Same as before — attempt these for real, paste your answers when ready, and I'll check them. Say "next" when you're through this one and I'll build the doc for strings & file I/O.*
