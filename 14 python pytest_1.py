#1. reproduce the assert-rewriting difference, yourself
# plain python run, no pytest -- saved separately as plain_assert.py:
#
# def add(a, b):
#     return a + b
#
# assert add(2, 3) == 6
'''
traceback (most recent call last):
  file "plain_assert.py", line 4, in <module>
    assert add(2, 3) == 6
assertionerror
'''
# plain assert gives nothing but "assertionerror" - no idea what add(2,3) actually returned

def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 6
'''
test_plain_assert.py::test_add FAILED                                    [100%]

=================================== FAILURES ===================================
___________________________________ test_add ___________________________________

    def test_add():
>       assert add(2, 3) == 6
E       assert 5 == 6
E        +  where 5 = add(2, 3)

test_plain_assert.py:5: AssertionError
'''
# same exact assert, run through pytest instead of plain python -
# pytest rewrites the assert and shows the actual value (5) and where it came from, with no
# custom message written anywhere - this is the whole reason to use pytest over a bare assert


#2. write a fixture with setup and teardown, and prove teardown runs
import pytest

@pytest.fixture
def sample_list():
    print("\n[fixture setup]")
    data = [1, 2, 3]
    yield data
    print("[fixture teardown]")

def test_uses_fixture(sample_list):
    assert sum(sample_list) == 6
'''
run with: python -m pytest -v -s

test_features.py::test_uses_fixture
[fixture setup]
PASSED[fixture teardown]
'''
# setup prints before the test body runs, teardown prints after - yield is the split point
# everything before yield is setup, the yielded value is what the test receives, everything
# after yield is teardown and runs once the test finishes


#3. parametrize a test over at least 4 cases, including one expected to fail
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (2, 2, 4),
    (0, 0, 0),
    (-1, 1, 0),
    (5, 5, 11),   # deliberately wrong on purpose - 5+5 is 10, not 11
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
'''
test_q3.py::test_add_parametrized[1-2-3] PASSED
test_q3.py::test_add_parametrized[2-2-4] PASSED
test_q3.py::test_add_parametrized[0-0-0] PASSED
test_q3.py::test_add_parametrized[-1-1-0] PASSED
test_q3.py::test_add_parametrized[5-5-11] FAILED

a = 5, b = 5, expected = 11

>       assert add(a, b) == expected
E       assert 10 == 11
E        +  where 10 = add(5, 5)

1 failed, 4 passed in 0.02s
'''
# one function definition became 5 separate test items - the [5-5-11] suffix in the failing
# line's name identifies exactly which parameter combination broke, the other 4 still passed
