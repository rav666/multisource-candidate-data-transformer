#!/usr/bin/env python3
"""
main.py — CLI for the Eightfold Multi-Source Candidate Data Transformer.

Usage examples:
  # Default schema, resume + CSV
  python main.py --resume path/to/resume.pdf --csv path/to/candidates.csv

  # With custom projection config
  python main.py --resume path/to/resume.pdf --csv path/to/candidates.csv \\
                 --config config_example.json

  # Resume only
  python main.py --resume path/to/resume.pdf

  # CSV only (row 0 by default)
  python main.py --csv path/to/candidates.csv --csv-row 0

  # Write output to a file instead of stdout
  python main.py --resume path/to/resume.pdf --output result.json
"""
import argparse
import json
import logging
import sys

from src.pipeline import Pipeline


def _build_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="Eightfold Multi-Source Candidate Data Transformer",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__
    )

    argument_parser.add_argument("--resume", metavar="PDF", help="Path to PDF resume.")
    argument_parser.add_argument("--csv", metavar="CSV", help="Path to recruiter CSV file.")
    argument_parser.add_argument(
        "--csv-row", metavar="N", type=int, default=0,
        help="Zero-based row index to use from the CSV (default: 0)."
    )

    argument_parser.add_argument("--config", metavar="JSON", help="Path to projection config JSON.")
    argument_parser.add_argument("--output", metavar="FILE", help="Write JSON output to FILE instead of stdout.", )
    argument_parser.add_argument("--pretty", action="store_true", default=True, help="Pretty-print JSON output (default: true).", )
    argument_parser.add_argument(
        "--log-level", default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: WARNING)."
    )

    return argument_parser


def main() -> int:
    args = _build_parser().parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s  %(name)s  %(message)s", )

    if not args.resume and not args.csv:
        print("Error: provide at least --resume or --csv.", file=sys.stderr)
        return 1

    try:
        result = Pipeline().run(
            resume_path=args.resume, csv_path=args.csv, config_path=args.config, csv_row_index=args.csv_row
        )

    except Exception as exc:
        print(f"Pipeline error: {exc}", file=sys.stderr)
        logging.exception("Unhandled pipeline exception")
        return 2

    indent = 2 if args.pretty else None
    json_output = json.dumps(result, indent=indent, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"Output written to {args.output}", file=sys.stderr)

    else:
        print(json_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
