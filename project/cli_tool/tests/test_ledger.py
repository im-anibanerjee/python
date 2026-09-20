import pytest
from datetime import date

from ledger import Transaction, InvalidTransactionError, TransactionLedger, ReportWriter

def test_transaction_from_row_valid():
    """ A well-formed row builds a transaction with all fields parsed correctly """
    row = {'date': '2026-09-01', 'category': 'groceries', 'description': 'Big Bazaar', 'amount': '-54.20'}
    txn = Transaction.from_row(1, row)
    assert txn.category == 'groceries'
    assert txn.amount == -54.20
    assert txn.description == 'Big Bazaar'
    assert str(txn.txn_date) == '2026-09-01'

def test_transaction_from_row_bad_date():
    """ A row with an invalid date raises InvalidTransactionError """
    row = {'date': '01-09-2026', 'category': 'groceries', 'description': '', 'amount': '-10'}
    with pytest.raises(InvalidTransactionError):
        Transaction.from_row(1, row)

def test_transaction_from_row_empty_category():
    """ A row with a blank or whitespace-only category raises InvalidTransactionError """
    row = {'date': '2026-09-01', 'category': '   ', 'description': '', 'amount': '-10'}
    with pytest.raises(InvalidTransactionError):
        Transaction.from_row(1, row)

def test_transaction_from_row_bad_amount():
    """ A row with a non-numeric amount raises InvalidTransactionError """
    row = {'date': '2026-09-01', 'category': 'groceries', 'description': '', 'amount': 'abc'}
    with pytest.raises(InvalidTransactionError):
        Transaction.from_row(1, row)

def test_ledger_totals_and_category_breakdown():
    """ total_income, total_expenses, net, and by_category are correct for a known set of transactions """
    ledger = TransactionLedger()
    ledger.transactions = [
        Transaction(date(2026, 9, 1), 'groceries', 'Big Bazaar', -54.20),
        Transaction(date(2026, 9, 3), 'salary', 'September salary', 2500.00),
        Transaction(date(2026, 9, 5), 'rent', 'September rent', -800.00),
        Transaction(date(2026, 10, 1), 'groceries', 'October shop', -30.00),
    ]

    assert ledger.total_income() == 2500.00
    assert ledger.total_expenses() == -884.20
    assert ledger.net() == 1615.80
    assert ledger.by_category() == {
        'groceries': -84.20,
        'salary': 2500.00,
        'rent': -800.00,
    }

def test_ledger_filter_by_month():
    """ Filter_by_month returns only the transactions from the given month, unchanged otherwise """
    ledger = TransactionLedger()
    ledger.transactions = [
        Transaction(date(2026, 9, 1), 'groceries', 'Big Bazaar', -54.20),
        Transaction(date(2026, 9, 3), 'salary', 'September salary', 2500.00),
        Transaction(date(2026, 10, 1), 'groceries', 'October shop', -30.00),
    ]

    september = ledger.filter_by_month('2026-09')
    assert len(september.transactions) == 2
    assert all(t.txn_date.strftime('%Y-%m') == '2026-09' for t in september.transactions)

def test_report_writer_footer_written_even_if_body_raises(tmp_path):
    """ ReportWriter's footer is written even when the body-writing step raises """
    report_path = tmp_path/'report.txt'

    with pytest.raises(ValueError):
        with ReportWriter(str(report_path), 'demo report', 3) as report:
            report.write_line('some body line')
            raise ValueError('something went wrong mid-body')

    contents = report_path.read_text()
    assert 'transactions considered 3' in contents
    assert '-- end of report --' in contents