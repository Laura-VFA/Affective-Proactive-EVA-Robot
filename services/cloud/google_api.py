# contains methods for the assistant performance: google services
# (TTS, STT and translation)
import os

from google.cloud import speech, texttospeech
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

# TTS 
credentials = service_account.Credentials.from_service_account_file(os.environ.get('TTS_CREDENTIALS'))
clientTTS = texttospeech.TextToSpeechClient(credentials=credentials)
voice = texttospeech.VoiceSelectionParams(
    language_code='es-ES', ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
tts_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    sample_rate_hertz=24000
)

# STT 
credentials = service_account.Credentials.from_service_account_file(os.environ.get('STT_CREDENTIALS'))
clientSTT = speech.SpeechClient(credentials=credentials)
stt_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="es-ES"
)

# Translator 
credentials = service_account.Credentials.from_service_account_file(os.environ.get('TRANSLATOR_CREDENTIALS'))
translate_client = translate.Client(credentials=credentials)



def getTextFromSpeech(audio_bytes):
    audio = speech.RecognitionAudio(content=audio_bytes)
    response = clientSTT.recognize(config=stt_config, audio=audio)
    
    total_response = ''

    for result in response.results:
        # The first alternative is the most likely one for this portion.
        total_response += result.alternatives[0].transcript

    return total_response

def getSpeechFromText(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = clientTTS.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=tts_config
    )

    return response.audio_content

def translateEStoEN(text):
    result = translate_client.translate(text, target_language='en')

    return result["translatedText"]

