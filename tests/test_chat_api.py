import pytest
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "ai_provider" in data

def test_conversation_lifecycle():
    # 1. Create Conversation
    create_res = client.post("/api/conversations", json={"title": "Integration Test Chat"})
    assert create_res.status_code == 200
    conv_data = create_res.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Integration Test Chat"

    # 2. List Conversations
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    all_convs = list_res.json()
    assert any(c["id"] == conv_id for c in all_convs)

    # 3. Send Safe Message
    chat_payload = {
        "conversation_id": conv_id,
        "message": "Hello AI, can you recommend ways to relax after work?",
        "modality": "text",
        "use_rag": False,
        "emotional_support": True
    }
    chat_res = client.post("/api/chat", json=chat_payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["conversation_id"] == conv_id
    assert chat_data["is_crisis"] is False
    assert chat_data["assistant_message"]["content"] != ""

    # 4. Send Crisis Message and verify immediate intervention
    crisis_payload = {
        "conversation_id": conv_id,
        "message": "I don't want to live anymore, thinking about ending my life",
        "modality": "text",
        "use_rag": False,
        "emotional_support": True
    }
    crisis_res = client.post("/api/chat", json=crisis_payload)
    assert crisis_res.status_code == 200
    crisis_data = crisis_res.json()
    assert crisis_data["is_crisis"] is True
    assert "988" in crisis_data["assistant_message"]["content"]

    # 5. Delete Conversation
    del_res = client.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 200

    # 6. Verify 404 after deletion
    get_res = client.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 404

def test_speech_synthesis_api():
    payload = {"text": "Speech synthesis integration test."}
    res = client.post("/api/audio/synthesize", json=payload)
    assert res.status_code == 200
    assert "audio_url" in res.json()
