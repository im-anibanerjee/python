#3. Parameterized decorator 
# could not solve; took help (IMP)
'''
def retry(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(times):
                result = func(*args, **kwargs)
                # result;
                # this prints 'Hi, Ani' once
            return result
            # only here it prints 3 times
        return wrapper
    return decorator

@retry(3)
def greetings(str):
    """greets hi"""
    print(f"Hi, {str}")

greetings("Ani")
'''
def retry(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(times):
                try:
                    result = func(*args, **kwargs)
                    return result       # succeeded — stop immediately, don't try again
                except Exception as e:
                    last_exception = e  # remember it, then let the loop continue
            raise last_exception        # only reached if EVERY attempt failed
        return wrapper
    return decorator


# --- the flaky test function, using a closure counter ---
def make_flaky():
    calls = 0
    def flaky():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError(f"attempt {calls} failed")
        print(f"succeeded on attempt {calls}")
        return "done"
    return flaky

flaky = make_flaky()
flaky_with_retry = retry(3)(flaky)     # same as @retry(3) applied manually
print(flaky_with_retry())
'''
Q: what is make_flaky/flaky doing?
make_flaky = factory, builds+returns a fresh flaky function, each with its own private counter
calls = 0 = the counter, lives inside make_flaky
flaky = inner function, called later, bumps calls by 1 each run, fails/succeeds based on count
nonlocal calls = lets flaky read/write make_flaky's calls, instead of creating a new local one

Q: why can't we just call flaky() directly - why need make_flaky() at all?
retry calls func() up to 3 times - each call is independent
a plain memoryless function behaves identically every call (always fails, or always succeeds)
to simulate "fails twice, succeeds on 3rd" the function must know WHICH call this is
only way a no-arg function can know that = remembering something across calls -> needs state
make_flaky() exists purely to give flaky that memory - a test double, not part of retry itself

Q: why not skip make_flaky, use a plain/global counter instead?
could use a global calls + `global calls` inside flaky - works, but shared across the whole script
a second test run would start from the leftover value, not 0 - tests contaminate each other
make_flaky() gives each flaky its OWN counter - isolated, reusable, no global mess

Q: doesn't make_flaky() also run multiple times? why does calls go 0->1->2->3 instead of resetting?
NO - make_flaky() runs ONCE only, at "flaky = make_flaky()"
that one call creates calls=0 once, builds + returns ONE flaky object
retry's loop then calls THAT SAME flaky object repeatedly (up to 3x) - never re-runs make_flaky()
same object -> same closure -> same calls variable -> keeps climbing 1,2,3 instead of resetting

contrast - IF retry instead called make_flaky()() fresh on every attempt:
  attempt0: make_flaky()() -> brand-new calls=0 -> becomes 1 -> raises
  attempt1: make_flaky()() -> ANOTHER brand-new calls=0 -> becomes 1 again -> raises again
  (would fail forever - this is NOT what the real code does)

Q: nonlocal - why is it needed?
python scans a function's whole body first; any name assigned to (calls += 1 counts) = assumed LOCAL
without nonlocal: calls += 1 tries to read local calls before it's assigned -> UnboundLocalError
nonlocal calls = override: use the enclosing function's calls, not a new local one
(global = same idea, but reaches module-level variables instead of an enclosing function's)

full trace of flaky_with_retry():
attempt0: func()->flaky(): calls 0->1, 1<3 True  -> raise -> caught, last_exception set
attempt1: func()->flaky(): calls 1->2, 2<3 True  -> raise -> caught, last_exception overwritten
attempt2: func()->flaky(): calls 2->3, 3<3 False -> prints success, return "done"
          wrapper: result = "done" -> returns immediately, loop stops early
output: succeeded on attempt 3
        done
'''