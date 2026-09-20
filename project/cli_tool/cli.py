import argparse
from ledger import TransactionLedger, ReportWriter

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='cli.py', description='Transaction Ledger CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    summary_parser = subparsers.add_parser('summary')
    summary_parser.add_argument('--input', required=True)
    summary_parser.add_argument('--report', required=True)

    by_category_parser = subparsers.add_parser('by-category')
    by_category_parser.add_argument('--input', required=True)
    by_category_parser.add_argument('--report', required=True)

    filter_parser = subparsers.add_parser('filter')
    filter_parser.add_argument('--input', required=True)
    filter_parser.add_argument('--report', required=True)
    filter_parser.add_argument('--month', required=True)

    return parser

# from ledger import TransactionLedger, ReportWriter
def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    ledger = TransactionLedger()
    ledger.load_csv(args.input)

    if args.command == 'summary':
        with ReportWriter(args.report, 'Transaction Ledger CLI', len(ledger.transactions)) as report:
            report.write_line(f'total income: {ledger.total_income():.2f}')
            report.write_line(f'total expenses: {ledger.total_expenses():.2f}')
            report.write_line(f'net: {ledger.net():.2f}')

    elif args.command == 'by-category':
        totals = ledger.by_category()
        with ReportWriter(args.report, 'Transaction Ledger CLI', len(ledger.transactions)) as report:
            for category, total in sorted(totals.items(), key=lambda kv: kv[1]):
                report.write_line(f'{category}: {total:.2f}')

    elif args.command == 'filter':
        filtered = ledger.filter_by_month(args.month)
        with ReportWriter(args.report, 'Transaction Ledger CLI', len(filtered.transactions)) as report:
            report.write_line(f'total income: {filtered.total_income():.2f}')
            report.write_line(f'total expenses: {filtered.total_expenses():.2f}')
            report.write_line(f'net: {filtered.net():.2f}')

    print(f'report written to {args.report}')

if __name__ == '__main__':
    main()