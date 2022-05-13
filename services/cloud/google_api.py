# Google services wrapper
# (TTS, STT and translation)
import os

from google.cloud import speech, texttospeech
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

# TTS 
credentials = service_account.Credentials.from_service_account_file(os.environ.get('GOOGLE_CREDENTIALS'))
clientTTS = texttospeech.TextToSpeechClient(credentials=credentials)
voice = texttospeech.VoiceSelectionParams(
    language_code='es-ES',
    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
tts_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    sample_rate_hertz=24000
)

# STT 
credentials = service_account.Credentials.from_service_account_file(os.environ.get('GOOGLE_CREDENTIALS'))
clientSTT = speech.SpeechClient(credentials=credentials)
stt_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="es-ES"
)

# Translator 
credentials = service_account.Credentials.from_service_account_file(os.environ.get('GOOGLE_CREDENTIALS'))
translate_client = translate.Client(credentials=credentials)



def speech_to_text(audio_bytes):
    audio = speech.RecognitionAudio(content=audio_bytes)
    response = clientSTT.recognize(config=stt_config, audio=audio)

    # The first alternative is the most likely one
    return "".join(result.alternatives[0].transcript for result in response.results)

def text_to_speech(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = clientTTS.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=tts_config
    )

    return response.audio_content

def translate_to(text, target_language='en'):
    # Origin language is automatically detected
    result = translate_client.translate(text, target_language=target_language)

    return result["translatedText"]
