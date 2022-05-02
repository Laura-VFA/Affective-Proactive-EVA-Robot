from dataclasses import dataclass

from .google_api import getSpeechFromText, getTextFromSpeech, translateEStoEN
from .ibm_api import analyzeMood, createSession, genResponse, is_session_active


@dataclass
class Request:
    audio: str
    text: str = None
    username: str = None
    proactive_question: str = ''

@dataclass
class Response:
    request: Request
    audio: str
    action: str
    username: str
    continue_conversation: bool
    eva_mood: str = 'neutral'
    text: str = None


def query(request : Request):
    # STT
    request.text = getTextFromSpeech(request.audio)
    print('L: ' + request.text)
    
    if not request.text:
        return None

    # Translation (for emotion analysis)
    translation = translateEStoEN(request.text)

    # Emotion Analysis & other context variables
    context_variables = analyzeMood(translation) 
    context_variables["username"] = request.username
    context_variables["action"] = None
    context_variables["continue"] = ""
    context_variables["eva_mood"] = ""
    context_variables["proactive_question"] = request.proactive_question
    print('L:', context_variables)

    # Generate the response
    text_response, user_skills = genResponse(request.text, context_variables)
    print('E: ' + text_response)
    print('E:', user_skills)

    # TTS
    audio_response = getSpeechFromText(text_response)

    # Send back the response
    return Response(
        request,
        audio_response,
        user_skills.get('action', None),
        user_skills.get('username', None),
        bool(user_skills.get('continue', '')),
        user_skills.get('eva_mood', 'neutral'),
        text_response
    )

def tts(text):
    return getSpeechFromText(text)

def stt(audio):
    return getTextFromSpeech(audio)

def prepare():
    if not is_session_active():
        createSession()
