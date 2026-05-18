import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.llm_service import llm_service


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    mock_response = MagicMock()
    mock_response.text = "```sql\nSELECT * FROM campaigns LIMIT 10;\n```"
    return mock_response


@pytest.mark.asyncio
async def test_generate_sql_success(mock_gemini_response):
    """Test successful SQL generation."""
    with patch.object(
        llm_service.client.models, 'generate_content'
    ) as mock_generate:
        mock_generate.return_value = mock_gemini_response

        result = await llm_service.generate_sql("Show me all campaigns")

        assert result["success"] is True
        assert "SELECT" in result["sql"]
        assert result["error"] == ""


@pytest.mark.asyncio
async def test_generate_sql_failure():
    """Test SQL generation failure."""
    with patch.object(
        llm_service.client.models, 'generate_content'
    ) as mock_generate:
        mock_generate.side_effect = Exception("API Error")

        result = await llm_service.generate_sql("Show me all campaigns")

        assert result["success"] is False
        assert result["sql"] == ""
        assert "Failed to generate SQL" in result["error"]


@pytest.mark.asyncio
async def test_summarize_results_with_data():
    """Test summarizing results when data exists."""
    query_results = [
        {"date": "2023-01-01", "spend": 100.50, "clicks": 50},
        {"date": "2023-01-02", "spend": 150.25, "clicks": 75}
    ]

    with patch.object(
        llm_service.client.models, 'generate_content'
    ) as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "The data shows increasing spend over the two days."
        mock_generate.return_value = mock_response

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
