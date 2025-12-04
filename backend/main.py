import os
import json
import asyncio
import websockets
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
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
deepgram = AsyncDeepgramClient(api_key=DEEPGRAM_API_KEY)
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
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

async def get_sarvam_tts(text):
    print(f"Generating TTS for: {text}")
    url = "https://api.sarvam.ai/text-to-speech"
    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": "anushka",
        "pitch": 0,
        "pace": 1.2,
        "loudness": 1.5,
        "speech_sample_rate": 8000,
        "enable_preprocessing": True,
        "model": "bulbul:v2"
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
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Sarvam Error Body: {response.text}")
        return None

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        # Connect to Deepgram Live
        # Use minimal options to reduce chance of errors
        async with deepgram.listen.v1.connect(
            model="nova-2",
            language="en-US",
            smart_format=True, 
            interim_results=True,
            utterance_end_ms=1000,
            vad_events=True,
            endpointing=True,
        ) as deepgram_connection:

            async def on_open(result=None, **kwargs):
                print(f"Deepgram Connection OPEN")

            async def on_message(result):
                # print(f"Deepgram Message: {result}") # Debugging
                if hasattr(result, 'channel'):
                    channel = result.channel
                    if isinstance(channel, list):
                        channel = channel[0]
                    
                    if hasattr(channel, 'alternatives'):
                        transcript = channel.alternatives[0].transcript
                        if len(transcript) > 0:
                             print(f"Transcript: {transcript}, Final: {result.is_final}")
                        
                        if len(transcript) > 0 and result.is_final:
                            print(f"User: {transcript}")
                            # 1. Get LLM Response
                            llm_response = await get_groq_response(transcript)
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

            # Register event handlers
            deepgram_connection.on(EventType.OPEN, on_open)
            deepgram_connection.on(EventType.MESSAGE, on_message)
            deepgram_connection.on(EventType.ERROR, lambda e: print(f"Deepgram Error: {e}"))
            deepgram_connection.on(EventType.CLOSE, lambda c: print(f"Deepgram Closed: {c}"))

            print(f"Deepgram connection object: {deepgram_connection}")
            print(f"Has start_listening: {hasattr(deepgram_connection, 'start_listening')}")

            # Start the listening loop in the background
            loop = asyncio.get_event_loop()
            print("Starting listener task...")
            listener_task = loop.create_task(deepgram_connection.start_listening())
            print("Listener task created.")
            
            # Add done callback to check for errors
            def handle_task_result(task):
                print("Listener task finished!")
                try:
                    task.result()
                except asyncio.CancelledError:
                    print("Listener task cancelled")
                except Exception as e:
                    print(f"Listener task failed: {e}")
                    import traceback
                    traceback.print_exc()
            listener_task.add_done_callback(handle_task_result)

            # Give the task a moment to start
            await asyncio.sleep(0.1)

            try:
                while True:
                    data = await websocket.receive_bytes()
                    # print(f"Received audio chunk: {len(data)} bytes")
                    await deepgram_connection.send_media(data)
            finally:
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
