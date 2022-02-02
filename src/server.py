import util

def query(audio_blob):
    # STT
    text_query = util.getTextFromSpeech(audio_blob)
    print('L: ' + text_query)

    # Generate the response
    text_response = util.genResponse(text_query)
    print('E: ' + text_response)

    # TTS and send back the response
    audio_stream = util.getSpeechFromText(text_response)
    return audio_stream
