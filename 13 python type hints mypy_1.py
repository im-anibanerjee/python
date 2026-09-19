#1. prove hints aren't enforced, yourself
def add(a: int, b: int) -> int:
    return a + b

print(add("2", "3"))
'''
23
'''
# python ran it anyway and did string concatenation - the int hints were never checked

# checked with: python -m mypy "13 python type hints mypy_1.py"
'''
error: argument 1 to "add" has incompatible type "str"; expected "int"  [arg-type]
error: argument 2 to "add" has incompatible type "str"; expected "int"  [arg-type]
found 2 errors in 1 file (checked 1 source file)
'''
# mypy read the same file without running it and caught exactly what python let through


#2. reproduce the Optional/None bug, then fix it with narrowing
from typing import Optional

def find_user(user_id: int) -> Optional[str]:
    users = {1: "ani", 2: "priya"}
    return users.get(user_id)

# bug version - commented out below, since it crashes and would stop the rest of this file from running
# name = find_user(3)
# print(name.upper())
'''
traceback (most recent call last):
  file "q2_bug.py", line 8, in <module>
    print(name.upper())
attributeerror: 'nonetype' object has no attribute 'upper'
'''
# real python crash, from actually running the two lines above on their own -
# user_id 3 isn't in the dict, so find_user returns None, and None has no upper()

# mypy on the same buggy file, before ever running it
'''
error: item "none" of "str | none" has no attribute "upper"  [union-attr]
found 1 error in 1 file (checked 1 source file)
'''
# mypy caught this from the Optional[str] return type alone, without needing user_id to actually be 3

# fixed version, with narrowing
name = find_user(3)
if name is not None:
    print(name.upper())
else:
    print("no user found")
'''
no user found
'''
# python: no crash now
'''
success: no issues found in 1 source file
'''
# mypy clean too - the if name is not None check narrows name from str | none down to just str inside the block


#3. write a generic function with TypeVar
from typing import TypeVar, Sequence

T = TypeVar("T")

def first(items: Sequence[T]) -> T:
    return items[0]

n: int = first([1, 2, 3])
s: str = first(["a", "b"])
print(n, s)
'''
1 a
'''
'''
success: no issues found in 1 source file
'''
# T gets filled in per call - int for the first call, str for the second, and mypy tracks both correctly

# now deliberately assign the wrong type
bad: str = first([1, 2, 3])
'''
error: incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
found 1 error in 1 file (checked 1 source file)
'''
# first([1,2,3]) is inferred as returning int for that call, so assigning it into a str variable is the mismatch
# mypy flags exactly that one line, the two lines above it stay clean
