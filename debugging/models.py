from pydantic import BaseModel, Field, field_validator

RECORDS = {
    "USER-101": {
        "record_id": "USER-101",
        "name": "Alice",
        "department": "Engineering",
        "tenure_months": 18,
        "completed_projects": 5,
        "skill_score": 85,
    },
    "USER-202": {
        "record_id": "USER-202",
        "name": "Bob",
        "department": "Engineering",
        "tenure_months": 6,
        "completed_projects": 1,
        "skill_score": 45,
    },
}


def calculate_score(record: dict) -> int:
    raw = (record["skill_score"] * 0.5
           + (record["completed_projects"] / 10) * 100 * 0.3
           + min(record["tenure_months"] / 24, 1.0) * 100 * 0.2)
    return max(0, min(100, round(raw)))


def calculate_status(score: int) -> str:
    if score >= 70:
        return "approved"
    if score >= 50:
        return "review"
    return "rejected"


class AnalyzerOutput(BaseModel):
    record_id: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"approved", "review", "rejected"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}, got {v!r}")
        return v
