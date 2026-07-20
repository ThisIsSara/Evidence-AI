# routers/investigation.py
# The API endpoints that trigger the local investigation engine.
# No AI models or external APIs are used - this just calls plain Python
# functions in services/investigation_engine.py and returns their result as JSON.

from fastapi import APIRouter, HTTPException

from models.schemas import CustomCaseRequest
from services.investigation_engine import analyze_case, build_case_from_custom_input, run_investigation

router = APIRouter()


@router.post("/run-investigation")
def run_investigation_endpoint():
    """Analyze the built-in demo case's evidence and return the full investigation report."""
    return run_investigation()


@router.post("/analyze-custom-case")
def analyze_custom_case_endpoint(payload: CustomCaseRequest):
    """Analyze a user-submitted case. FastAPI has already validated the request shape via CustomCaseRequest."""
    try:
        evidence_items = [item.model_dump() for item in payload.evidence]
        case = build_case_from_custom_input(
            payload.case_title, payload.case_category, payload.report_language, evidence_items
        )
        return analyze_case(case)
    except Exception as error:
        # Something unexpected happened inside the engine itself (not a validation problem,
        # FastAPI already handles those). Keep the error message simple and non-technical.
        raise HTTPException(
            status_code=500,
            detail="We couldn't analyze this evidence. Please check the submitted text and try again.",
        ) from error
