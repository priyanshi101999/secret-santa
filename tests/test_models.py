import pytest

from secret_santa.models import Assignment, Employee


class TestEmployee:
    def test_valid_employee(self):
        emp = Employee(name="Alice Smith", email="alice@acme.com")
        assert emp.name == "Alice Smith"
        assert emp.email == "alice@acme.com"

    def test_key_is_lowercased_email(self):
        emp = Employee(name="Alice", email="Alice@ACME.com")
        assert emp.key == "alice@acme.com"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            Employee(name="", email="alice@acme.com")

    def test_blank_name_raises(self):
        with pytest.raises(ValueError):
            Employee(name="   ", email="alice@acme.com")

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError):
            Employee(name="Alice", email="not-an-email")

    def test_empty_email_raises(self):
        with pytest.raises(ValueError):
            Employee(name="Alice", email="")


class TestAssignment:
    def test_as_row(self):
        giver = Employee(name="Alice Smith", email="alice@acme.com")
        child = Employee(name="Bob Jones", email="bob@acme.com")
        assignment = Assignment(giver=giver, child=child)

        assert assignment.as_row() == {
            "Employee_Name": "Alice Smith",
            "Employee_EmailID": "alice@acme.com",
            "Secret_Child_Name": "Bob Jones",
            "Secret_Child_EmailID": "bob@acme.com",
        }
