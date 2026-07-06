import csv
import os
import zipfile

import pytest

from secret_santa.csv_io import (
    AssignmentCSVWriter,
    EmployeeCSVReader,
    PreviousAssignmentCSVReader,
)
from secret_santa.exceptions import CSVFormatError, DuplicateEmployeeError
from secret_santa.models import Assignment, Employee

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def write_xlsx(path, rows):
    def cell_reference(row_number, column_number):
        column_name = ""
        while column_number:
            column_number, remainder = divmod(column_number - 1, 26)
            column_name = chr(ord("A") + remainder) + column_name
        return f"{column_name}{row_number}"

    sheet_rows = []
    for row_number, row in enumerate(rows, start=1):
        cells = []
        for column_number, value in enumerate(row, start=1):
            reference = cell_reference(row_number, column_number)
            cells.append(
                f'<c r="{reference}" t="inlineStr"><is><t>{value}</t></is></c>'
            )
        sheet_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )

    with zipfile.ZipFile(path, "w") as workbook:
        workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)


class TestEmployeeCSVReader:
    def test_reads_valid_employees(self):
        reader = EmployeeCSVReader()
        employees = reader.read(os.path.join(FIXTURES_DIR, "employees.csv"))

        assert len(employees) == 5
        assert employees[0].name == "Alice Smith"
        assert employees[0].email == "alice@acme.com"

    def test_reads_valid_xlsx_employees(self, tmp_path):
        xlsx_path = tmp_path / "employees.xlsx"
        write_xlsx(
            xlsx_path,
            [
                ["Employee_Name", "Employee_EmailID"],
                ["Alice Smith", "alice@acme.com"],
                ["Bob Jones", "bob@acme.com"],
            ],
        )

        reader = EmployeeCSVReader()
        employees = reader.read(str(xlsx_path))

        assert [employee.name for employee in employees] == ["Alice Smith", "Bob Jones"]
        assert [employee.email for employee in employees] == ["alice@acme.com", "bob@acme.com"]

    def test_missing_file_raises(self):
        reader = EmployeeCSVReader()
        with pytest.raises(FileNotFoundError):
            reader.read(os.path.join(FIXTURES_DIR, "does_not_exist.csv"))

    def test_missing_column_raises(self, tmp_path):
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("Name,Email\nAlice,alice@acme.com\n")

        reader = EmployeeCSVReader()
        with pytest.raises(CSVFormatError):
            reader.read(str(bad_csv))

    def test_unsupported_file_type_raises(self, tmp_path):
        bad_file = tmp_path / "employees.txt"
        bad_file.write_text("Employee_Name,Employee_EmailID\nAlice,alice@acme.com\n")

        reader = EmployeeCSVReader()
        with pytest.raises(CSVFormatError):
            reader.read(str(bad_file))

    def test_empty_file_raises(self, tmp_path):
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("")

        reader = EmployeeCSVReader()
        with pytest.raises(CSVFormatError):
            reader.read(str(empty_csv))

    def test_duplicate_email_raises(self, tmp_path):
        dup_csv = tmp_path / "dup.csv"
        dup_csv.write_text(
            "Employee_Name,Employee_EmailID\n"
            "Alice,alice@acme.com\n"
            "Alice Duplicate,alice@acme.com\n"
        )

        reader = EmployeeCSVReader()
        with pytest.raises(DuplicateEmployeeError):
            reader.read(str(dup_csv))

    def test_invalid_row_raises_csv_format_error(self, tmp_path):
        bad_csv = tmp_path / "bad_row.csv"
        bad_csv.write_text(
            "Employee_Name,Employee_EmailID\n"
            ",missing-name@acme.com\n"
        )

        reader = EmployeeCSVReader()
        with pytest.raises(CSVFormatError):
            reader.read(str(bad_csv))


class TestPreviousAssignmentCSVReader:
    def test_reads_valid_previous_assignments(self):
        reader = PreviousAssignmentCSVReader()
        previous = reader.read(os.path.join(FIXTURES_DIR, "previous_assignments.csv"))

        assert previous["alice@acme.com"] == "bob@acme.com"
        assert previous["bob@acme.com"] == "carol@acme.com"
        assert len(previous) == 5

    def test_reads_valid_xlsx_previous_assignments(self, tmp_path):
        xlsx_path = tmp_path / "previous.xlsx"
        write_xlsx(
            xlsx_path,
            [
                [
                    "Employee_Name",
                    "Employee_EmailID",
                    "Secret_Child_Name",
                    "Secret_Child_EmailID",
                ],
                ["Alice Smith", "alice@acme.com", "Bob Jones", "bob@acme.com"],
            ],
        )

        reader = PreviousAssignmentCSVReader()
        previous = reader.read(str(xlsx_path))

        assert previous == {"alice@acme.com": "bob@acme.com"}

    def test_none_path_returns_empty_dict(self):
        reader = PreviousAssignmentCSVReader()
        assert reader.read(None) == {}

    def test_missing_file_raises(self):
        reader = PreviousAssignmentCSVReader()
        with pytest.raises(FileNotFoundError):
            reader.read(os.path.join(FIXTURES_DIR, "does_not_exist.csv"))


class TestAssignmentCSVWriter:
    def test_writes_expected_rows(self, tmp_path):
        alice = Employee(name="Alice Smith", email="alice@acme.com")
        bob = Employee(name="Bob Jones", email="bob@acme.com")
        assignments = [Assignment(giver=alice, child=bob)]

        output_path = tmp_path / "output.csv"
        writer = AssignmentCSVWriter()
        writer.write(str(output_path), assignments)

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert rows[0]["Employee_Name"] == "Alice Smith"
        assert rows[0]["Secret_Child_Name"] == "Bob Jones"

    def test_creates_missing_directories(self, tmp_path):
        alice = Employee(name="Alice Smith", email="alice@acme.com")
        bob = Employee(name="Bob Jones", email="bob@acme.com")
        assignments = [Assignment(giver=alice, child=bob)]

        nested_path = tmp_path / "nested" / "dir" / "output.csv"
        writer = AssignmentCSVWriter()
        writer.write(str(nested_path), assignments)

        assert nested_path.exists()
