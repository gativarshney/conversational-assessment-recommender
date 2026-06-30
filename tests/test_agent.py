import pytest
from unittest.mock import MagicMock, patch
from app.agent import RecommendationAgent
from app.schemas.chat import Message

@pytest.fixture
def mock_retriever() -> MagicMock:
    """Fixture that returns a mocked retriever with pre-seeded query outputs."""
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        {
            "entity_id": "4094",
            "name": "Core Java (Advanced Level) (New)",
            "link": "https://www.shl.com/products/product-catalog/view/core-java-advanced-level-new/",
            "test_type": "K",
            "keys": ["Knowledge & Skills"],
            "job_levels": ["Professional Individual Contributor"],
            "languages": ["English (USA)"],
            "duration": "17 minutes",
            "description": "Advanced core java programming capabilities."
        }
    ]
    return retriever

def test_agent_fallback_mock_mode(mock_retriever: MagicMock) -> None:
    """Tests that the agent falls back to rule-based mock logic when the API key is missing."""
    with patch("app.agent.settings.GEMINI_API_KEY", None):
        agent = RecommendationAgent(retriever=mock_retriever)
        assert agent.model is None
        
        # Test vague request fallback
        response = agent.process_conversation([
            Message(role="user", content="I need some assessment solutions.")
        ])
        assert "clarify" in response["reply"].lower() or "assist" in response["reply"].lower() or "help" in response["reply"].lower()
        assert response["recommendations"] == []
        
        # Test Java request fallback
        response = agent.process_conversation([
            Message(role="user", content="Suggest a test for a Java engineer.")
        ])
        assert len(response["recommendations"]) == 1
        assert response["recommendations"][0]["name"] == "Core Java (Advanced Level) (New)"
        assert response["recommendations"][0]["url"].endswith("core-java-advanced-level-new/")
        
        # Test out-of-scope query fallback
        response = agent.process_conversation([
            Message(role="user", content="Can you draft a contract template?")
        ])
        assert response["recommendations"] == []
        assert "only discuss" in response["reply"].lower()

def test_agent_gemini_api_invocation_mocked(mock_retriever: MagicMock) -> None:
    """Tests the full RAG prompt building and structured generation calls when an API key is present."""
    with patch("app.agent.settings.GEMINI_API_KEY", "mocked_gemini_api_key"):
        with patch("google.generativeai.configure") as mock_configure:
            with patch("google.generativeai.GenerativeModel") as mock_model_class:
                mock_model = MagicMock()
                mock_model_class.return_value = mock_model
                
                # Setup mocked structured API response
                mock_response = MagicMock()
                mock_response.text = (
                    '{"reply": "Here is the advanced Core Java assessment for your team.", '
                    '"recommendations": [{"name": "Core Java (Advanced Level) (New)", '
                    '"url": "https://www.shl.com/products/product-catalog/view/core-java-advanced-level-new/", '
                    '"test_type": "K"}], "end_of_conversation": false}'
                )
                mock_model.generate_content.return_value = mock_response
                
                agent = RecommendationAgent(retriever=mock_retriever)
                assert agent.model is not None
                
                messages = [Message(role="user", content="Recommend a coding test for Java.")]
                response = agent.process_conversation(messages)
                
                # Check assertions
                mock_model.generate_content.assert_called_once()
                assert response["reply"] == "Here is the advanced Core Java assessment for your team."
                assert len(response["recommendations"]) == 1
                assert response["recommendations"][0]["name"] == "Core Java (Advanced Level) (New)"
                assert response["end_of_conversation"] is False
