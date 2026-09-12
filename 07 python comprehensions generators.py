#1. Predict, then verify
def gen():
    print("start")
    x = yield 1
    print(f"received: {x}")
    yield 2

g = gen()
print(next(g))
print(next(g))
