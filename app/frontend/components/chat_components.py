import streamlit as st
import html
from typing import List, Dict, Any, Optional

def render_header():
    """Renders the top branding header with a glowing aesthetic."""
    st.markdown("""
        <div class="companion-header">
            <div>
                <h1>🔮 Antigravity Multimodal Companion</h1>
                <p>Empathetic AI Companion with Grounded Document RAG, Vision Reasoning & Voice</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_user_message(content: str, modality: str = "text", media_url: Optional[str] = None):
    """Renders a user message bubble."""
    safe_content = html.escape(content).replace("\n", "<br>")
    modality_icon = "💬"
    if modality == "image":
        modality_icon = "🖼️"
    elif modality == "audio":
        modality_icon = "🎙️"
    elif modality == "document":
        modality_icon = "📄"

    st.markdown(f"""
        <div class="message-row user-row">
            <div class="user-bubble">
                <div style="font-size: 11px; opacity: 0.8; margin-bottom: 4px;">{modality_icon} You</div>
                <div>{safe_content}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_assistant_message(
    content: str,
    citations: Optional[List[Dict[str, Any]]] = None,
    emotion: Optional[str] = None,
    is_crisis: bool = False,
    message_id: Optional[str] = None
):
    """Renders an assistant message bubble with badges, citations, and actions."""
    # Determine badge
    badges_html = ""
    if is_crisis:
        badges_html += '<span class="badge-tag badge-crisis">🛡️ Crisis Support</span> '
    elif emotion and emotion != "neutral":
        badges_html += f'<span class="badge-tag badge-empathy">💜 {emotion.capitalize()}</span> '
    
    if citations:
        badges_html += '<span class="badge-tag badge-rag">📚 Grounded in Documents</span> '

    safe_content = html.escape(content).replace("\n", "<br>")

    st.markdown(f"""
        <div class="message-row assistant-row">
            <div class="assistant-bubble">
                <div style="margin-bottom: 6px;">{badges_html}</div>
                <div>{safe_content}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Render citations if present
    if citations:
        with st.expander(f"📖 View Document Citations ({len(citations)} source chunks)"):
            for i, cite in enumerate(citations):
                st.markdown(f"""
                    <div class="citation-box">
                        <div class="citation-title">[{i+1}] {cite.get('document_name', 'Document')} (Page {cite.get('page_number', 1)}) — Relevance: {cite.get('similarity', 0.0)}</div>
                        <div>"{html.escape(cite.get('snippet', ''))}"</div>
                    </div>
                """, unsafe_allow_html=True)
