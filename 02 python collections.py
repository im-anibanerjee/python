#1. Dedupe, preserving order
# list(set(items)) removes duplicates but scrambles order (sets are unordered)
def dedup(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    print(result)

dedup([1,2,1,2,3,3,5,7,8,7,9,8])
#[1, 2, 3, 5, 7, 8, 9]

#2. Group by key
def group(items):
    result = {}
    for item in items:
        category = item.get('category')
        amount = item.get('amount')
        result[category] = result.get(category, 0) + amount
    print(result)

transactions = [
    {"category": "food", "amount": 200},
    {"category": "travel", "amount": 500},
    {"category": "food", "amount": 150},
    {"category": "travel", "amount": 300},
]
group(transactions)
# {'food': 150, 'travel': 300}

#3. Explain in your own words
'''
dict is built on a hash table — it uses hash(key) to find where to store/look up a value, in roughly constant time. 
that only works if the key's hash never changes, which is why only immutable types can be dict keys: strings, numbers, tuples 
(as long as everything inside the tuple is also immutable)

a list can't be a key — Python raises TypeError: unhashable type: 'list' 
because if you mutated the list after using it as a key, its hash would change and the dict's internal bookkeeping would break
'''

#4. Predict, then verify
original = [[1, 2], [3, 4]]
copy_a = original.copy()
copy_b = original[:]
copy_a[0][0] = 999
print(original)
print(copy_b)

'''
[[999, 2], [3, 4]]
[[999, 2], [3, 4]]
'''