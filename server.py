from matplotlib.style import context
from google_api import getTextFromSpeech, getSpeechFromText, translateEStoEN
from ibm_api import genResponse, analyzeMood

def query(audio_blob):
    # STT
    text_query = getTextFromSpeech(audio_blob)
    print('L: ' + text_query)
    if not text_query:
        return None

    # Translation (for emotion analysis)
    translation = translateEStoEN(text_query)

    # Emotion Analysis
    context_variables = analyzeMood(translation) 
    print(context_variables)
    # TODO add username and other db variables

    # Generate the response
    text_response = genResponse(text_query, context_variables)
    print('E: ' + text_response)

    # TTS
    audio_response = getSpeechFromText(text_response)

    # Send back the response
    return audio_response
