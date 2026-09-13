#3. Rewrite your Timer from Q1 using @contextlib.contextmanager
from contextlib import contextmanager
@contextmanager
def timer():
    import time
    start = time.perf_counter()
    print(f'execution starts: {start}')
    result = {}
    try:
        yield result
    finally:
        print(f'time taken: {time.perf_counter()-start}')
        result['elapsed'] = time.perf_counter()-start

with timer() as t:
    print('inside with')
print(t['elapsed'])
'''
execution starts: 0.050972
inside with
time taken: 0.00018669999999999798
0.0002605999999999997
'''

#4. Two files, one with
print("before copying")
with open("in.txt") as fin:
    with open("out.txt", "w") as fout:
        fout.write(fin.read())
print("after copying")

#5. contextlib.suppress vs bare try/except
from contextlib import suppress
result = {} # empty dict
with suppress(KeyError):
    print('inside with-suppress; access dict key, which does not exist')
    print(result['key'])
    print('error is suppressed')
'''
inside with-suppress; access dict key, which does not exist
'''

try:
    print('inside try; access dict key, which does not exist')
    print(result['no_key'])
except KeyError as e: 
    print(f'inside except; exception caught {e}')
'''
inside try; access dict key, which does not exist
inside except; exception caught 'no_key'
'''
'''
suppress(KeyError) vs try/except KeyError: pass -
behaviorally IDENTICAL once try/except is written correctly
real difference: suppress is harder to write wrong, clearer to read

forces you to name the exception type
   suppress(...) takes the type as its argument - no way to call it without one
   bare try/except doesn't force this - a lazy bare "except:" catches EVERYTHING
   (typos -> NameError, even KeyboardInterrupt) - suppress removes that shortcut

reads as intent, not as an empty gap
   "except KeyError: pass" - pass looks the same whether deliberate or forgotten TODO
   "with suppress(KeyError):" - the name itself says "ignoring a KeyError here"
   intent is visible in the first line, no need to infer from an empty block

less boilerplate for something this small
   try/except/pass = 3 lines of scaffolding around 1 line of real logic
   suppress(KeyError): result['key'] = 1 line total
   less to get subtly wrong (bad indentation, try block covering more than intended)

bottom line: not that suppress catches something try/except would miss
it's that suppress is harder to write carelessly, clearer to read at a glance
'''