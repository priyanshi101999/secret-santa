import random
from typing import Dict, List, Optional

from .exceptions import AssignmentImpossibleError, InsufficientEmployeesError
from .models import Assignment, Employee

MIN_EMPLOYEES = 2


class SecretSantaAssigner:
    def __init__(self, max_attempts: int = 1000, random_seed: Optional[int] = None):
        self._max_attempts = max_attempts
        self._rng = random.Random(random_seed)

    def assign(
        self,
        employees: List[Employee],
        previous_assignments: Optional[Dict[str, str]] = None,
    ) -> List[Assignment]:
        previous_assignments = previous_assignments or {}

        if len(employees) < MIN_EMPLOYEES:
            raise InsufficientEmployeesError(
                f"Secret Santa needs at least {MIN_EMPLOYEES} employees; got {len(employees)}."
            )

        for _ in range(self._max_attempts):
            pairs = self._try_backtracking_assignment(employees, previous_assignments)
            if pairs is not None:
                return [Assignment(giver=giver, child=child) for giver, child in pairs.items()]

        raise AssignmentImpossibleError(
            "Could not find a valid assignment. The previous-year restrictions may be too tight."
        )

    def _try_backtracking_assignment(
        self,
        employees: List[Employee],
        previous_assignments: Dict[str, str],
    ) -> Optional[Dict[Employee, Employee]]:
        givers = list(employees)
        self._rng.shuffle(givers)

        pairs: Dict[Employee, Employee] = {}
        used_children: set = set()

        def backtrack(index: int) -> bool:
            if index == len(givers):
                return True

            giver = givers[index]
            candidates = [e for e in employees if e.key != giver.key and e.key not in used_children]
            self._rng.shuffle(candidates)

            previous_child_email = previous_assignments.get(giver.key)

            for candidate in candidates:
                if candidate.key == previous_child_email:
                    continue

                pairs[giver] = candidate
                used_children.add(candidate.key)

                if backtrack(index + 1):
                    return True

                del pairs[giver]
                used_children.discard(candidate.key)

            return False

        if backtrack(0):
            return pairs
        return None
