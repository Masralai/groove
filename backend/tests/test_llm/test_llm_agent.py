import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.llm_agent_service import llm_agent_service

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    mock_response = MagicMock()
    mock_response.text = "```sql\nSELECT * FROM campaigns LIMIT 10;\n```"
    return mock_response

@pytest.mark.asyncio
async def test_generate_sql_success(mock_gemini_response):
    """Test successful SQL generation."""
    with patch('app.services.llm_agent_service.genai.GenerativeModel') as mock_model:
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_gemini_response
        mock_model.return_value = mock_instance
        
        result = await llm_agent_service.generate_sql("Show me all campaigns")
        
        assert result["success"] is True
        assert "SELECT" in result["sql"]
        assert result["error"] == ""

@pytest.mark.asyncio
async def test_generate_sql_failure():
    """Test SQL generation failure."""
    with patch('app.services.llm_agent_service.genai.GenerativeModel') as mock_model:
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_instance
        
        result = await llm_agent_service.generate_sql("Show me all campaigns")
        
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
    
    with patch('app.services.llm_agent_service.genai.GenerativeModel') as mock_model:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "The data shows increasing spend over the two days."
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = await llm_agent_service.summarize_results(
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
    
    result = await llm_agent_service.summarize_results(
        "What was our spend trend?", 
        "SELECT date, spend, clicks FROM insights", 
        query_results
    )
    
    assert result["success"] is True
    assert "No data found" in result["summary"]
    assert result["error"] == ""