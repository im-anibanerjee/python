#1. prove the level gate, yourself
import logging

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
q1_logger = logging.getLogger("q1_demo")

q1_logger.debug("debug msg")
q1_logger.info("info msg")
q1_logger.warning("warning msg")
q1_logger.error("error msg")
print("---")
'''
WARNING: warning msg
ERROR: error msg
---
'''
# only warning and error printed - basicConfig(level=logging.WARNING) means "only emit WARNING
# and above", so debug and info never even reach a handler, they get dropped at the logger
# level itself, before formatting or output ever happens


#2. two handlers, two different views of the same events
logger2 = logging.getLogger("multi_handler_demo")
logger2.setLevel(logging.DEBUG)   # the logger itself lets everything through
logger2.propagate = False   # keep this section isolated from question 1's root config above

console = logging.StreamHandler()
console.setLevel(logging.WARNING)   # console handler only wants WARNING+
console.setFormatter(logging.Formatter("CONSOLE %(levelname)s: %(message)s"))

file_handler = logging.FileHandler("app.log", mode="w")
file_handler.setLevel(logging.DEBUG)   # file handler wants everything
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))

logger2.addHandler(console)
logger2.addHandler(file_handler)

logger2.debug("debug message")
logger2.info("info message")
logger2.warning("warning message")
logger2.error("error message")
logger2.critical("critical message")
print("---")
'''
CONSOLE WARNING: warning message
CONSOLE ERROR: error message
CONSOLE CRITICAL: critical message
---
'''
# checked app.log separately - it has all 5:
'''
2026-... DEBUG: debug message
2026-... INFO: info message
2026-... WARNING: warning message
2026-... ERROR: error message
2026-... CRITICAL: critical message
'''
# console only shows 3 of the 5 (its own WARNING threshold), the file has all 5 (its own
# DEBUG threshold) - same logger, same 5 calls, two independent filters on the two handlers


#3. propagation, proven both ways
child = logging.getLogger("app.worker")
child.setLevel(logging.INFO)   # explicit, so this doesn't just inherit question 1's root WARNING
child.info("message from child - should reach root's handler with no handler config on child at all")
'''
INFO: message from child - should reach root's handler with no handler config on child at all
'''
# never attached a handler to "app.worker" directly - it propagated up to the root logger
# (configured once, at the very top of this file, by basicConfig) and printed using the
# root's own format string

child.propagate = False
child.info("message from child - should NOT appear now, propagation disabled")
print("(nothing printed above this line for the child logger means propagate=False worked)")
'''
(nothing printed above this line for the child logger means propagate=False worked)
'''
# propagate = False cuts the path up to the root logger's handler - "app.worker" has no
# handlers of its own, so with propagation off the message has nowhere left to go
