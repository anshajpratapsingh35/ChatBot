# 🔮 Multimodal AI Companion (MVP)

A modular, production-oriented, and intelligent **Multimodal AI Companion** combining:
- **Multimodal AI Processing**: Text conversation, image understanding (VQA), speech-to-text (STT), and neural text-to-speech (TTS).
- **Precision RAG (Retrieval-Augmented Generation)**: Grounded question-answering over uploaded PDFs, DOCXs, and TXTs with chunk citations and anti-hallucination guardrails.
- **Empathetic Emotional Support**: Active listening, supportive dialogue, and compassionate framing isolated from standard transactional queries.
- **Enterprise Safety Guardrails**: Real-time crisis detection (self-harm/suicide keyword interception with verified global & local emergency resources), prompt injection defense, and file signature validation.
- **Clean Decoupled Architecture**: High-performance FastAPI REST backend connected to a normalized MySQL schema and a responsive Streamlit interface in a modern dark violet/purple aesthetic.

---

## 🏛️ System Architecture

```
                    ┌────────────────────────────────────────┐
                    │      Streamlit Frontend (:8501)        │
                    │ (Violet Dark UI, Chat Bubbles, Audio)  │
                    └──────────────────┬─────────────────────┘
                                       │ HTTP REST APIs
                                       ▼
                    ┌────────────────────────────────────────┐
                    │        FastAPI Backend (:8000)         │
                    │ (CORS, SlowAPI Rate Limiting, Routers) │
                    └──────┬───────────┬───────────┬─────────┘
                           │           │           │
         ┌─────────────────┘           │           └─────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────────┐
│  Domain Services │         │  Data Storage    │         │  AI / Model Engine   │
├──────────────────┤         ├──────────────────┤         ├──────────────────────┤
│ • ChatService    │         │ • MySQL 8.0+     │         │ • Gemini 2.0 / OpenAI│
│ • RAGService     │         │   (conversations,│         │ • text-embedding-004 │
│ • ImageService   │         │    messages,     │         │ • Edge-TTS / gTTS    │
│ • AudioService   │         │    documents,    │         │ • Pillow Preprocess  │
│ • DocumentService│         │    embeddings)   │         │ • PyMuPDF / docx     │
│ • EmotionService │         │ • Local Storage  │         └──────────────────────┘
│ • SafetyService  │         │   (vault files)  │
└──────────────────┘         └──────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | Streamlit | `>= 1.35.0` | Dark violet/purple UI, audio player, image/doc preview, RAG citations |
| **Backend** | FastAPI | `0.115.6` | REST API, OpenAPI docs, Pydantic v2 schemas |
| **Database** | MySQL | `8.0+` | Normalized storage with foreign keys, indexing, and SQLite fallback |
| **ORM** | SQLAlchemy + PyMySQL | `2.0.36` / `1.1.1` | Pooled DB engine, transactional sessions |
| **AI Providers** | Google GenAI / OpenAI | `google-genai 2.28.0` / `openai 3.26.0` | Multimodal chat, vision reasoning, and text embeddings |
| **Document Parsers**| PyMuPDF (`fitz`), python-docx| `1.23.8` / `1.1.0` | Page-aware text extraction for PDF, DOCX, TXT |
| **Speech (TTS/STT)**| `edge-tts`, `gTTS`, Whisper | `edge-tts 7.3.1` | Neural speech synthesis and transcription |
| **Image Vision** | Pillow (`PIL`) | `10.1.0` | Orientation correction, scaling, and format normalization |
| **Security** | SlowAPI, Regex AST | `0.1.9` | Rate limiting, MIME verification, crisis & prompt injection defense |

---

## 📁 Project Directory Structure

```
d:\ff\ChatBot\
├── app/
│   ├── backend/
│   │   ├── main.py                  # FastAPI initialization, CORS, exception handlers
│   │   ├── api/                     # Modular API routers
│   │   │   ├── chat_router.py       # /api/chat, /api/chat/multimodal, /api/conversations
│   │   │   ├── document_router.py   # /api/documents/upload, /api/documents
│   │   │   ├── audio_router.py      # /api/audio/transcribe, /api/audio/synthesize
│   │   │   └── health_router.py     # /api/health
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings, .env loader
│   │   │   ├── security.py          # Input validation, sanitization, rate limiting
│   │   │   └── guardrails.py        # Crisis detection, safety policies, prompts
│   │   ├── database/
│   │   │   ├── connection.py        # SQLAlchemy engine, session maker, DB health check
│   │   │   └── init_db.py           # Table schema migration and creation
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── document.py
│   │   │   └── chunk.py
│   │   ├── schemas/                 # Pydantic request & response schemas
│   │   ├── services/                # Domain logic
│   │   │   ├── provider_service.py  # LLM/Embeddings abstraction (Gemini/OpenAI)
│   │   │   ├── chat_service.py      # Conversation management & LLM turns
│   │   │   ├── rag_service.py       # Chunking, vector embedding, cosine search
│   │   │   ├── image_service.py     # Pillow validation & multimodal vision
│   │   │   ├── audio_service.py     # Whisper STT & Edge/Google TTS
│   │   │   ├── document_service.py  # PyMuPDF/docx page text extraction
│   │   │   ├── emotion_service.py   # Empathy analysis & response conditioning
│   │   │   └── safety_service.py    # Self-harm/crisis detection & moderation
│   │   └── utils/
│   │       ├── logger.py            # Structured logging
│   │       └── file_storage.py      # Local secure disk manager
│   │
│   ├── frontend/
│   │   ├── streamlit_app.py         # Streamlit interactive UI entrypoint
│   │   ├── components/              # UI widgets (chat bubbles, audio player, citations)
│   │   └── assets/                  # CSS styles, violet dark theme
│   │
│   └── storage/                     # Isolated local disk storage
│       ├── documents/               # Stored PDFs/DOCXs
│       ├── images/                  # Stored uploaded images
│       └── audio/                   # Generated/received speech audio files
│
├── tests/                           # Complete test suite
├── scripts/
│   ├── init_mysql.py                # Database setup & verification script
│   └── run_dev.bat                  # One-click Windows development launcher
├── .env.example                     # Environment template
├── requirements.txt                 # Pinned dependencies
└── README.md                        # Project documentation
```

---

## 🚀 Setup & Installation (Windows / VS Code)

### 1. Prerequisites
- **Python**: 3.11+ installed.
- **MySQL**: MySQL 8.0+ installed and running (or XAMPP with MySQL started).
  > *Note: If MySQL is not running, the application gracefully activates an automated local SQLite database fallback (`app/storage/companion.db`) so development never halts.*

### 2. Configure Environment
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and set your credentials:
```env
# AI Provider (Gemini or OpenAI)
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# MySQL Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=multimodal_companion_db
```

### 3. Initialize MySQL Database
Run the initialization helper script to create the database schema:
```powershell
python scripts/init_mysql.py
```

### 4. Running the Application

Open two terminal windows in VS Code (or double click `scripts/run_dev.bat`):

**Terminal 1 — Backend (FastAPI):**
```powershell
python -m uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

**Terminal 2 — Frontend (Streamlit):**
```powershell
python -m streamlit run app/frontend/streamlit_app.py
```
- Streamlit Web Interface: `http://localhost:8501`

---

## 🎯 Key Features & Modalities

### 1. Text & Conversational Context
- Multi-turn conversation retention with configurable context sliding window.
- Session isolation: Conversations are strictly independent with dedicated message histories.

### 2. Vision Reasoning (Image Understanding)
- Upload JPG, JPEG, PNG, or WEBP images.
- Pillow validation, automatic EXIF orientation transposition, and aspect ratio scaling.
- Visual Question Answering (VQA) with detailed scene and object analysis.

### 3. Voice Audio (STT & TTS)
- Upload or record audio files (WAV, MP3, M4A, OGG).
- Transcribes spoken audio into prompt context.
- Generates natural spoken responses using Microsoft Neural Voices (`edge-tts`) or `gTTS`.
- Direct audio player playback directly in the chat interface.

### 4. Grounded Document RAG
- Upload PDF, DOCX, or TXT knowledge files.
- SHA-256 duplicate detection avoids redundant chunking.
- Recursive character chunking preserving page-number metadata.
- Semantic vector similarity search with cosine distance ranking.
- Context-grounded responses with collapsible citations (`[Doc: <name>, Page: <n>]`).
- Strict refusal when documents lack the answer, preventing hallucination.

### 5. Emotional Support & Crisis Safety Protocol
- Detects user emotional state (sadness, anxiety, loneliness, anger, joy) and conditions response with warm, active-listening empathy.
- **Safety Interceptor**: Immediately detects self-harm or suicide keywords, bypassing standard generation to provide compassionate support and emergency resources:
  - *US / Canada: 988 Suicide & Crisis Lifeline*
  - *India: Tele-MANAS (14416 / 1800-891-4416) & Vandrevala Foundation (+91 9999 666 555)*
  - *UK: 111 / Samaritans (116 123)*
  - *International: findahelpline.com*
- Strict boundary: Never diagnoses conditions or claims to be a licensed therapist.

---

## 🧪 Testing

Run the automated test suite with pytest:
```powershell
python -m pytest tests/ -v
```

Tests cover:
- Database connectivity, conversation CRUD, and cascading deletions.
- Document parsing (PDF/DOCX/TXT), chunking overlap, and vector similarity retrieval.
- Image preprocessing and MIME signature validation.
- Audio synthesis and TTS generation.
- Crisis detection, prompt injection mitigation, and empathy classification.
- Full FastAPI endpoint integration (`/api/health`, `/api/chat`, `/api/conversations`, `/api/audio/synthesize`).

---

## 🔒 Scope & Controlled MVP Notice
User authentication and admin portals are explicitly excluded from this MVP release. The application is intended for controlled local development and testing environments.
