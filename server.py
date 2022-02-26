from google_api import getTextFromSpeech, getSpeechFromText
from ibm_api import genResponse

def query(audio_blob):
    # STT
    text_query = getTextFromSpeech(audio_blob)
    print('L: ' + text_query)
    if not text_query:
        return None

    # Generate the response
    text_response = genResponse(text_query)
    print('E: ' + text_response)

    # TTS
    audio_response = getSpeechFromText(text_response)

    # Send back the response
    return audio_response
