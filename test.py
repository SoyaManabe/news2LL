import asyncio

try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyht import Client
from dotenv import load_dotenv
from pyht.client import TTSOptions
import os
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play

load_dotenv()

os.environ["PLAY_HT_USER_ID"] = "wYNfoMQ8WJSabFEVtP0bQzzn6E13"
os.environ["PLAY_HT_API_KEY"] = "ea3c42b8bd6a489bb1098931e0df05e1"

client = Client(
    user_id=os.getenv("PLAY_HT_USER_ID"),
    api_key=os.getenv("PLAY_HT_API_KEY"),
)
options = TTSOptions(voice="s3://voice-cloning-zero-shot/b41d1a8c-2c99-4403-8262-5808bc67c3e0/bentonsaad/manifest.json")

def pht_text_to_speech(text):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    audio_data = BytesIO()

    for chunk in client.tts(text, options):
        # do something with the audio chunk
        audio_data.write(chunk)
    
    loop.close()
    audio_data.seek(0)
    return audio_data

