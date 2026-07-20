# models/schemas.py
# Pydantic models describing the shape of requests our API accepts.
# FastAPI uses these to validate incoming JSON automatically - if a request
# doesn't match, FastAPI rejects it before our code ever runs.

from typing import List, Literal

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """One piece of evidence submitted for a custom investigation."""

    title: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=20000)


class CustomCaseRequest(BaseModel):
    """The full payload for POST /analyze-custom-case."""

    case_title: str = Field(..., min_length=1, max_length=200)
    case_category: str = Field(..., min_length=1, max_length=100)
    report_language: Literal["en", "ar"] = "en"
    # At least 2 evidence documents are required for contradiction detection
    # to have anything to compare; 6 is the same cap the form UI enforces.
    evidence: List[EvidenceItem] = Field(..., min_length=2, max_length=6)
