class SecretSantaError(Exception):
    pass


class CSVFormatError(SecretSantaError):
    pass


class InsufficientEmployeesError(SecretSantaError):
    pass


class AssignmentImpossibleError(SecretSantaError):
    pass


class DuplicateEmployeeError(SecretSantaError):
    pass
