from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.backend.database.connection import get_db
from app.backend.models.conversation import Conversation
from app.backend.models.message import Message
from app.backend.schemas.chat_schema import (
    ChatRequest, ChatResponse, ConversationCreate, ConversationResponse,
    ConversationDetailResponse, MessageResponse
)
from app.backend.services.chat_service import chat_service
from app.backend.services.audio_service import audio_service
from app.backend.services.image_service import image_service
from app.backend.core.security import SecurityValidator, limiter
from app.backend.utils.file_storage import FileStorageManager
from app.backend.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Chat & Conversations"])

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("60/minute")
def send_chat_message(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db)
):
    """Processes a text-based conversational turn with RAG and emotional support."""
    try:
        return chat_service.process_chat_turn(db, payload)
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/multimodal", response_model=ChatResponse)
@limiter.limit("30/minute")
async def send_multimodal_message(
    request: Request,
    message: str = Form(default=""),
    conversation_id: Optional[str] = Form(default=None),
    modality: str = Form(default="image"),  # "image" or "audio"
    file: UploadFile = File(...),
    use_rag: bool = Form(default=True),
    emotional_support: bool = Form(default=True),
    api_key: Optional[str] = Form(default=None),
    ai_provider: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """Accepts an image or audio upload alongside user text for multimodal reasoning."""
    content = await file.read()
    
    if modality == "image":
        SecurityValidator.validate_image(file.filename, content, file.content_type)
        _, file_path = FileStorageManager.save_image(file.filename, content)
        # Preprocess image
        image_service.preprocess_image(file_path)
        
        chat_req = ChatRequest(
            conversation_id=conversation_id,
            message=message or "Analyze this image in detail.",
            modality="image",
            media_path=file_path,
            use_rag=use_rag,
            emotional_support=emotional_support,
            api_key=api_key,
            ai_provider=ai_provider
        )
        return chat_service.process_chat_turn(db, chat_req)

    elif modality == "audio":
        SecurityValidator.validate_audio(file.filename, content, file.content_type)
        ext = file.filename.split(".")[-1]
        _, file_path = FileStorageManager.save_audio(content, ext=f".{ext}")
        
        # Transcribe audio to text
        transcribed_text = await audio_service.transcribe_audio(file_path)
        combined_prompt = f"{message} (Spoken: {transcribed_text})" if message else transcribed_text

        chat_req = ChatRequest(
            conversation_id=conversation_id,
            message=combined_prompt,
            modality="audio",
            media_path=file_path,
            use_rag=use_rag,
            emotional_support=emotional_support,
            api_key=api_key,
            ai_provider=ai_provider
        )
        return chat_service.process_chat_turn(db, chat_req)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported multimodal modality: {modality}")

@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    """Lists all active conversations."""
    conversations = db.scalars(
        select(Conversation)
        .where(Conversation.is_archived == False)
        .order_by(desc(Conversation.updated_at))
    ).all()

    result = []
    for c in conversations:
        msg_count = len(c.messages)
        resp = ConversationResponse.model_validate(c)
        resp.message_count = msg_count
        result.append(resp)
    return result

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Creates a fresh conversation thread."""
    conv = Conversation(title=payload.title or "New Conversation")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationResponse.model_validate(conv)

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full message history for a conversation."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    messages = [MessageResponse.model_validate(m) for m in conv.messages]
    resp = ConversationDetailResponse.model_validate(conv)
    resp.messages = messages
    return resp

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Deletes a conversation and all its messages."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    db.delete(conv)
    db.commit()
    logger.info(f"Deleted conversation: {conversation_id}")
    return {"message": "Conversation deleted successfully.", "id": conversation_id}
