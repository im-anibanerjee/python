#4. timeit a real before/after
import timeit

data_list = list(range(10000))
data_set = set(range(10000))

t_list = timeit.timeit(lambda: 9999 in data_list, number=1000)
t_set = timeit.timeit(lambda: 9999 in data_set, number=1000)

print(f"'in' on a list (10000 items): {t_list:.4f}s for 1000 checks")
print(f"'in' on a set (10000 items): {t_set:.4f}s for 1000 checks")
print(f"set is {t_list / t_set:.0f}x faster")
'''
'in' on a list (10000 items): 0.0468s for 1000 checks
'in' on a set (10000 items): 0.0000s for 1000 checks
set is 1252x faster
'''
# checking membership in a list has to walk the list one item at a time until it finds a
# match (or reaches the end) - worst case it checks all 10000 items, every single call
# a set is backed by a hash table, so membership is a direct lookup by hash - roughly
# constant time no matter how big the set is, which is why the gap is this dramatic


#5. cProfile a function with a hidden bottleneck
import cProfile
import time

def fetch_from_api():
    time.sleep(0.03)   # stands in for a real, slow network call
    return {"status": "ok"}

def compute_summary(n):
    total = 0
    for i in range(n):
        total += i * i
    return total

def handle_request():
    for _ in range(4):
        fetch_from_api()
        compute_summary(50000)

cProfile.run("handle_request()")
'''
         16 function calls in 0.131 seconds

   Ordered by: standard name

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.131    0.131 <string>:1(<module>)
        1    0.000    0.000    0.131    0.131 q5.py:14(handle_request)
        4    0.000    0.000    0.121    0.030 q5.py:4(fetch_from_api)
        4    0.010    0.002    0.010    0.002 q5.py:8(compute_summary)
        1    0.000    0.000    0.131    0.131 {built-in method builtins.exec}
        4    0.121    0.030    0.121    0.030 {built-in method time.sleep}
        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
'''
# compute_summary LOOKS like it should be the heavier one - it runs a real loop 50000 times,
# 4 times over, 200000 iterations total of actual arithmetic
# but its tottime is only 0.010s total
# fetch_from_api's own tottime is basically 0.000, but its cumtime is 0.121s, almost the
# entire runtime, because that's all time.sleep - which shows up as its own line with
# tottime 0.121
# the real bottleneck is time.sleep inside fetch_from_api, not the "busier-looking"
# compute_summary loop - exactly the point of profiling instead of guessing from how a
# function reads
