from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import get_agent
from app.agent import RecommendationAgent

router = APIRouter()

@router.get("/health")
def health_check() -> dict:
    """Readiness probe endpoint. Returns status OK."""
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest, 
    agent: RecommendationAgent = Depends(get_agent)
) -> ChatResponse:
    """
    Stateless conversational recommendation endpoint.
    Processes the request messages and returns the next reply and recommendations list.
    """
    response_data = agent.process_conversation(request.messages)
    return ChatResponse(
        reply=response_data["reply"],
        recommendations=response_data["recommendations"],
        end_of_conversation=response_data["end_of_conversation"]
    )
