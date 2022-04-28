# contains methods for the assistant performance: ibm watson

import json
import os
from datetime import datetime

from ibm_watson import AssistantV2, NaturalLanguageUnderstandingV1


with open(os.environ.get('WATSON_ASSISTANT_CREDENTIALS')) as json_file:
    auth_data = json.load(json_file)

SESSION_TIME = 10 # in seconds
last_query_time = None
session_id = ''
assistant_id = auth_data['assistant_id']

assistant = AssistantV2(
    version='2021-06-14',
)

def createSession():
    global session_id, assistant_id

    response = assistant.create_session(
        assistant_id=assistant_id
    ).get_result()
    session = response['session_id']

    session_id = session


# Natural Language Understanding: Emotions 
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




def genResponse(data, context_data={}):
    global session_id, assistant_id, last_query_time

    if not data :
        return None

    response = assistant.message(
        assistant_id=assistant_id,
        session_id=session_id,
        input={
            'message_type': 'text',
            'text': data,
            'options': {
                'return_context': True # For returning the context variables
            }
        },
        context={
            "skills": {
                "main skill": {
                    "user_defined": context_data
                }
            }
        }
    ).get_result()

    last_query_time = datetime.now()

    final_response = '. '.join([resp['text'] for resp in response['output']['generic']])
    
    action = (get_user_skill(response, 'action'), get_user_skill(response, 'username'))
    print(action)
    continue_flag = bool(get_user_skill(response, 'continue'))
    print('Continue', continue_flag)
    eva_mood = get_user_skill(response, 'eva_mood')
    eva_mood = eva_mood if eva_mood else 'neutral'
    return final_response, action, continue_flag, eva_mood


def analyzeMood(text):
    nluOptions['text'] = text
    try:
        response = nlu.analyze(**nluOptions).get_result()
    except Exception as e:
        print('analyzeMood error: ', str(e))
        return {}
    else:
        return response['emotion']['document']['emotion']


def is_session_active(): # empty query to check if session is active
    global last_query_time
    return last_query_time is not None and (datetime.now() - last_query_time).total_seconds() < SESSION_TIME 

def get_user_skill(response, skill):
    if not skill in response['context']['skills']['main skill']['user_defined']:
        return None

    return response['context']['skills']['main skill']['user_defined'][skill]
