import argparse
import sys

from .assigner import SecretSantaAssigner
from .csv_io import AssignmentCSVWriter, EmployeeCSVReader, PreviousAssignmentCSVReader
from .exceptions import SecretSantaError


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Secret Santa assignments.")
    parser.add_argument(
        "--employees",
        required=True,
        help="CSV or XLSX file containing Employee_Name and Employee_EmailID.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Where to write the assignments CSV.",
    )
    parser.add_argument(
        "--previous",
        default=None,
        help="Last year's assignments CSV or XLSX file, if any.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for repeatable output.",
    )
    return parser


def run(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        employees = EmployeeCSVReader().read(args.employees)
        previous = PreviousAssignmentCSVReader().read(args.previous)
        assignments = SecretSantaAssigner(random_seed=args.seed).assign(employees, previous)
        AssignmentCSVWriter().write(args.output, assignments)

        print(f"Success: {len(assignments)} assignment(s) written to {args.output}")
        return 0

    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except SecretSantaError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
