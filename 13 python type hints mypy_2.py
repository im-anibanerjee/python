#4. compare plain mypy to mypy --strict
def add(a, b):
    return a + b

print(add(2, 3))
'''
5
'''
# plain mypy on this file
'''
success: no issues found in 1 source file
'''
# unannotated code is treated as Any by default, so plain mypy says nothing about it

# mypy --strict on the same unannotated file
'''
error: function is missing a type annotation  [no-untyped-def]
error: call to untyped function "add" in typed context  [no-untyped-call]
found 2 errors in 1 file (checked 1 source file)
'''
# --strict demands every function be annotated, and also flags CALLING an untyped function from typed code
# two different errors, on two different lines, from the same one missing annotation

# fully annotated version
def add_typed(a: int, b: int) -> int:
    return a + b

print(add_typed(2, 3))
'''
5
'''
# mypy --strict on the annotated version
'''
success: no issues found in 1 source file
'''
# adding the hints back is the entire fix - strict isn't checking anything new, just refusing to skip unannotated code


#5. contrast hint documentation vs real enforcement
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

u = User(name="ani", age="27")
print(u)
print(type(u.age))
'''
name='ani' age=27
<class 'int'>
'''
# age="27" is a string going in, but pydantic actually reads the age: int hint and coerces it -
# type(u.age) really is int, not str, so this is a real runtime effect, not just documentation

bad = User(name="ani", age="not a number")
'''
pydantic_core._pydantic_core.validationerror: 1 validation error for user
age
  input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not a number', input_type=str]
'''
# "not a number" can't be coerced into an int, so pydantic raises a real ValidationError at runtime

'''
this is the opposite of question 1 - plain python (def add(a: int, b: int)) never looked at the
hints at all, it just ran add("2","3") and did string concatenation
pydantic's BaseModel is a library that deliberately reads __annotations__ itself and uses it to
validate and convert real data, so here the hint isn't just a label on the jar, it's the actual
check being enforced, live, every time a User gets constructed
this is exactly what FastAPI does with request bodies too
'''

# bonus, found by actually running mypy on this same file too, not just python:
'''
error: argument "age" to "user" has incompatible type "str"; expected "int"  [arg-type]
'''
# mypy flags User(age="27") as a mismatch too, since it only reads the declared field type (int)
# and sees a str literal being passed - it has no idea pydantic will successfully coerce that
# string at runtime, so mypy and pydantic genuinely disagree here
# real pydantic projects install a separate mypy plugin specifically so mypy understands this
# coercion behavior instead of flagging it as a plain type error

