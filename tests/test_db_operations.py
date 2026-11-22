import pytest
from app.backend.database.connection import get_db, check_db_health
from app.backend.models.conversation import Conversation
from app.backend.models.message import Message
from app.backend.models.document import Document
from app.backend.models.chunk import DocumentChunk, Embedding

def test_database_connection_healthy():
    status = check_db_health()
    assert status["connected"] is True
    assert status["status"] == "healthy"

def test_conversation_and_message_crud():
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Create
        conv = Conversation(title="Test DB Session")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        assert conv.id is not None
        assert conv.title == "Test DB Session"

        # Add Messages
        msg1 = Message(
            conversation_id=conv.id,
            role="user",
            content="Hello AI",
            modality="text"
        )
        msg2 = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Hello User, how can I support you today?",
            modality="text",
            metadata_payload={"emotion": "neutral"}
        )
        db.add_all([msg1, msg2])
        db.commit()

        # Query
        fetched_conv = db.get(Conversation, conv.id)
        assert len(fetched_conv.messages) == 2
        assert fetched_conv.messages[0].content == "Hello AI"
        assert fetched_conv.messages[1].role == "assistant"

        # Cleanup
        db.delete(fetched_conv)
        db.commit()
        assert db.get(Conversation, conv.id) is None
    finally:
        db.close()
