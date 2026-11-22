from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CitationItem(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    chunk_index: int
    snippet: str
    similarity: float

class MessageBase(BaseModel):
    role: str
    content: str
    modality: str = "text"
    media_url: Optional[str] = None
    citations: Optional[List[CitationItem]] = None
    metadata_payload: Optional[Dict[str, Any]] = None

class MessageCreate(BaseModel):
    content: str
    modality: str = "text"
    media_url: Optional[str] = None

class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    message_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    modality: str = "text"
    use_rag: bool = True
    emotional_support: bool = True
    media_path: Optional[str] = None
    api_key: Optional[str] = None
    ai_provider: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    citations: List[CitationItem] = []
    detected_emotion: Optional[str] = None
    is_crisis: bool = False
