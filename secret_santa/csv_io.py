import csv
import os
import re
import zipfile
from xml.etree import ElementTree
from typing import Dict, List, Tuple

from .exceptions import CSVFormatError, DuplicateEmployeeError
from .models import Assignment, Employee

EMPLOYEE_COLUMNS = ("Employee_Name", "Employee_EmailID")
PREVIOUS_ASSIGNMENT_COLUMNS = (
    "Employee_Name",
    "Employee_EmailID",
    "Secret_Child_Name",
    "Secret_Child_EmailID",
)


class EmployeeCSVReader:
    def read(self, filepath: str) -> List[Employee]:
        rows = _read_rows(filepath, required_columns=EMPLOYEE_COLUMNS)

        employees: List[Employee] = []
        seen_emails: Dict[str, str] = {}

        for line_no, row in rows:
            name = row["Employee_Name"].strip()
            email = row["Employee_EmailID"].strip()
            try:
                employee = Employee(name=name, email=email)
            except ValueError as exc:
                raise CSVFormatError(f"{filepath}, line {line_no}: {exc}") from exc

            if employee.key in seen_emails:
                raise DuplicateEmployeeError(
                    f"{filepath}, line {line_no}: duplicate employee email "
                    f"'{employee.email}' (already seen for '{seen_emails[employee.key]}')"
                )
            seen_emails[employee.key] = employee.name
            employees.append(employee)

        return employees


class PreviousAssignmentCSVReader:
    def read(self, filepath: str) -> Dict[str, str]:
        if not filepath:
            return {}

        rows = _read_rows(filepath, required_columns=PREVIOUS_ASSIGNMENT_COLUMNS)

        previous: Dict[str, str] = {}
        for line_no, row in rows:
            giver_email = row["Employee_EmailID"].strip().lower()
            child_email = row["Secret_Child_EmailID"].strip().lower()
            if not giver_email or not child_email:
                raise CSVFormatError(
                    f"{filepath}, line {line_no}: missing email in previous assignment row"
                )
            previous[giver_email] = child_email

        return previous


class AssignmentCSVWriter:
    def write(self, filepath: str, assignments: List[Assignment]) -> None:
        directory = os.path.dirname(os.path.abspath(filepath))
        os.makedirs(directory, exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PREVIOUS_ASSIGNMENT_COLUMNS)
            writer.writeheader()
            for assignment in assignments:
                writer.writerow(assignment.as_row())


def _read_rows(filepath: str, required_columns: Tuple[str, ...]):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    extension = os.path.splitext(filepath)[1].lower()
    if extension == ".csv":
        return _read_csv_rows(filepath, required_columns)
    if extension == ".xlsx":
        return _read_xlsx_rows(filepath, required_columns)

    raise CSVFormatError(f"{filepath}: unsupported file type '{extension}'. Use .csv or .xlsx.")


def _read_csv_rows(filepath: str, required_columns: Tuple[str, ...]):
    try:
        with open(filepath, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                raise CSVFormatError(f"{filepath}: file is empty or has no header row")

            _validate_required_columns(filepath, reader.fieldnames, required_columns)
            return list(enumerate(reader, start=2))
    except csv.Error as exc:
        raise CSVFormatError(f"{filepath}: malformed CSV ({exc})") from exc


def _read_xlsx_rows(filepath: str, required_columns: Tuple[str, ...]):
    try:
        with zipfile.ZipFile(filepath) as workbook:
            shared_strings = _read_shared_strings(workbook)
            sheet_xml = workbook.read("xl/worksheets/sheet1.xml")
    except KeyError as exc:
        raise CSVFormatError(f"{filepath}: workbook is missing required sheet data") from exc
    except zipfile.BadZipFile as exc:
        raise CSVFormatError(f"{filepath}: malformed XLSX file") from exc

    rows = _parse_xlsx_sheet(sheet_xml, shared_strings)
    if not rows:
        raise CSVFormatError(f"{filepath}: file is empty or has no header row")

    headers = rows[0]
    _validate_required_columns(filepath, headers, required_columns)

    parsed_rows = []
    for index, row_values in enumerate(rows[1:], start=2):
        row = {
            header: row_values[position] if position < len(row_values) else ""
            for position, header in enumerate(headers)
        }
        parsed_rows.append((index, row))

    return parsed_rows


def _read_shared_strings(workbook: zipfile.ZipFile) -> List[str]:
    try:
        shared_xml = workbook.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ElementTree.fromstring(shared_xml)
    strings = []

    for item in root.findall("main:si", namespace):
        text_parts = [node.text or "" for node in item.findall(".//main:t", namespace)]
        strings.append("".join(text_parts))

    return strings


def _parse_xlsx_sheet(sheet_xml: bytes, shared_strings: List[str]) -> List[List[str]]:
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ElementTree.fromstring(sheet_xml)
    parsed_rows = []

    for row in root.findall(".//main:sheetData/main:row", namespace):
        values_by_column: Dict[int, str] = {}
        for cell in row.findall("main:c", namespace):
            cell_reference = cell.attrib.get("r", "")
            column_index = _column_index(cell_reference)
            values_by_column[column_index] = _cell_value(cell, shared_strings, namespace)

        if values_by_column:
            max_column = max(values_by_column)
            parsed_rows.append([values_by_column.get(index, "") for index in range(max_column + 1)])

    return parsed_rows


def _cell_value(cell, shared_strings: List[str], namespace: Dict[str, str]) -> str:
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", namespace)).strip()

    value_node = cell.find("main:v", namespace)
    if value_node is None or value_node.text is None:
        return ""

    value = value_node.text
    if cell_type == "s":
        try:
            return shared_strings[int(value)].strip()
        except (IndexError, ValueError) as exc:
            raise CSVFormatError("XLSX contains an invalid shared string reference") from exc

    return value.strip()


def _column_index(cell_reference: str) -> int:
    match = re.match(r"([A-Z]+)", cell_reference.upper())
    if not match:
        return 0

    index = 0
    for char in match.group(1):
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def _validate_required_columns(
    filepath: str,
    fieldnames: Tuple[str, ...] | List[str],
    required_columns: Tuple[str, ...],
) -> None:
    missing = [col for col in required_columns if col not in fieldnames]
    if missing:
        raise CSVFormatError(f"{filepath}: missing required column(s): {', '.join(missing)}")
