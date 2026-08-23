import os
from dotenv import load_dotenv

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
STT_Model = "whisper-large-v3-turbo"
ChatModel = "gemini-3.5-flash-lite"
SpeakerVoice = "en-AU-WilliamNeural"
Mp3_Fiels_Path = "./VoiceText/Mp3Files"
Wav_Files_Path = "./VoiceText/WavFiles"

