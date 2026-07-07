# Secret Santa

A small Python script for generating Secret Santa assignments from an employee list.

It reads the current employee list and writes a CSV where:

- nobody gets themselves
- everyone is assigned exactly once
- nobody gets the same Secret Child they had in the previous-year result file

The employer-provided `sample_data/Secret-Santa-Game-Result-2023.xlsx` file is
used as the previous-year assignment history.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate the virtualenv with:

```bash
source venv/bin/activate
```

## Run

```bash
python -m secret_santa.main --employees sample_data/employees.csv --previous sample_data/Secret-Santa-Game-Result-2023.xlsx --output output/assignments.csv
```

You can also pass the provided `.xlsx` file with the same column names:

```bash
python -m secret_santa.main --employees "Employee-List.xlsx" --output output/assignments.csv
```

You can replace the previous-year file with another CSV or XLSX file:

```bash
python -m secret_santa.main ^
  --employees sample_data/employees.csv ^
  --previous previous_assignments.csv ^
  --output output/assignments.csv
```

Add `--seed 42` if you want the same output each time while testing.

## File Format

CSV and XLSX inputs use the same column names. The output is always CSV.

Employee file:

```csv
Employee_Name,Employee_EmailID
Alice Smith,alice@acme.com
```

Previous assignment file:

```csv
Employee_Name,Employee_EmailID,Secret_Child_Name,Secret_Child_EmailID
Alice Smith,alice@acme.com,Bob Jones,bob@acme.com
```

The output uses the same columns as the previous assignment file.

## Tests

```bash
pytest
```

## Docker

In Git Bash, run these commands one by one:

```bash
docker build -t secret-santa .
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W)/output:/app/output" secret-santa
```
