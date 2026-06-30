from typing import List
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str = Field(..., description="Role of the message author (e.g., 'user' or 'assistant')")
    content: str = Field(..., description="The textual content of the message")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="The stateless sequence of chat messages")

class Recommendation(BaseModel):
    name: str = Field(..., description="The name of the recommended assessment")
    url: str = Field(..., description="The scraped catalog URL of the assessment")
    test_type: str = Field(..., description="The test type code (e.g., 'K' for Knowledge, 'P' for Personality)")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="The agent's text response")
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="A list of 1 to 10 recommended assessments, or empty if gathering details/refusing"
    )
    end_of_conversation: bool = Field(
        default=False,
        description="Whether the recommendation task is completed"
    )
