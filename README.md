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

## Models Used
- **STT**: Deepgram `nova-2`
- **LLM**: Groq `llama-3.3-70b-versatile`
- **TTS**: Sarvam `bulbul:v2` (Speaker: `anushka`)

## Usage
1. Open the frontend URL (usually `http://localhost:5173`).
2. Click the microphone button to start.
3. Speak into your microphone.
4. The AI will respond with audio.

## Troubleshooting
- **Port 8000 already in use**: If the backend fails to start, check if another process is using port 8000 (`lsof -ti:8000 | xargs kill -9`).
- **Deepgram Connection Error**: Ensure your API key is valid and you are using the correct model configuration.
- **Sarvam 400 Error**: Ensure you are using `bulbul:v2` as the model and a valid speaker like `anushka`.
