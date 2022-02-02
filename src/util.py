# util.js contains methods for the assistant performance: google services
# (TTS, STT and translation) and Watson Assistant
from functools import total_ordering
import json
from urllib import response
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EmotionOptions

from google.cloud import texttospeech, speech
from google.cloud import translate_v2 as translate
from matplotlib.style import context

# Assistant IBM (TODO PROBAR A QUE COJA SOLO LO DE LAS APIKEY)
with open('./assistant_credentials.json') as json_file:
    auth_data = json.load(json_file)

session_id = ''
final_response = ''
assistant_id = auth_data['assistant_id']

authenticator = IAMAuthenticator(auth_data['apikey'])
assistant = AssistantV2(
    authenticator=authenticator
)
assistant.set_service_url(auth_data['url'])

def createSession(assistant_id):
    try:
        response = assistant.create_session(
            assistant_id=assistant_id
        ).get_result()

        session_id = response['session_id']
    except Exception as e:
        print(('createSession Error: ' + str(e)))

createSession(assistant_id)


# Natural Language Understanding: Emotions IBM
nlu = NaturalLanguageUnderstandingV1(
    version='2021-08-01'
)
nluOptions = {
    'text': '',
    'features': {
        'emotion': {},
    },
    'language': "en"
}


# TTS Google
#const { Readable } = require('stream');
clientTTS = texttospeech.TextToSpeechClient()
#const clientTTS = new textToSpeech.TextToSpeechClient( {keyFilename: "tts_credentials.json"});
voice = texttospeech.VoiceSelectionParams(
    language_code='es-ES', ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
tts_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16, #TODO LINEAR16, 24000 HRZ
    sample_rate_hertz=24000
)


# STT Google
clientSTT = speech.SpeechClient() # keyfilename?
stt_config = speech.RecognitionConfig(
    #sample_rate_hertz=16000,
    language_code="es-ES"
)

# Translator Google
translate_client = translate.Client() #keyfilename??


def translateEStoEN(text):
    result = translate_client.translate(text, target_language='en')
    return result["translatedText"]

def analyzeMood(text):
    nluOptions['text'] = text
    try:
        response = nlu.analyze(**nluOptions).get_result()
    except Exception as e:
        print('analyzeMood error: ', str(e))
    return response['result']['emotion']['document']['emotion']

def getTextFromSpeech(speech):
    try:
        audio = clientSTT.RecognitionAudio(content=speech)
        response = clientSTT.recognize(config=stt_config, audio=audio)
    except Exception as e:
        print('STT Error:', str(e))
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

    return response.audio_content

def genResponse(data):
    if data != '':
        translt = translateEStoEN(data)
        moodAnalysis = analyzeMood(translt)
        print(moodAnalysis)
        context_data = {
            "sadness": moodAnalysis['sadness'],
            "joy": moodAnalysis['joy'],
            "fear": moodAnalysis['fear'],
            "disgust": moodAnalysis['disgust'],
            "anger": moodAnalysis['anger'],
        }
    
    try:
        response = assistant.message(
            assistant_id=assistant_id,
            session_id=session_id,
            input={
                'message_type': 'text',
                'text': data
            },
            context={
                "skills": {
                    "main skill": {
                        "user_defined": context_data
                    }
                }
            }
        ).get_result()
    except Exception as e:
        print('genResponse Error: ', str(e))

    final_response = '. '.join([resp['text'] for resp in response['output']['generic']])
    return final_response


# TODO: AÑADIR AWAITS