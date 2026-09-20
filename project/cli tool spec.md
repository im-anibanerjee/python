# Wknd 1-3 capstone: Transaction Ledger CLI — assignment spec

This is the "exam question" for the capstone that closes out Wknd 1-3. It says what the tool must do and how it will be judged - it does not say how to write the code. That part happens live, piece by piece, in chat, with a separate build-notes file logging each piece (code, explanation, and the real questions/answers from our back-and-forth) as we go, per what we agreed on. This spec stays fixed once you're happy with it - if we discover mid-build that something here needs to change, that's a deliberate decision we make together, not a quiet drift.

## What it is, in one sentence

A command-line tool that reads a CSV of bank-style transactions and produces spending reports from it - a small, real version of the "transactions" concept that Wknd 4-5 (SQL) and Wknd 6-7 (FastAPI) both build on later, so this isn't a throwaway exercise.

## Where it lives

New folder in the existing repo: `D:\interview prep\python\cli-tool\`. Work is committed and pushed directly to `main` on the existing GitHub repo - no feature branch or PR for this project (changed from the original plan; see "Definition of done" below).

Planned file layout (kept deliberately small - this is your first real multi-file project, not a package with ten modules):
```
cli-tool/
  ledger.py           # Transaction, InvalidTransactionError, log_execution_time, ReportWriter, TransactionLedger
  cli.py              # command-line entry point (argparse)
  tests/
    test_ledger.py    # pytest suite
  sample_data/
    transactions.csv  # small sample file to run the tool against
  README.md
```

## The concepts this build must genuinely use (not just mention)

- **Class-based design** - a `Transaction` class representing one row, and a `TransactionLedger` class that holds a list of transactions and knows how to summarize them. Not everything needs to be a class (a plain function is often the right call, per the args/kwargs doc) - only these two things, because they genuinely have state and behavior worth bundling together.
- **Custom exception** - `InvalidTransactionError`, raised when a CSV row is genuinely malformed (see validation rules below). Real error handling, not decoration.
- **A decorator** - `@log_execution_time`, wrapping the function that loads and parses the whole CSV, logging (via the `logging` module, not `print`) how long loading took.
- **A context manager** - `ReportWriter`, responsible for opening the output report file, writing a header when entered, and guaranteeing a footer gets written on the way out - even if something goes wrong while the report body is being written. This is the same guarantee doc `09 python context managers.md` covers (`__exit__` runs regardless of whether the `with` block raised).
- **pytest tests** - covering: `Transaction` parsing a good row correctly; `Transaction` raising `InvalidTransactionError` on each kind of bad row; `TransactionLedger`'s summarizing logic (totals, category breakdown, month filtering) against a small known set of transactions; and a test proving `ReportWriter`'s footer is written even when the body-writing step raises.
- **README.md** - what the tool does, how to run it, one example command and its output.
- **A real commit and push** - to `main` on your actual GitHub repo, not simulated.

## Input format

A CSV with a header row and these columns:

```
date,category,description,amount
2026-09-01,groceries,Big Bazaar,-54.20
2026-09-03,salary,September salary,2500.00
2026-09-05,rent,September rent,-800.00
2026-09-10,groceries,Corner store,-12.75
2026-09-15,entertainment,Movie tickets,-18.00
```

- `date` - `YYYY-MM-DD`.
- `category` - free text, non-empty (e.g. `groceries`, `rent`, `salary`, `entertainment`).
- `description` - free text, may be empty.
- `amount` - a number; negative means money out (an expense), positive means money in (income) - the same convention a real bank statement export uses.

## What makes a row invalid (this is what `InvalidTransactionError` is for)

A row is invalid, and must raise `InvalidTransactionError`, if any of:
- `date` isn't a valid `YYYY-MM-DD` date.
- `amount` isn't a valid number.
- `category` is empty or missing.

`TransactionLedger`'s CSV-loading step must catch this per row, **skip that row, log a warning naming the row number and the reason**, and keep going - one bad row must never crash the whole load. At the end, the load logs how many rows were loaded successfully and how many were skipped.

## Required commands

Run as `python cli.py <command> --input <csv path> --report <output path> [options]`.

- `summary` - total income, total expenses, and net (income + expenses) across every loaded transaction.
- `by-category` - the same totals, broken down per category, sorted by total spent (most negative first).
- `filter --month YYYY-MM` - same as `summary`, but restricted to transactions in the given month.

Every command writes its result to the `--report` file via `ReportWriter` (header: tool name + generation timestamp; body: the actual numbers; footer: total transaction count considered + "-- end of report --"), and also prints a short confirmation to the terminal (e.g. `report written to report.txt`).

## Definition of done

- All three commands run against `sample_data/transactions.csv` and produce a sensible report file.
- Deliberately feeding it a CSV with at least one bad row (bad date, bad amount, empty category - one of each) proves: the bad rows are skipped and logged, the good rows are still processed correctly, and nothing crashes.
- `pytest` passes, covering everything listed above, and you can explain what each test is actually checking and why.
- `README.md` accurately describes how to run it, with one real example.
- The work is committed and pushed directly to `main` on your GitHub repo.

## What happens next

We build this piece by piece, live, starting with the `Transaction` class and `InvalidTransactionError` together (since the exception only makes sense once you can see what it's protecting). Nothing here is written until we've walked through it together in chat and you've typed it yourself.
