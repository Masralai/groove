from unittest.mock import patch

import pytest

from app.services.llm_service import llm_service


@pytest.mark.asyncio
async def test_generate_sql_success():
    """Test successful SQL generation."""
    with patch.object(llm_service, '_call_llm') as mock_call:
        mock_call.return_value = {
            "success": True,
            "text": "```sql\nSELECT * FROM campaigns LIMIT 10;\n```"
        }

        result = await llm_service.generate_sql("Show me all campaigns")

        assert result["success"] is True
        assert "SELECT" in result["sql"]
        assert result["error"] == ""


@pytest.mark.asyncio
async def test_generate_sql_failure():
    """Test SQL generation failure."""
    with patch.object(llm_service, '_call_llm') as mock_call:
        mock_call.return_value = {
            "success": False,
            "error": "API Error"
        }

        result = await llm_service.generate_sql("Show me all campaigns - failure test")

        assert result["success"] is False
        assert result["error"] == "API Error"


@pytest.mark.asyncio
async def test_summarize_results_with_data():
    """Test summarizing results when data exists."""
    query_results = [
        {"date": "2023-01-01", "spend": 100.50, "clicks": 50},
        {"date": "2023-01-02", "spend": 150.25, "clicks": 75}
    ]

    with patch.object(llm_service, '_call_llm') as mock_call:
        mock_call.return_value = {
            "success": True,
            "text": "The data shows increasing spend over the two days."
        }

        result = await llm_service.summarize_results(
            "What was our spend trend?",
            "SELECT date, spend, clicks FROM insights",
            query_results
        )

        assert result["success"] is True
        assert "increasing spend" in result["summary"]
        assert result["error"] == ""


@pytest.mark.asyncio
async def test_summarize_results_no_data():
    """Test summarizing results when no data exists."""
    query_results = []

    result = await llm_service.summarize_results(
        "What was our spend trend?",
        "SELECT date, spend, clicks FROM insights",
        query_results
    )

    assert result["success"] is True
    assert "No data found" in result["summary"]
    assert result["error"] == ""
