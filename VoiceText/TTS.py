import edge_tts
import os
import asyncio
import pygame
from config import settings 
from groq import Groq
import soundfile as sf
import sounddevice as sd
import tempfile

class SpeechText:
    @staticmethod
    async def Text_to_speech(text : str):
        output_file = f"{settings.Mp3_Fiels_Path}/response.mp3"
        voice = settings.SpeakerVoice
        communicate = edge_tts.Communicate(text,
                                        voice,
                                        rate = "+7%",
                                        pitch="-30Hz",
                                        )
        await communicate.save(output_file)

        pygame.mixer.init()
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        pygame.mixer.quit()



    @staticmethod
    def Speech_to_text():
        client = Groq(api_key = settings.GROQ_API_KEY)   # api key

        sample_rate = 16000
        chunk_duration = 3  # second

        def record_chunk():
            print("listenning.....")

            audio = sd.rec(
                int(chunk_duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype= "float32"
            )
            sd.wait()
            return audio

        while True:
            audio = record_chunk()
            with tempfile.NamedTemporaryFile(suffix=".wav") as f:   # f = path/file_name.wav
                file_path = os.path.join(settings.Wav_Files_Path,os.path.basename(f.name))
                sf.write(file_path,audio,sample_rate)

                with open(file_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file = audio_file,
                        model= settings.STT_Model    # Model name
                    )
                return transcription.text
            


# def speak(text):
#     asyncio.run(SpeechText.Text_to_speech(text))

# text = """Hello, thank you for calling City Center Pharmacy. 
# I see you're looking to coordinate a prescription refill today.
#  To ensure everything is processed accurately, 
# I'll just need to verify a few details with you first."""
# speak(text)

print(SpeechText.Speech_to_text())