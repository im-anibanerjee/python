import csv
import functools
import logging
import time 

from datetime import date, datetime

# import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class InvalidTransactionError(Exception):
    """ Raised when a CSV row can't be turned into a valid Transaction """
    pass

# from datetime import date
class Transaction:
    """ One validated transaction, parsed from a single CSV row """
    
    def __init__(self, txn_date: date, category: str, description: str, amount: float) -> None: 
        self.txn_date = txn_date
        self.category = category
        self.description = description
        self.amount = amount

    @classmethod
    def from_row(cls, row_number: int, row: dict) -> "Transaction":
        """ Build a Transaction from one CSV row; raises InvalidTransactionError if the row is invalid """

        raw_date = row.get('date', '')
        raw_category = row.get('category', '')
        raw_amount = row.get('amount', '')
        try:
            # takes a string (YYYY-MM-DD; iso format), returns a real date object.
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            raise InvalidTransactionError(f'row {row_number}: invalid date: {raw_date!r}')

        # strip() removes leading/trailing whitespace
        # if raw_category value exytracted is empty after strip
        if not raw_category.strip():
            raise InvalidTransactionError(f'row {row_number}: catgory is empty')

        try:
            parsed_amount = float(raw_amount)
        except ValueError:
            raise InvalidTransactionError(f'row {row_number}: invalid amount: {raw_amount!r}')
        
        return cls(parsed_date, raw_category, row.get('description', ''), parsed_amount)

# decorator
'''
import functools
import time
'''
def log_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f'{func.__name__} took {elapsed:.4f}sec')
        return result
    return wrapper

class TransactionLedger:
    """ Holds all loaded transactions and can summarize them """

    def __init__(self) -> None:
        self.transactions: list[Transaction] = []
        self.skipped_count: int = 0

    @log_execution_time
    def load_csv(self, path: str) -> None:
        """ Reads a csv file, keeps valid transactions, and skips/logs invalid rows """
        with open(path, newline='') as f:
            # import csv
            reader = csv.DictReader(f)
            for row_number, row in enumerate(reader, start=1): 
                try:
                    transaction = Transaction.from_row(row_number, row)
                except InvalidTransactionError as e:
                    logger.warning(str(e))
                    self.skipped_count += 1
                else:
                    self.transactions.append(transaction)

        logger.info(f'loaded {len(self.transactions)} transactions, skipped {self.skipped_count}')

    def total_income(self) -> float:
        """ Returns the sum of every positive (income) transaction amount """
        return sum(t.amount for t in self.transactions if t.amount > 0)

    def total_expenses(self) -> float:
        """ Returns the sum of every negative (expense) transaction amount """
        return sum(t.amount for t in self.transactions if t.amount < 0)

    def net(self) -> float:
        """ Returns total income plus total expenses, i.e. the overall balance """
        return self.total_income() + self.total_expenses()

    def by_category(self) -> dict:
        """ Returns a dict mapping each category to its total transaction amount """
        totals = {}
        for t in self.transactions:
            totals[t.category] = totals.get(t.category, 0.0) + t.amount
        return totals

    def filter_by_month(self, month: str) -> "TransactionLedger":
        """ Returns a new ledger containing only the transactions from the given month """
        filtered = TransactionLedger()
        filtered.transactions = [t for t in self.transactions if t.txn_date.strftime("%Y-%m") == month]
        filtered.skipped_count = self.skipped_count
        return filtered

# from datetime import date, datetime
class ReportWriter:
    """ Context manager: opens a report file, writes a header on entry, and 
    guarantees a footer is written on exit - even if the body raises """

    def __init__(self, path: str, title: str, transaction_count: int) -> None:
        self.path = path
        self.title = title
        self.transaction_count = transaction_count
        self.file = None

    def __enter__(self) -> 'ReportWriter':
        self.file = open(self.path, 'w')
        timestamp = datetime.now().isoformat(timespec='seconds')
        self.file.write(f'{self.title}\n')
        self.file.write(f'generated: {timestamp}\n')
        self.file.write('\n')
        return self

    def write_line(self, text: str) -> None:
        self.file.write(text + '\n')

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.file.write('\n')
        self.file.write(f'transactions considered {self.transaction_count}\n')
        self.file.write('-- end of report --\n')
        self.file.close()
        return False