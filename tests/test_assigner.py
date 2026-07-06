import pytest

from secret_santa.assigner import SecretSantaAssigner
from secret_santa.exceptions import AssignmentImpossibleError, InsufficientEmployeesError
from secret_santa.models import Employee


def make_employees(n):
    return [Employee(name=f"Employee {i}", email=f"emp{i}@acme.com") for i in range(n)]


class TestSecretSantaAssigner:
    def test_no_self_assignment(self):
        employees = make_employees(6)
        assigner = SecretSantaAssigner(random_seed=1)
        assignments = assigner.assign(employees)

        for assignment in assignments:
            assert assignment.giver.key != assignment.child.key

    def test_each_employee_assigned_exactly_once_as_giver(self):
        employees = make_employees(8)
        assigner = SecretSantaAssigner(random_seed=2)
        assignments = assigner.assign(employees)

        giver_keys = [a.giver.key for a in assignments]
        assert sorted(giver_keys) == sorted(e.key for e in employees)

    def test_each_employee_assigned_exactly_once_as_child(self):
        employees = make_employees(8)
        assigner = SecretSantaAssigner(random_seed=3)
        assignments = assigner.assign(employees)

        child_keys = [a.child.key for a in assignments]
        assert sorted(child_keys) == sorted(e.key for e in employees)

    def test_respects_previous_year_assignments(self):
        employees = make_employees(5)
        previous = {
            employees[0].key: employees[1].key,
            employees[1].key: employees[2].key,
            employees[2].key: employees[3].key,
            employees[3].key: employees[4].key,
            employees[4].key: employees[0].key,
        }

        assigner = SecretSantaAssigner(random_seed=4)
        assignments = assigner.assign(employees, previous)

        for assignment in assignments:
            assert previous.get(assignment.giver.key) != assignment.child.key

    def test_too_few_employees_raises(self):
        employees = make_employees(1)
        assigner = SecretSantaAssigner()
        with pytest.raises(InsufficientEmployeesError):
            assigner.assign(employees)

    def test_empty_employees_raises(self):
        assigner = SecretSantaAssigner()
        with pytest.raises(InsufficientEmployeesError):
            assigner.assign([])

    def test_two_employees_without_history_works(self):
        employees = make_employees(2)
        assigner = SecretSantaAssigner(random_seed=5)
        assignments = assigner.assign(employees)

        assert len(assignments) == 2
        assert assignments[0].giver.key != assignments[0].child.key

    def test_two_employees_with_full_history_is_impossible(self):
        # With only 2 people, if last year's pairing already used the only
        # possible non-self pairing in both directions, no valid assignment exists.
        employees = make_employees(2)
        previous = {
            employees[0].key: employees[1].key,
            employees[1].key: employees[0].key,
        }
        assigner = SecretSantaAssigner(max_attempts=50)
        with pytest.raises(AssignmentImpossibleError):
            assigner.assign(employees, previous)

    def test_reproducible_with_same_seed(self):
        employees = make_employees(10)
        assigner_a = SecretSantaAssigner(random_seed=42)
        assigner_b = SecretSantaAssigner(random_seed=42)

        result_a = {a.giver.key: a.child.key for a in assigner_a.assign(employees)}
        result_b = {a.giver.key: a.child.key for a in assigner_b.assign(employees)}

        assert result_a == result_b
