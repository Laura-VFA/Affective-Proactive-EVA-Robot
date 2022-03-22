from google_api import getTextFromSpeech, getSpeechFromText, translateEStoEN
from ibm_api import genResponse, analyzeMood, is_session_active, createSession

def query(audio_blob, username=None):
    # STT
    text_query = getTextFromSpeech(audio_blob)
    print('L: ' + text_query)
    if not text_query:
        return None, None

    # Translation (for emotion analysis)
    translation = translateEStoEN(text_query)

    # Emotion Analysis & other context variables
    context_variables = analyzeMood(translation) 
    context_variables["username"] = username
    context_variables["action"] = None
    context_variables["continue"] = ""
    print(context_variables)

    # Generate the response
    text_response, action, continue_flag = genResponse(text_query, context_variables)
    print('E: ' + text_response)

    # TTS
    audio_response = getSpeechFromText(text_response)

    # Send back the response
    return audio_response, action, continue_flag

def tts(text):
    return getSpeechFromText(text)

def prepare():
    if not is_session_active():
        createSession()
