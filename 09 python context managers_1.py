#1. Write a class-based context manager Timer
class Timer:
    def __enter__(self):
        import time
        self.start = time.perf_counter()
        print(f'execution starts at: {self.start}')
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        import time
        if exc_type is ValueError:
            print(f'inside __exit__; inside if; caught {exc_type}, value:{exc_value}, traceback: {exc_tb}')
            print(f'took time: {time.perf_counter()-self.start}')
            '''
            return True
            this means this exception is handled and will not propage
            so 'except Exception as e:' block in 'with Timer()' will not fire 
            and will not print: f'in try-except: caught {e}'
            so deliberately returning False, so that it is caught
            '''
            return False
        print(f'inside __exit__; outside if')
        print(f'took time: {time.perf_counter()-self.start}')
        return False

try:
    with Timer():
        raise ValueError("VALUE")
except Exception as e:
    print(f'in try-except: caught {e}')
'''
execution starts at: 0.0615625
inside __exit__; inside if; caught <class 'ValueError'>, value:VALUE, traceback: <traceback object at 0x00000293DA8FAF00>
took time: 0.0003140999999999977
in try-except: caught VALUE
'''

with Timer():
    sum = 0
    print(f'body inside with; sum: {sum}')
'''
execution starts at: 0.0619575
body inside with; sum: 0
inside __exit__; outside if
took time: 0.0002254000000000006
'''

#2. Write SuppressValueError-style class
class SuppressValueError:
    def __enter__(self):
        import time
        self.start = time.perf_counter()
        print(f'starts at: {self.start}')
        return self

    def __exit__(self, exc_type, exc, tb):
        import time
        if exc_type is ValueError:
            print(f'inside __exit__; inside if; caught {exc_type}, value:{exc}, traceback: {tb}; suppressing')
            print(f'took time: {time.perf_counter()-self.start}')
            return True
        elif exc_type is FileNotFoundError:
        # elif exc_type is not ValueError:
            '''
            this block:  print(f'no exception') 
            was also getting into this condition because of: elif exc_type is not ValueError: (earlier)
            so changed to: elif exc_type is FileNotFoundError: (later) 
            '''
            print(f'inside __exit__; inside elif')
            print(f'exception caught: {exc_type}; not suppressing')
            print(f'took time: {time.perf_counter()-self.start}')
            '''
            have to return False here
            or else 'print(f'no exception check')...' block will continue to run
            which is not what i intend while experimenting with this question solution
            '''
            return False
        print(f'no exception check')
        print(f'took time: {time.perf_counter()-self.start}')
        return False

for count in range(1, 4):
    try:
        with SuppressValueError():
            if count==1:
                print(f'suppressing check')
                raise ValueError("VALUE")
                '''
                starts at: 0.0512246
                suppressing check
                inside __exit__; inside if; caught <class 'ValueError'>, value:VALUE, traceback: <traceback object at 0x00000220E7ACC840>; suppressing
                took time: 0.00026099999999999735
                '''
            elif count==2:
                print(f'not suppressing check')
                raise FileNotFoundError("file not found")
                '''
                starts at: 0.0515271
                not suppressing check
                inside __exit__; inside elif
                exception caught: <class 'FileNotFoundError'>; not suppressing
                took time: 0.00015369999999999967
                in try-except: caught file not found
                '''
            else: 
                print(f'no exception')
                ''' 
                starts at: 0.0519149
                no exception
                no exception check
                took time: 0.00017380000000000173
                '''     
    except Exception as e:
        print(f'in try-except: caught {e}')

print('execution completed')    # execution completed
