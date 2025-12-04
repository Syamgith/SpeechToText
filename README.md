# Voice-to-Voice AI Demo

A real-time voice conversation demo using **Deepgram** (STT), **Groq** (LLM), and **Sarvam** (TTS).

## Architecture
- **Frontend**: React (Vite) + WebSocket
- **Backend**: Python (FastAPI) + WebSocket

## Prerequisites
- Node.js & npm
- Python 3.8+
- API Keys for Deepgram, Groq, and Sarvam

## Setup

### 1. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/` with:
```env
DEEPGRAM_API_KEY=your_key
GROQ_API_KEY=your_key
SARVAM_API_KEY=your_key
```

Run the server:
```bash
uvicorn main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage
1. Open the frontend URL (usually `http://localhost:5173`).
2. Click the microphone button to start.
3. Speak into your microphone.
4. The AI will respond with audio.
