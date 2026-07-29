class WorkflowError(Exception):
    pass


class WorkflowTimeoutError(WorkflowError):
    pass


class MalformedOutputError(WorkflowError):
    pass


class DataIntegrityError(WorkflowError):
    def __init__(self, message: str, expected_record_id: str, actual_record_id: str) -> None:
        super().__init__(message)
        self.expected_record_id = expected_record_id
        self.actual_record_id = actual_record_id
