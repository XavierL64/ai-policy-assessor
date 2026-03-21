from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pydantic models – define the contract between the API and its callers
# ---------------------------------------------------------------------------

# --- Request ---

class AssessmentRequest(BaseModel):
    commitment_id: str = Field(
        description="Commitment ID to assess (e.g. 'CP.1', 'CP.2')"
    )
    pdf_source: str = Field(
        description="Path to the policy PDF file"
    )
    model: str = Field(
        default="gpt-4o",
        description="OpenAI model name to use for the assessment"
    )

# --- Response ---

class Reference(BaseModel):
    excerpt: str = Field(description="Verbatim excerpt from the policy")
    document_name: str = Field(description="Name of the source document")
    page_start: int = Field(description="Page where the excerpt starts")
    page_end: int = Field(description="Page where the excerpt ends")

class CommitmentResult(BaseModel):
    value: bool = Field(description="Whether the policy contains the commitment")
    references: list[Reference] = Field(description="Supporting excerpts from the policy")

class ExceptionResult(BaseModel):
    exception_id: str = Field(description="ID from the exception taxonomy")
    applies: bool = Field(description="Whether this exception applies")
    description: str | None = Field(description="Short description if the exception applies")
    mitigated: bool = Field(description="Whether the exception is mitigated")
    mitigant: str | None = Field(description="Short description of the mitigant")
    references: list[Reference] = Field(description="Supporting excerpts from the policy")

class AssessmentResponse(BaseModel):
    commitment: CommitmentResult
    exceptions: list[ExceptionResult]

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Policy Assessor",
    description="Evaluates bank fossil fuel policies against defined assessment criteria.",
)

@app.get("/health")
def health_check():
    """Simple health check to verify the service is running."""
    return {"status": "ok"}

@app.post("/assess", response_model=AssessmentResponse)
def run_assessment(request: AssessmentRequest):
    """
    Run a policy commitment assessment using the two-step simple approach.

    Assesses whether a policy contains a specified commitment, then evaluates
    applicable exceptions and their mitigants.
    """
    from two_step_simple import run_two_step_simple_analysis

    try:
        result = run_two_step_simple_analysis(
            commitment_id=request.commitment_id,
            pdf_source=request.pdf_source,
            model_name=request.model,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result
