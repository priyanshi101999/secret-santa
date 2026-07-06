from dataclasses import dataclass


@dataclass(frozen=True)
class Employee:
    name: str
    email: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Employee name cannot be empty.")
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email address for employee '{self.name}': {self.email!r}")

    @property
    def key(self) -> str:
        return self.email.strip().lower()


@dataclass(frozen=True)
class Assignment:
    giver: Employee
    child: Employee

    def as_row(self) -> dict:
        return {
            "Employee_Name": self.giver.name,
            "Employee_EmailID": self.giver.email,
            "Secret_Child_Name": self.child.name,
            "Secret_Child_EmailID": self.child.email,
        }
