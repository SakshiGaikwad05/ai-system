import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StageLog:
    timestamp: float
    request_id: str
    stage: str
    status: str
    duration_ms: float
    attempt: int = 1
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    expected_record_id: Optional[str] = None
    actual_record_id: Optional[str] = None


class Logger:
    def __init__(self) -> None:
        self.logs: List[StageLog] = []

    def log(self, request_id: str, stage: str, status: str,
            duration_ms: float, attempt: int = 1,
            error_type: Optional[str] = None,
            error_message: Optional[str] = None,
            expected_record_id: Optional[str] = None,
            actual_record_id: Optional[str] = None) -> None:
        entry = StageLog(
            timestamp=time.time(),
            request_id=request_id,
            stage=stage,
            status=status,
            duration_ms=round(duration_ms, 1),
            attempt=attempt,
            error_type=error_type,
            error_message=error_message,
            expected_record_id=expected_record_id,
            actual_record_id=actual_record_id,
        )
        self.logs.append(entry)

    def by_request(self, request_id: str) -> List[StageLog]:
        return [l for l in self.logs if l.request_id == request_id]

    def last(self) -> Optional[StageLog]:
        return self.logs[-1] if self.logs else None

    def clear(self) -> None:
        self.logs.clear()


logger = Logger()
