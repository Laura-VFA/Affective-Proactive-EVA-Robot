# contains methods for the assistant performance: google services
# (TTS, STT and translation)

from google.oauth2 import service_account

from google.cloud import texttospeech, speech
from google.cloud import translate_v2 as translate



# TTS 
SERVICE_ACCOUNT_FILE = "./credentials/tts_credentials.json"
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
clientTTS = texttospeech.TextToSpeechClient(credentials=credentials)
#const clientTTS = new textToSpeech.TextToSpeechClient( {keyFilename: "tts_credentials.json"});
voice = texttospeech.VoiceSelectionParams(
    language_code='es-ES', ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
tts_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16, #TODO LINEAR16, 24000 HRZ
    sample_rate_hertz=24000
)

# STT 
SERVICE_ACCOUNT_FILE = "./credentials/stt_credentials.json"
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
clientSTT = speech.SpeechClient(credentials=credentials) # keyfilename?
stt_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="es-ES"
)

# Translator 
SERVICE_ACCOUNT_FILE = "./credentials/translation_credentials.json"
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
translate_client = translate.Client(credentials=credentials) #keyfilename??



def getTextFromSpeech(audio_bytes):
    try:
        audio = speech.RecognitionAudio(content=audio_bytes)
        response = clientSTT.recognize(config=stt_config, audio=audio)
    except Exception as e:
        print('STT Error:', str(e))
    
    else:
        total_response = ''

        for result in response.results:
            # The first alternative is the most likely one for this portion.
            total_response += result.alternatives[0].transcript

        return total_response

def getSpeechFromText(text):
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = clientTTS.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=tts_config
        )
    except Exception as e:
        print('TTS Error: ', str(e))
    else:
        return response.audio_content

def translateEStoEN(text):
    try:
        result = translate_client.translate(text, target_language='en')
    except Exception as e:
        print('translation Error: ', str(e))
    else:
        return result["translatedText"]

