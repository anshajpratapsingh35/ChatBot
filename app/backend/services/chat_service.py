from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.backend.models.conversation import Conversation
from app.backend.models.message import Message
from app.backend.models.document import Document, ConversationDocumentMapping
from app.backend.schemas.chat_schema import ChatRequest, ChatResponse, MessageResponse, CitationItem
from app.backend.services.safety_service import safety_service
from app.backend.services.emotion_service import emotion_service
from app.backend.services.rag_service import rag_service
from app.backend.services.image_service import image_service
from app.backend.services.provider_service import provider_service
from app.backend.core.guardrails import SafetyGuardrails
from app.backend.utils.logger import logger

class ChatService:
    """Orchestrates multi-turn conversations, RAG grounding, vision reasoning, and persistence."""

    @staticmethod
    def get_or_create_conversation(db: Session, conversation_id: Optional[str] = None) -> Conversation:
        if conversation_id:
            conv = db.get(Conversation, conversation_id)
            if conv and not conv.is_archived:
                return conv
        
        # Create new conversation
        new_conv = Conversation(title="New Conversation")
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        logger.info(f"Created new conversation session: {new_conv.id}")
        return new_conv

    @staticmethod
    def process_chat_turn(db: Session, request: ChatRequest) -> ChatResponse:
        """
        Processes a full conversational turn:
        1. Validates / sanitizes input.
        2. Evaluates crisis / prompt injection guardrails.
        3. Identifies emotional state.
        4. Performs RAG semantic retrieval if applicable.
        5. Handles image analysis if media_path provided.
        6. Constructs context window and prompts LLM.
        7. Persists messages to database.
        """
        conversation = ChatService.get_or_create_conversation(db, request.conversation_id)
        sanitized_input = safety_service.sanitize(request.message)

        # 1. Safety & Crisis Inspection
        is_safe, safety_msg, is_crisis = safety_service.inspect_input(sanitized_input)
        if not is_safe:
            # Save user message
            user_msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=sanitized_input,
                modality=request.modality
            )
            # Save assistant intervention
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=safety_msg,
                modality="text",
                metadata_payload={"crisis": is_crisis, "blocked": True}
            )
            db.add(user_msg)
            db.add(assistant_msg)
            db.commit()
            db.refresh(user_msg)
            db.refresh(assistant_msg)

            return ChatResponse(
                conversation_id=conversation.id,
                user_message=MessageResponse.model_validate(user_msg),
                assistant_message=MessageResponse.model_validate(assistant_msg),
                citations=[],
                detected_emotion="crisis" if is_crisis else "blocked",
                is_crisis=is_crisis
            )

        # 2. Emotion Analysis
        detected_emotion = emotion_service.detect_emotion(sanitized_input)
        empathy_guidance = emotion_service.get_empathy_guidance(detected_emotion) if request.emotional_support else ""

        # 3. RAG Retrieval
        citations: List[CitationItem] = []
        rag_context_text = ""
        if request.use_rag:
            citations = rag_service.retrieve_relevant_chunks(
                db=db,
                query=sanitized_input,
                conversation_id=conversation.id
            )
            if citations:
                rag_context_text = rag_service.format_context_for_prompt(citations, db)

        # 4. Generate Response based on Modality
        if request.modality == "image" and request.media_path:
            # Multimodal Vision Turn
            try:
                response_text = image_service.analyze_image(
                    image_path=request.media_path,
                    user_query=sanitized_input or "Describe what you see in this image.",
                    api_key=request.api_key,
                    provider=request.ai_provider
                )
            except Exception as e:
                response_text = f"Unable to analyze the image: {str(e)}"
        else:
            # Multi-turn Text / RAG Turn
            # Build conversation history window (last 8 messages)
            history_records = db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(desc(Message.created_at))
                .limit(8)
            ).all()
            history_records.reverse()

            history_msgs = []
            for h in history_records:
                history_msgs.append({"role": h.role, "content": h.content})

            # Append current turn
            history_msgs.append({"role": "user", "content": sanitized_input})

            # Build system prompt with empathy + RAG context
            system_instruction = SafetyGuardrails.build_system_prompt(
                emotional_support=request.emotional_support,
                rag_context=rag_context_text if citations else None
            )
            if empathy_guidance:
                system_instruction += f"\n\nCURRENT EMOTION GUIDANCE:\n{empathy_guidance}"

            response_text = provider_service.generate_chat_response(
                messages=history_msgs,
                system_instruction=system_instruction,
                api_key=request.api_key,
                provider=request.ai_provider
            )

        # 5. Persist to Database
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=sanitized_input,
            modality=request.modality,
            media_url=request.media_path
        )
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            modality="text",
            citations=[c.model_dump() for c in citations] if citations else None,
            metadata_payload={"emotion": detected_emotion, "rag_grounded": bool(citations)}
        )

        db.add(user_msg)
        db.add(assistant_msg)

        # Update conversation title if default
        if conversation.title == "New Conversation":
            first_few_words = " ".join(sanitized_input.split()[:5])
            if first_few_words:
                conversation.title = first_few_words[:40]

        db.commit()
        db.refresh(user_msg)
        db.refresh(assistant_msg)

        return ChatResponse(
            conversation_id=conversation.id,
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
            citations=citations,
            detected_emotion=detected_emotion,
            is_crisis=False
        )

chat_service = ChatService()
