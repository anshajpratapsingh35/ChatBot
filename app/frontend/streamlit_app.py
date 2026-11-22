import os
import streamlit as st
import requests
from pathlib import Path
from app.frontend.components.chat_components import (
    render_header, render_user_message, render_assistant_message
)

# Page Configuration
st.set_page_config(
    page_title="Multimodal AI Companion",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Styling
css_file = Path(__file__).parent / "assets" / "styles.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

# Session State Initialization
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auto_tts" not in st.session_state:
    st.session_state.auto_tts = False
if "emotional_support" not in st.session_state:
    st.session_state.emotional_support = True
if "use_rag" not in st.session_state:
    st.session_state.use_rag = True
if "tts_voice" not in st.session_state:
    st.session_state.tts_voice = "en-US-AriaNeural"
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = ""

def check_backend_health():
    try:
        r = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
        return r.status_code == 200, r.json() if r.status_code == 200 else {}
    except Exception:
        return False, {}

def fetch_conversations():
    try:
        r = requests.get(f"{API_BASE_URL}/api/conversations", timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.sidebar.error(f"Failed to fetch conversations: {e}")
    return []

def load_conversation(conv_id: str):
    try:
        r = requests.get(f"{API_BASE_URL}/api/conversations/{conv_id}", timeout=4)
        if r.status_code == 200:
            data = r.json()
            st.session_state.conversation_id = conv_id
            st.session_state.messages = data.get("messages", [])
            st.rerun()
    except Exception as e:
        st.error(f"Error loading conversation {conv_id}: {e}")

def create_new_conversation():
    try:
        r = requests.post(f"{API_BASE_URL}/api/conversations", json={"title": "New Conversation"}, timeout=4)
        if r.status_code == 200:
            data = r.json()
            st.session_state.conversation_id = data["id"]
            st.session_state.messages = []
            st.rerun()
    except Exception as e:
        st.error(f"Error creating conversation: {e}")

def delete_conversation(conv_id: str):
    try:
        requests.delete(f"{API_BASE_URL}/api/conversations/{conv_id}", timeout=4)
        if st.session_state.conversation_id == conv_id:
            st.session_state.conversation_id = None
            st.session_state.messages = []
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting conversation: {e}")

def fetch_documents():
    try:
        r = requests.get(f"{API_BASE_URL}/api/documents", timeout=4)
        if r.status_code == 200:
            return r.json().get("documents", [])
    except Exception:
        pass
    return []

def delete_document(doc_id: str):
    try:
        r = requests.delete(f"{API_BASE_URL}/api/documents/{doc_id}", timeout=4)
        if r.status_code == 200:
            st.sidebar.success("Document removed.")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error deleting document: {e}")

def synthesize_audio(text: str):
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/audio/synthesize",
            json={"text": text, "voice": st.session_state.tts_voice},
            timeout=10
        )
        if r.status_code == 200:
            audio_url = r.json().get("audio_url")
            return f"{API_BASE_URL}{audio_url}"
    except Exception as e:
        st.warning(f"Voice synthesis unavailable: {e}")
    return None

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.markdown("### 🔮 Navigation & Sessions")
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        create_new_conversation()

    st.markdown("---")
    st.markdown("#### 💬 Previous Conversations")
    conversations = fetch_conversations()
    if conversations:
        for c in conversations[:12]:
            col1, col2 = st.columns([5, 1])
            with col1:
                is_active = (c["id"] == st.session_state.conversation_id)
                prefix = "▶ " if is_active else ""
                label = f"{prefix}{c['title'][:22]} ({c.get('message_count', 0)})"
                if st.button(label, key=f"conv_{c['id']}", use_container_width=True):
                    load_conversation(c["id"])
            with col2:
                if st.button("🗑️", key=f"del_{c['id']}", help="Delete Conversation"):
                    delete_conversation(c["id"])
    else:
        st.caption("No conversations yet.")

    st.markdown("---")
    st.markdown("#### 📚 Uploaded Knowledge Base")
    doc_uploader = st.file_uploader(
        "Upload PDF, DOCX, TXT",
        type=["pdf", "docx", "txt"],
        key="doc_sidebar_uploader",
        help="Embeddings will be indexed into MySQL for RAG grounding."
    )
    if doc_uploader is not None:
        if st.button("📥 Process Document", use_container_width=True):
            with st.spinner("Chunking & Embedding document..."):
                files = {"file": (doc_uploader.name, doc_uploader.getvalue(), doc_uploader.type)}
                try:
                    r = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, timeout=30)
                    if r.status_code == 200:
                        st.success(f"Indexed {doc_uploader.name}!")
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", "Upload failed"))
                except Exception as ex:
                    st.error(f"Upload error: {ex}")

    docs = fetch_documents()
    if docs:
        for d in docs:
            d_col1, d_col2 = st.columns([5, 1])
            with d_col1:
                st.caption(f"📄 **{d['filename'][:20]}** ({d['total_chunks']} chunks)")
            with d_col2:
                if st.button("✕", key=f"doc_del_{d['id']}", help="Delete Document"):
                    delete_document(d['id'])
    else:
        st.caption("No documents indexed yet.")

    st.markdown("---")
    st.markdown("#### ⚙️ Companion Settings")
    st.session_state.emotional_support = st.toggle("💜 Emotional Support", value=st.session_state.emotional_support)
    st.session_state.use_rag = st.toggle("📚 Use RAG Knowledge", value=st.session_state.use_rag)
    st.session_state.auto_tts = st.toggle("🔊 Auto Voice Response", value=st.session_state.auto_tts)
    
    st.session_state.tts_voice = st.selectbox(
        "Neural Voice",
        ["en-US-AriaNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"],
        index=0
    )

    st.markdown("#### 🔑 Model Access Key")
    key_input = st.text_input(
        "API Key (Optional)",
        type="password",
        value=st.session_state.custom_api_key,
        placeholder="Paste Gemini or OpenAI key...",
        help="Connect your personal API key directly from the browser without editing server files."
    )
    if key_input != st.session_state.custom_api_key:
        st.session_state.custom_api_key = key_input

    if st.button("🧹 Clear Chat History", use_container_width=True):
        if st.session_state.conversation_id:
            delete_conversation(st.session_state.conversation_id)

# ==========================================
# MAIN INTERFACE
# ==========================================
render_header()

# Backend connectivity check
is_healthy, health_info = check_backend_health()
if not is_healthy:
    st.warning("⚠️ Backend server is offline. Please run `uvicorn app.backend.main:app --reload` to start the backend.")

# Display Chat Messages
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        render_user_message(
            content=msg["content"],
            modality=msg.get("modality", "text"),
            media_url=msg.get("media_url")
        )
    else:
        meta = msg.get("metadata_payload") or {}
        render_assistant_message(
            content=msg["content"],
            citations=msg.get("citations"),
            emotion=meta.get("emotion"),
            is_crisis=meta.get("crisis", False),
            message_id=msg.get("id")
        )
st.markdown('</div>', unsafe_allow_html=True)

# Audio Player for Latest Voice Generation
if "latest_audio_url" in st.session_state and st.session_state.latest_audio_url:
    st.audio(st.session_state.latest_audio_url, format="audio/mp3")

# Multimodal Input Tabs
input_tab1, input_tab2, input_tab3 = st.tabs(["💬 Text Message", "🖼️ Image Reasoning", "🎙️ Voice Audio"])

# 1. TEXT INPUT TAB
with input_tab1:
    user_prompt = st.chat_input("Share your thoughts or ask a question...")
    if user_prompt:
        # Optimistic update
        st.session_state.messages.append({
            "role": "user",
            "content": user_prompt,
            "modality": "text"
        })
        with st.spinner("AI Companion is thinking..."):
            payload = {
                "conversation_id": st.session_state.conversation_id,
                "message": user_prompt,
                "modality": "text",
                "use_rag": st.session_state.use_rag,
                "emotional_support": st.session_state.emotional_support,
                "api_key": st.session_state.get("custom_api_key") or None
            }
            try:
                r = requests.post(f"{API_BASE_URL}/api/chat", json=payload, timeout=30)
                if r.status_code == 200:
                    resp_data = r.json()
                    st.session_state.conversation_id = resp_data["conversation_id"]
                    asst_msg = resp_data["assistant_message"]
                    st.session_state.messages.append(asst_msg)

                    # Trigger TTS if enabled
                    if st.session_state.auto_tts:
                        audio_url = synthesize_audio(asst_msg["content"])
                        st.session_state.latest_audio_url = audio_url

                    st.rerun()
                else:
                    st.error(f"Error {r.status_code}: {r.json().get('detail')}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# 2. IMAGE REASONING TAB
with input_tab2:
    img_col1, img_col2 = st.columns([1, 1])
    with img_col1:
        uploaded_img = st.file_uploader("Upload Image (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"], key="chat_img_upload")
        if uploaded_img:
            st.image(uploaded_img, caption="Image Preview", use_container_width=True)
    with img_col2:
        img_prompt = st.text_area("Question about image", value="What do you see in this image? Please describe it in detail.")
        if uploaded_img and st.button("🔍 Analyze Image", key="btn_analyze_img", use_container_width=True):
            with st.spinner("Analyzing visual details..."):
                files = {"file": (uploaded_img.name, uploaded_img.getvalue(), uploaded_img.type)}
                data = {
                    "conversation_id": st.session_state.conversation_id or "",
                    "message": img_prompt,
                    "modality": "image",
                    "use_rag": False,
                    "emotional_support": st.session_state.emotional_support,
                    "api_key": st.session_state.get("custom_api_key") or ""
                }
                try:
                    r = requests.post(f"{API_BASE_URL}/api/chat/multimodal", files=files, data=data, timeout=40)
                    if r.status_code == 200:
                        resp_data = r.json()
                        st.session_state.conversation_id = resp_data["conversation_id"]
                        st.session_state.messages.append(resp_data["user_message"])
                        st.session_state.messages.append(resp_data["assistant_message"])
                        st.rerun()
                    else:
                        st.error(f"Error: {r.json().get('detail')}")
                except Exception as e:
                    st.error(f"Image analysis request failed: {e}")

# 3. VOICE AUDIO TAB
with input_tab3:
    audio_col1, audio_col2 = st.columns([1, 1])
    with audio_col1:
        uploaded_audio = st.file_uploader("Upload Voice Audio (WAV, MP3, M4A, OGG)", type=["wav", "mp3", "m4a", "ogg", "webm"], key="chat_audio_upload")
        if uploaded_audio:
            st.audio(uploaded_audio)
    with audio_col2:
        audio_text_context = st.text_input("Additional context (optional)", placeholder="E.g., I'm feeling stressed today...")
        if uploaded_audio and st.button("🎙️ Send Spoken Message", key="btn_send_audio", use_container_width=True):
            with st.spinner("Transcribing speech and generating response..."):
                files = {"file": (uploaded_audio.name, uploaded_audio.getvalue(), uploaded_audio.type)}
                data = {
                    "conversation_id": st.session_state.conversation_id or "",
                    "message": audio_text_context,
                    "modality": "audio",
                    "use_rag": st.session_state.use_rag,
                    "emotional_support": st.session_state.emotional_support,
                    "api_key": st.session_state.get("custom_api_key") or ""
                }
                try:
                    r = requests.post(f"{API_BASE_URL}/api/chat/multimodal", files=files, data=data, timeout=40)
                    if r.status_code == 200:
                        resp_data = r.json()
                        st.session_state.conversation_id = resp_data["conversation_id"]
                        st.session_state.messages.append(resp_data["user_message"])
                        asst_msg = resp_data["assistant_message"]
                        st.session_state.messages.append(asst_msg)

                        # Synthesize speech response
                        audio_url = synthesize_audio(asst_msg["content"])
                        st.session_state.latest_audio_url = audio_url

                        st.rerun()
                    else:
                        st.error(f"Error: {r.json().get('detail')}")
                except Exception as e:
                    st.error(f"Audio processing failed: {e}")
