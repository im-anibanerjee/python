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
