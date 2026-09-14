#3. Reproduce the lost-update race, then fix it with a lock
import threading, time
count1 = 0
N = 10

def racy(name, delay):
    global count1
    print(f'start thread execution: {name}')
    for i in range(N):
        temp = count1
        time.sleep(delay)
        count1 = temp + 1

t1 = threading.Thread(target=racy, args=('t1', 1))
t2 = threading.Thread(target=racy, args=('t2', 1))
t1.start(); t2.start()
t1.join(); t2.join()
print(f'expected count: {N*2}; current count because of race: {count1}')
'''
start thread execution: t1
start thread execution: t2
(took some time before printing this)
expected count: 20; current count because of race: 10
'''

count2 = 0
lock = threading.Lock()
def locky(name, delay):
    global count2
    print(f'start thread execution: {name}')
    for i in range(N):
        with lock:
            temp = count2
            time.sleep(delay)
            count2 = temp + 1

t1 = threading.Thread(target=locky, args=('t1', 1))
t2 = threading.Thread(target=locky, args=('t2', 1))
t1.start(); t2.start()
t1.join(); t2.join()
print(f'expected count: {N*2}; current count because of lock: {count2}')
'''
start thread execution: t1
start thread execution: t2
expected count: 20; current count because of lock: 20
'''

#4. Explain it back, as a comment
'''
the GIL only guarantees one bytecode instruction runs at a time, not a whole sequence
temp = counter1 (READ) and counter1 = temp + 1 (WRITE) are two separate steps
and the GIL can switch threads in between them

time.sleep(delay) forces exactly that switch, on purpose
so both threads can READ the same stale value and WRITE back the same result 
one increment gets silently lost, even though only one thread was ever "running" at a time

with lock: fixes it not by changing the GIL, but by making READ+WRITE one indivisible unit 
no thread can start its READ until the other has finished its WRITE
'''

#5. Check your own installed Python
'''
checked which python is on PATH:
    $ python --version
    Python 3.9.0

ran the check script:
    $ python -c "import sys, sysconfig
    print('version:', sys.version)
    print('Py_GIL_DISABLED:', sysconfig.get_config_var('Py_GIL_DISABLED'))
    print('has _is_gil_enabled:', hasattr(sys, '_is_gil_enabled'))"

real output:
    version: 3.9.0 ...
    Py_GIL_DISABLED: None
    has _is_gil_enabled: False

expected - free-threading (PEP 703) only exists from 3.13 onward (3.13t/ 3.14t builds)
on 3.9 these symbols don't exist at all, not just "off"

a free-threaded 3.13t/3.14t build would show 
    Py_GIL_DISABLED: 1 and
    sys._is_gil_enabled() would exist, returning True/False.

if i reran Q1 there, i'd expect "2 threads" to stop matching "1 thread sequential" and 
drop close to "2 processes" instead - GIL actually off means two threads can run CPU-bound bytecode in true parallel
'''