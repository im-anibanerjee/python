#1. Reproduce the CPU-bound non-speedup, and the multiprocessing fix, yourself
import time, threading, multiprocessing
N = -20
def counter(n):
    while n<0:
        n += 1

if __name__ == "__main__":
    # 1 call; 1 thread
    start = time.perf_counter()
    counter(N)
    print(f'1 call; 1 thread; time taken: {time.perf_counter()-start:.2f}')
    # 1 call; 1 thread; time taken: 0.00

    # 2 call sequential; 1 thread
    start = time.perf_counter()
    counter(N); counter(N)
    print(f'2 call; 1 thread; time taken: {time.perf_counter()-start:.2f}')
    # 2 call; 1 thread; time taken: 0.00

    # 2 call; 2 threads
    start = time.perf_counter()
    # t1 = threading.Thread(target=counter, args=(N)) or threading.Thread(target=counter, args=N)
    # this will raise error, have to give args as tuple; have to give (N, )
    t1 = threading.Thread(target=counter, args=(N,))
    t2 = threading.Thread(target=counter, args=(N,))
    t1.start(); t2.start()
    t1.join(); t2.join()
    print(f'2 call; 1 thread; time taken: {time.perf_counter()-start:.2f}')
    # 2 call; 1 thread; time taken: 0.00

    # 2 calls; 2 process
    start = time.perf_counter()
    mp1 = multiprocessing.Process(target=counter, args=(N,))
    mp2 = multiprocessing.Process(target=counter, args=(N,))
    mp1.start(); mp2.start()
    mp1.join(); mp2.join()
    print(f'2 call; 2 process; time taken: {time.perf_counter()-start:.2f}')
    # 2 call; 2 process; time taken: 0.15

#2. Reproduce the I/O-bound speedup
import time, threading
def fetch(name, delay):
    print(f'starting task: {name}; going to sleep for {delay}s')
    time.sleep(delay)
    print(f'resuming after sleep; task:{name} is done')

if __name__ == "__main__":
    start = time.perf_counter()
    fetch('a', 1); fetch('b', 2); fetch('c', 3)
    print(f'sequential execution, time taken: {time.perf_counter()-start}')
    '''
    starting task: a; going to sleep for 1s
    resuming after sleep; task:a is done
    starting task: b; going to sleep for 2s
    resuming after sleep; task:b is done
    starting task: c; going to sleep for 3s
    resuming after sleep; task:c is done
    sequential execution, time taken: 6.0283513
    '''
    start = time.perf_counter()
    tasks = ['a', 'b', 'c', 'd']
    delays = [1, 2, 3]
    threads = [threading.Thread(target=fetch, args=(task, delay)) for task, delay in zip(tasks, delays)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f'thread execution, time taken: {time.perf_counter()-start}')
    '''
    starting task: a; going to sleep for 1s
    starting task: b; going to sleep for 2s
    starting task: c; going to sleep for 3s
    resuming after sleep; task:a is done
    resuming after sleep; task:b is done
    resuming after sleep; task:c is done
    thread execution, time taken: 3.0087596000000003
    '''
'''
if __name__ == "__main__" needed here because of multiprocessing.

Process -on windows there's no fork
so a new process re-imports this whole file from scratch just to get the counter function

without the guard, that re-import would hit mp1.start()/mp2.start() again
    spawning another process, 
    which imports again... 

python detects this and raises RuntimeError
wrapping it in if __name__ == "__main__": means that part only runs in the real, originally launched process, not during a re-import
'''