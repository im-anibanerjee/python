#4. test an exception with pytest.raises, including the message
import pytest

def withdraw(balance, amount):
    if amount > balance:
        raise ValueError("insufficient funds")
    return balance - amount

def test_withdraw_raises():
    with pytest.raises(ValueError, match="insufficient funds"):
        withdraw(100, 500)
'''
test_withdraw_raises PASSED
'''
# the exception type matches (ValueError) and the message matches the regex - test passes

# now deliberately break the match string
def test_withdraw_raises_broken_match():
    with pytest.raises(ValueError, match="not enough money"):
        withdraw(100, 500)
'''
    def withdraw(balance, amount):
        if amount > balance:
>           raise ValueError("insufficient funds")
E           ValueError: insufficient funds

during handling of the above exception, another exception occurred:

    def test_withdraw_raises_broken_match():
>       with pytest.raises(ValueError, match="not enough money"):
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'not enough money'
E         Actual message: 'insufficient funds'

1 failed
'''
# the right exception type still gets raised (ValueError), but pytest.raises also checks the
# message against match= - "not enough money" never appears in the real message
# ("insufficient funds"), so the test fails even though the exception type was correct
# this is why match= exists at all - catching the right exception TYPE but the wrong message
# is a real, common bug (e.g. someone edits the error text later and breaks an assumption
# some other part of the code was relying on)


#5. fixture scope, proven side by side
@pytest.fixture(scope="function")   # default - reruns for every test
def func_scoped():
    print("\n  [function-scoped setup]")
    return "x"

@pytest.fixture(scope="module")     # runs once for the whole file
def module_scoped():
    print("\n  [module-scoped setup]")
    return "y"

def test_one(func_scoped, module_scoped):
    assert func_scoped == "x"

def test_two(func_scoped, module_scoped):
    assert module_scoped == "y"
'''
run with: python -m pytest -v -s

test_scope.py::test_one
  [module-scoped setup]

  [function-scoped setup]
PASSED
test_scope.py::test_two
  [function-scoped setup]
PASSED
'''
# module-scoped setup printed once, only before test_one (the first test that needed it) -
# test_two reused the same value without rerunning it
# function-scoped setup printed twice, once per test, since its default scope reruns every time
