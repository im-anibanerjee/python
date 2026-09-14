#4. 
import asyncio
async def greet(name):
    print(f'Hi {name}')
    return 'done'
result = greet('Ani')
print(result)
'''
<coroutine object greet at 0x000001D5DE59C2C0>
sys:1: RuntimeWarning: coroutine 'greet' was never awaited
'''
'''
calling greet() does not run the function body; it just builds a coroutine object, ready to run
same as calling a generator function: def gen(): yield 1; gen() also just builds a generator object, does not run anything
body only actually runs when something drives it forward; either await from inside another coroutine, or asyncio.run()
'''

#5. Order of completion vs. order passed in
import asyncio
async def fetch(name, delay):
    print(f'start task: {name}')
    print(f'sleep of {delay}s on task:{name}')
    await asyncio.sleep(delay)
    print(f'resume task:{name} after sleep of {delay}s')
    return f'task:{name} is done'

async def main():
    import time
    start = time.perf_counter()
    result = await asyncio.gather(
        fetch("a.com", 1),
        fetch("b.com", 2),
        fetch("c.com", 3)
    )
    print(result)
    print(f'time taken to execute all fetch: {time.perf_counter()-start}')

asyncio.run(main())
'''
start task: a.com
sleep of 1s on task:a.com
start task: b.com
sleep of 2s on task:b.com
start task: c.com
sleep of 3s on task:c.com
resume task:a.com after sleep of 1s
resume task:b.com after sleep of 2s
resume task:c.com after sleep of 3s
['task:a.com is done', 'task:b.com is done', 'task:c.com is done']
time taken to execute all fetch: 2.9958382
'''