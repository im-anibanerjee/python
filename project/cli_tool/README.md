# Transaction Ledger CLI

A command-line tool that reads a CSV of bank-style transactions and produces spending reports from it.

## Commands

- `summary` - total income, total expenses, and net across every loaded transaction.
- `by-category` - the same totals, broken down per category, sorted by total spent (most negative first).
- `filter --month YYYY-MM` - same as summary, but restricted to transactions in a given month.

Each command reads a CSV, validates every row (skipping and logging any row with a bad date, bad amount, or empty category), and writes the result to a report file.

## How to run it

Run from inside this folder:

```
python -m pytest tests/test_ledger.py -v
python cli.py <command> --input <csv path> --report <output path> [--month YYYY-MM]
```

`--report` can point anywhere, including the `reports/` folder in this project.

## Example

```
python cli.py summary --input sample_data/transactions.csv --report reports/summary.txt
```

Terminal output:
```
WARNING: row 3: invalid date: '01-09-2026'
WARNING: row 4: catgory is empty
WARNING: row 5: invalid amount: 'abc'
INFO: loaded 2 transactions, skipped 3
INFO: load_csv took 0.0284sec
report written to reports/summary.txt
```

`reports/summary.txt`:
```
Transaction Ledger CLI
generated: 2026-09-20T16:18:07

total income: 2500.00
total expenses: -54.20
net: 2445.80

transactions considered 2
-- end of report --
```
