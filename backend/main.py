import os
import json
import asyncio
import websockets
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from deepgram import DeepgramClient
from deepgram.clients.live.v1 import LiveTranscriptionEvents, LiveOptions
from groq import Groq

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# Initialize Clients
deepgram = DeepgramClient(DEEPGRAM_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

async def get_groq_response(text):
    print(f"Generating response for: {text}")
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful voice assistant. Keep your responses concise and conversational.",
            },
            {
                "role": "user",
                "content": text,
            }
        ],
        model="llama3-8b-8192",
    )
    return chat_completion.choices[0].message.content

async def get_sarvam_tts(text):
    print(f"Generating TTS for: {text}")
    url = "https://api.sarvam.ai/text-to-speech"
    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN", # Defaulting to Hindi/Indian context given Sarvam, but can be changed
        "speaker": "meera"
    }
    headers = {
        "Content-Type": "application/json",
        "API-Subscription-Key": SARVAM_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        # Sarvam returns base64 encoded audio in "audios" list
        data = response.json()
        if "audios" in data and len(data["audios"]) > 0:
            return data["audios"][0] # Base64 string
        return None
    except Exception as e:
        print(f"Error in Sarvam TTS: {e}")
        return None

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        deepgram_socket = deepgram.listen.asyncwebsocket.v("1")

        async def on_message(result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            
            if result.is_final:
                print(f"User: {sentence}")
                # 1. Get LLM Response
                llm_response = await get_groq_response(sentence)
                print(f"AI: {llm_response}")
                
                # 2. Get TTS
                audio_base64 = await get_sarvam_tts(llm_response)
                
                if audio_base64:
                    # Send back to client
                    await websocket.send_json({
                        "type": "audio",
                        "data": audio_base64,
                        "text": llm_response
                    })
                else:
                    print("Failed to generate audio")

        deepgram_socket.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms=1000,
            vad_events=True,
        )

        if await deepgram_socket.start(options) is False:
            print("Failed to start Deepgram")
            return

        while True:
            data = await websocket.receive_bytes()
            await deepgram_socket.send(data)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # await deepgram_socket.finish() # This might cause issues if socket is already closed
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
