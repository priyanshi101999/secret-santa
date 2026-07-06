import csv
import os

from secret_santa.main import run

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestMainCLI:
    def test_full_run_without_previous_history(self, tmp_path):
        output_path = tmp_path / "output.csv"
        exit_code = run(
            [
                "--employees", os.path.join(FIXTURES_DIR, "employees.csv"),
                "--output", str(output_path),
                "--seed", "7",
            ]
        )

        assert exit_code == 0
        assert output_path.exists()

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 5

    def test_full_run_with_previous_history(self, tmp_path):
        output_path = tmp_path / "output.csv"
        exit_code = run(
            [
                "--employees", os.path.join(FIXTURES_DIR, "employees.csv"),
                "--previous", os.path.join(FIXTURES_DIR, "previous_assignments.csv"),
                "--output", str(output_path),
                "--seed", "8",
            ]
        )

        assert exit_code == 0

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        previous_pairs = set()
        with open(
            os.path.join(FIXTURES_DIR, "previous_assignments.csv"), newline="", encoding="utf-8"
        ) as f:
            for row in csv.DictReader(f):
                previous_pairs.add((row["Employee_EmailID"], row["Secret_Child_EmailID"]))

        for row in rows:
            pair = (row["Employee_EmailID"], row["Secret_Child_EmailID"])
            assert pair not in previous_pairs
            assert row["Employee_EmailID"] != row["Secret_Child_EmailID"]

    def test_missing_employees_file_returns_error_code(self, tmp_path):
        output_path = tmp_path / "output.csv"
        exit_code = run(
            [
                "--employees", "does_not_exist.csv",
                "--output", str(output_path),
            ]
        )
        assert exit_code == 1
