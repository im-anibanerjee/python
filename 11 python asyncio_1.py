#1. Blocking vs non-blocking, side by side
# version 1: using simply await
import asyncio, time
async def fetch(url, delay):
    print(f'fetching url: {url}')
    await asyncio.sleep(delay)
    print(f'fetched url: {url}')
    return f'{url} done; '

async def main_awaitsequence():
    start = time.perf_counter()
    r1 = await fetch('a.com', 1)
    r2 = await fetch('b.com', 1)
    r3 = await fetch('c.com', 1)
    print(r1, r2, r3)
    print(f'time taken: {time.perf_counter()-start}')
asyncio.run(main_awaitsequence())
'''
fetching url: a.com
fetched url: a.com
fetching url: b.com
fetched url: b.com
fetching url: c.com
fetched url: c.com
a.com done;  b.com done;  c.com done; 
time taken: 3.0085628
'''
# version 2: using ayncio.gather()
async def main_asynciogather():
    start = time.perf_counter()
    result = await asyncio.gather(
        fetch("a.com", 1),
        fetch("b.com", 1),
        fetch("c.com", 1)
    )
    print(result)
    print(f'time taken: {time.perf_counter()-start}')
asyncio.run(main_asynciogather())
'''
fetching url: a.com
fetching url: b.com
fetching url: c.com
fetched url: a.com
fetched url: b.com
fetched url: c.com
['a.com done; ', 'b.com done; ', 'c.com done; ']
time taken: 0.9984445000000002
'''
print()

#2. Reproduce the time.sleep() bug on purpose 
import asyncio, time
async def fetch_timesleep(url, delay):
    print(f'fetching: {url}')
    time.sleep(delay)
    print(f'fetched: {url}')
    return f'{url} done'

async def fetch_awaitasynciosleep(url, delay):
    print(f'fetching: {url}')
    await asyncio.sleep(delay)
    print(f'fetched: {url}')
    return f'{url} done'

async def main_asynciogather_2():
    start = time.perf_counter()
    result = await asyncio.gather(
        fetch_timesleep("a.com", 1),
        fetch_timesleep("b.com", 1),
        fetch_timesleep("c.com", 1)
    )
    print(result)
    print(f'time taken: {time.perf_counter()-start}')
    '''
    fetching: a.com
    fetched: a.com
    fetching: b.com
    fetched: b.com
    fetching: c.com
    fetched: c.com
    ['a.com done', 'b.com done', 'c.com done']
    time taken: 3.0283676999999996
    '''
    start = time.perf_counter()
    result = await asyncio.gather(
        fetch_awaitasynciosleep("a.com", 1),
        fetch_awaitasynciosleep("b.com", 1),
        fetch_awaitasynciosleep("c.com", 1)
    )
    print(result)
    print(f'time taken: {time.perf_counter()-start}')
    '''
    fetching: a.com
    fetching: b.com
    fetching: c.com
    fetched: a.com
    fetched: b.com
    fetched: c.com
    ['a.com done', 'b.com done', 'c.com done']
    time taken: 1.0152687999999994
    '''
asyncio.run(main_asynciogather_2())
'''
time.sleep() freezes the whole event loop — nothing else can run while it waits
await asyncio.sleep() only pauses that one coroutine and hands control back, so other coroutines can keep going
'''

#3. create_task and doing something else in between
import asyncio
async def fetch(task_name, delay):
    print(f'starting task: {task_name}')
    print(f'adding sleep: {delay} on task: {task_name}')
    await asyncio.sleep(delay)
    print(f'{delay} sec crossed')
    print(f'resuming task: {task_name} after sleep: {delay}')
    print(f'task: {task_name} done')
    return f'task: {task_name} done'

async def main():
    task = asyncio.create_task(fetch('Ani', 2))
    print('still executing in main')
    print('adding sleep in main for 1')
    await asyncio.sleep(1)
    print('resuming main')
    '''
    still executing in main
    adding sleep in main for 1
    starting task: Ani
    adding sleep: 2 on task: Ani
    resuming main

    this is the output without: 'result = await task'
    '''
    result = await task
    '''
    still executing in main
    adding sleep in main for 1
    starting task: Ani
    adding sleep: 2 on task: Ani
    resuming main
    2 sec crossed
    resuming task: Ani after sleep: 2
    task: Ani done

    this is the output with: 'result = await task'
    '''
    print(result)
    '''
    still executing in main
    adding sleep in main for 1
    starting task: Ani
    adding sleep: 2 on task: Ani
    resuming main
    2 sec crossed
    resuming task: Ani after sleep: 2
    task: Ani done
    task: Ani done
    '''
asyncio.run(main())