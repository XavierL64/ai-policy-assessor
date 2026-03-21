from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# --- Health check ---

def test_health_check():
    """Service should return ok when running."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Input validation ---

def test_assess_missing_fields():
    """Should return 422 when required fields are missing."""
    response = client.post("/assess", json={})
    assert response.status_code == 422

def test_assess_missing_pdf_source():
    """Should return 422 when pdf_source is missing."""
    response = client.post("/assess", json={"commitment_id": "CP.1"})
    assert response.status_code == 422


# --- Successful assessment (mocked) ---

MOCK_RESULT = {
    "commitment": {
        "value": True,
        "references": [
            {
                "excerpt": "The bank will not finance new coal power plants.",
                "document_name": "Climate Policy 2024",
                "page_start": 3,
                "page_end": 3,
            }
        ],
    },
    "exceptions": [
        {
            "exception_id": "EX.1",
            "applies": True,
            "description": "Existing contractual obligations",
            "mitigated": True,
            "mitigant": "Phase-out by 2030",
            "references": [
                {
                    "excerpt": "Existing commitments will be honoured until 2030.",
                    "document_name": "Climate Policy 2024",
                    "page_start": 5,
                    "page_end": 5,
                }
            ],
        }
    ],
}

@patch("two_step_simple.run_two_step_simple_analysis", return_value=MOCK_RESULT)
def test_assess_success(mock_analysis):
    """Should return 200 with correct response shape when assessment succeeds."""
    response = client.post("/assess", json={
        "commitment_id": "CP.1",
        "pdf_source": "policies/Test/test.pdf",
    })
    assert response.status_code == 200

    data = response.json()
    assert "commitment" in data
    assert "exceptions" in data
    assert data["commitment"]["value"] is True
    assert len(data["exceptions"]) == 1
    assert data["exceptions"][0]["exception_id"] == "EX.1"

@patch("two_step_simple.run_two_step_simple_analysis", return_value=MOCK_RESULT)
def test_assess_uses_default_model(mock_analysis):
    """Should pass default model when not specified."""
    client.post("/assess", json={
        "commitment_id": "CP.1",
        "pdf_source": "policies/Test/test.pdf",
    })
    mock_analysis.assert_called_once_with(
        commitment_id="CP.1",
        pdf_source="policies/Test/test.pdf",
        model_name="gpt-4o",
    )


# --- Error handling ---

@patch("two_step_simple.run_two_step_simple_analysis", side_effect=FileNotFoundError("PDF not found"))
def test_assess_file_not_found(mock_analysis):
    """Should return 404 when PDF file doesn't exist."""
    response = client.post("/assess", json={
        "commitment_id": "CP.1",
        "pdf_source": "policies/nonexistent.pdf",
    })
    assert response.status_code == 404
