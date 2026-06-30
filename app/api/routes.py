from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.get("/health")
def health_check() -> dict:
    """Readiness probe endpoint. Returns status OK."""
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Stateless conversational recommendation endpoint.
    Processes the request messages and returns the next reply and recommendations list.
    """
    # Phase 1: Return a mock response that conforms to the requested schema.
    return ChatResponse(
        reply="Hello! I am your SHL Assessment Recommendation assistant. How can I help you today?",
        recommendations=[],
        end_of_conversation=False
    )
