import logging
import queue
import threading

from services.camera_service import (FaceDB, PresenceDetector, RecordFace,
                                     Wakeface)
from services.cloud import server
from services.cloud.telegram import TelegramService
from services.eva_led import *
from services.eyes.eva_eyes import EvaEyes
from services.mic import Recorder
from services.proactive_service import ProactivePhrases, ProactiveService
from services.speaker import Speaker

# Logging configuration
logging.basicConfig(filename='./logs/UI.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
#log = logging.getLogger('STDERR')


notifications = queue.Queue()
listen_timer = None
DELAY_TIMEOUT = 5 # in sec
with open('files/connection_error.wav', 'rb') as f:
    connection_error_audio = f.read()

with open('files/tg_contact_error.wav', 'rb') as f:
    tg_contact_error_audio = f.read()


def wf_event_handler(event, usernames=None):
    global eva_context

    if event == 'face_listen' and eva_context['state'] == 'idle_presence':
        notifications.put({'transition': 'idle_presence2listening'})
    
    elif event in ['face_not_listen', 'not_faces']:
        eva_context['username'] = None

        if eva_context['state'] == 'listening':
            notifications.put({'transition': 'listening2idle_presence'})
        
    elif event == 'face_recognized':
        print(usernames)

        known_names = [name for name in usernames if name] # remove None names
        if known_names:
            known_names = sorted(usernames, key=lambda name: usernames[name], reverse=True)
            eva_context['username'] = known_names[0]
            print('username updated to', eva_context['username'])

        elif None in usernames and usernames[None] >= 3: # Detect 3 unknown in a row
            proactive.update('sensor', 'unknown_face')


def rf_event_handler(event, progress=None):
    if event == 'recording_face':
        notifications.put({
            'transition': 'recording_face', 
            'params': {
                'progress': progress
            }
        })

def pd_event_handler(event):
    if event == 'person_detected' and eva_context['state'] == 'idle' :
        notifications.put({'transition': 'idle2idle_presence'})
        proactive.update('sensor', 'presence')
    
    elif event == 'empty_room'  and eva_context['state'] == 'idle_presence' :
        notifications.put({'transition': 'idle_presence2idle'})
    

def mic_event_handler(event, audio=None):
    global eva_context

    notification = {
        'transition': '',
        'params': {
            'audio': audio
        }
    }
    if event == 'start_recording' and eva_context['state'] in ['listening', 'listening_without_cam']:
        if eva_context['state'] == 'listening':
            notification['transition']  = 'listening2recording'
        elif eva_context['state'] == 'listening_without_cam':
            notification['transition']  = 'listening_without_cam2recording'
        notifications.put(notification)

    if event == 'stop_recording' and eva_context['state'] == 'recording':
        notification['transition']  = 'recording2processingquery'
        notifications.put(notification)


def speaker_event_handler(event):
    global eva_context
    if event == 'finish_speak':
        if eva_context['continue_conversation']:
            
            notifications.put({'transition': 'speaking2listening_without_cam'})
        
        else:
            notifications.put({'transition': 'speaking2idle_presence'})

def proactive_service_event_handler(event, params={}):
    notification = {
        'transition': 'proactive2processingquery',
        'params': {
            'question': None
        }
    }

    if event == 'ask_how_are_you':
        notification ['params']['question'] = 'how_are_you'
        notifications.put(notification)
    
    elif event == 'ask_who_are_you':
        notification ['params']['question'] = 'who_are_you'
        notifications.put(notification)
    
    elif event == 'read_pending_messages':
        notification ['params']['question'] = 'read_pending_messages'
        notification['params']['messages'] = params
        notifications.put(notification)
        

def listen_timeout_handler():
    global eva_context
    notifications.put({'transition': 'listening_without_cam2idle_presence'})

def tg_event_handler(name, message): # incoming telegram message
    
    notifications.put({
        'transition': 'received_tg_message', 
        'params': {
            'name': name,
            'message': message
        }
    })


def process_transition(transition, params):
    global eva_context, listen_timer

    if transition == 'idle2idle_presence' and eva_context['state'] == 'idle':
        eva_led.set(StaticColor('purple'))
        eva_context['state'] = 'idle_presence'
        wf.start()
    
    if transition == 'idle_presence2idle' and eva_context['state'] == 'idle_presence':
        eva_led.set(StaticColor('black'))
        eva_context['username'] = None
        eva_context['state'] = 'idle'
        wf.stop()

    if transition == 'idle_presence2listening' and eva_context['state'] == 'idle_presence':
        eva_led.set(Loop('b'))
        eva_context['state'] = 'listening'
        pd.stop()
        mic.start()

    elif transition == 'listening2idle_presence' and eva_context['state'] == 'listening':
        eva_led.set(StaticColor('black'))
        eva_context['state'] = 'idle_presence'
        mic.stop()
        pd.start()

    elif transition == 'listening2recording' and eva_context['state'] == 'listening':
        eva_context['state'] = 'recording'
        eva_led.set(Loop('w'))
        try:
            server.prepare()
        except Exception as e:
            pass # TODO: logging
        #disconnect camera
        wf.stop()
    
    elif transition == 'listening_without_cam2recording' and eva_context['state'] == 'listening_without_cam':
        eva_context['state'] = 'recording'
        eva_led.set(Loop('w'))
        try:
            server.prepare()
        except Exception as e:
            pass # TODO: logging

        listen_timer.cancel()

    elif transition == 'recording2processingquery' and eva_context['state'] == 'recording':
        eva_context['state'] = 'processing_query'
        eva_led.set(StaticColor('black'))
        mic.stop()

        audio = params['audio']

        try:
            response = server.query(
                server.Request(
                    audio, 
                    username=eva_context['username'], 
                    proactive_question=eva_context['proactive_question']
                )
            )
        except Exception:
            eva_context['continue_conversation'] = False
            eva_context['proactive_question'] = ''
            eva_context['state'] = 'speaking'
            eva_led.set(Breath('r'))
            speaker.start(connection_error_audio)
        else:
            if response:
                if response.action: # Execute associated action
                    # Switch with action types
                    if response.action == 'record_face':
                        eva_context['username'] = response.username
                        rf.start(response.username)
                    elif response.action == 'update_target_name':
                        # Get text from speech to get user destination name
                        text = response.request.text.split()
                        dst_name = ' '.join(text[text.index('a' if 'a' in text else 'para') + 1 :])
                        eva_context['tg_destination_name'] = dst_name
                        print(dst_name)
                    elif response.action == 'send_message':
                        msg = response.request.text
                        try:
                            tg.send_message(eva_context['tg_destination_name'], msg) # try con except key error por si el contacto no existe?
                        except (KeyError, IndexError):
                            response.audio = tg_contact_error_audio
                        eva_context['tg_destination_name'] = ''

                eva_context['continue_conversation'] = response.continue_conversation
                eva_context['proactive_question'] = ''

                # Reproduce response                
                eva_context['state'] = 'speaking'
                #eva_eyes.set(eva_mood)
                eva_led.set(Breath('b'))
                speaker.start(response.audio)
            elif eva_context['continue_conversation']: # Avoid end the conversation due to noises
                eva_context['state'] = 'listening_without_cam'
                eva_led.set(Loop('b'))
                mic.start()

                # Add a timeout to execute a transition funcion due to inactivity
                listen_timer = threading.Timer(DELAY_TIMEOUT, listen_timeout_handler)
                listen_timer.start()
            else:
                #eva_eyes.set('neutral')
                eva_led.set(StaticColor('black'))
                eva_context['state'] = 'idle_presence'
                pd.start()
                wf.start()

    elif transition == 'speaking2listening_without_cam' and eva_context['state'] == 'speaking':
        eva_context['state'] = 'listening_without_cam'
        eva_led.set(Loop('b'))
        mic.start()

        # Add a timeout to execute a transition funcion due to inactivity
        listen_timer = threading.Timer(DELAY_TIMEOUT, listen_timeout_handler)
        listen_timer.start()

    elif transition == 'speaking2idle_presence' and eva_context['state'] == 'speaking':
        eva_context['state'] = 'idle_presence' 
        eva_led.set(StaticColor('black'))
        rf.stop()
        pd.start()
        wf.start()
    
    elif transition == 'listening_without_cam2idle_presence'and eva_context['state'] == 'listening_without_cam':
        eva_context['state'] = 'idle_presence'
        eva_context['continue_conversation'] =  False
        eva_context['proactive_question'] =  ''
        eva_context['tg_destination_name'] = ''
        #eva_eyes.set('neutral')
        eva_led.set(Close('blue'))
        mic.stop()
        rf.stop()
        pd.start()
        wf.start()

    elif transition == 'proactive2processingquery':
        if params['question'] == 'how_are_you':
            if eva_context['state'] == 'idle_presence':
                eva_context['state'] = 'processing_query'
                eva_led.set(StaticColor('black'))
                wf.stop()
                pd.stop()

                try:
                    audio_response = server.tts(ProactivePhrases.get(params['question']))
                except Exception as e:
                    eva_context['continue_conversation'] = False
                    eva_context['proactive_question'] = ''
                    eva_context['state'] = 'speaking'
                    eva_led.set(Breath('r'))
                    speaker.start(connection_error_audio)

                    proactive.update('abort', 'how_are_you')

                else:
                    eva_context['proactive_question'] = 'how_are_you'
                    eva_context['continue_conversation'] = True
                    eva_context['state'] = 'speaking'
                    eva_led.set(Breath('b'))
                    speaker.start(audio_response)
                    try:
                        server.prepare()
                    except Exception as e:
                        pass # TODO: logging

                    proactive.update('confirm', 'how_are_you')

            else:
                proactive.update('abort', 'how_are_you')
            
        elif params['question'] == 'who_are_you':
            if eva_context['state'] == 'listening':
                eva_context['state'] = 'processing_query'
                eva_led.set(StaticColor('black'))
                mic.stop()
                wf.stop()

                try:
                    audio_response = server.tts(ProactivePhrases.get(params['question']))    
                except Exception as e:
                    eva_context['continue_conversation'] = False
                    eva_context['proactive_question'] = ''
                    eva_context['state'] = 'speaking'
                    eva_led.set(Breath('r'))
                    speaker.start(connection_error_audio)

                    proactive.update('abort', 'who_are_you')
                else:
                    eva_context['proactive_question'] = 'who_are_you'
                    eva_context['continue_conversation'] = True
                    eva_context['state'] = 'speaking'
                    eva_led.set(Breath('b'))
                    speaker.start(audio_response)
                    try:
                        server.prepare()
                    except Exception as e:
                        pass # TODO logging

                    proactive.update('confirm', 'who_are_you')
            else:
                proactive.update('abort', 'who_are_you')
            
        elif params['question'] == 'read_pending_messages':
            if eva_context['state'] in ['listening', 'idle_presence']:
                eva_led.set(StaticColor('black'))
                if eva_context['state'] == 'listening': mic.stop()
                wf.stop()
                if eva_context['state'] == 'idle_presence': pd.stop()
                eva_context['state'] = 'processing_query'

                try:
                    # Fusion messages
                    text = '. '.join(
                        f'{name} te ha escrito {"un mensaje que dice" if len(messages) == 1 else "varios mensajes que dicen"}: {". ".join(messages)}'
                        for name, messages in params['messages'].items()
                    )
                    print(text)

                    # Generate the audio
                    audio_response = server.tts(text)    

                except Exception as e:
                    eva_context['continue_conversation'] = False
                    eva_context['proactive_question'] = ''
                    eva_context['state'] = 'speaking'
                    eva_led.set(Breath('r'))
                    speaker.start(connection_error_audio)

                    proactive.update('abort', 'read_pending_messages')
                else:
                    eva_context['continue_conversation'] = False
                    eva_context['state'] = 'speaking'
                    eva_led.set(Breath('g'))
                    speaker.start(audio_response)

                    proactive.update('confirm', 'read_pending_messages')
            else:
                proactive.update('abort', 'read_pending_messages')


    elif transition == 'recording_face':
        eva_led.set(Progress(percentage=params['progress']))

        if params['progress'] == 100:
            rf.stop()
            if eva_context['state'] == 'listening_without_cam':
                eva_led.set(Loop('b'))
            elif eva_context['state'] == 'recording':
                eva_led.set(Loop('w'))
            else:
                eva_led.set(StaticColor('black'))


    elif transition == 'received_tg_message':
        if eva_context['state'] in ['idle_presence', 'listening']:
            eva_led.set(StaticColor('black'))
            if eva_context['state'] == 'listening': mic.stop()
            wf.stop()
            if eva_context['state'] == 'idle_presence': pd.stop()
            eva_context['state'] = 'processing_query'

            try:
                audio_response = server.tts(f'{params["name"]} te ha escrito un mensaje que dice: {params["message"]}')    
            except Exception as e:
                eva_context['continue_conversation'] = False
                eva_context['proactive_question'] = ''
                eva_context['state'] = 'speaking'
                eva_led.set(Breath('r'))
                speaker.start(connection_error_audio)

            else:
                eva_context['continue_conversation'] = False
                eva_context['state'] = 'speaking'
                eva_led.set(Breath('g'))
                speaker.start(audio_response)
        
        else:
            # Pass message to proactive service, to read it later
            proactive.update('sensor', 'received_tg_message', params)



        
    

eva_led = EvaLed()
#eva_eyes = EvaEyes()
FaceDB.load()
ProactivePhrases.load()

wf = Wakeface(wf_event_handler)
rf = RecordFace(rf_event_handler)
pd = PresenceDetector(pd_event_handler)

proactive = ProactiveService(proactive_service_event_handler)

speaker = Speaker(speaker_event_handler)
mic = Recorder(mic_event_handler)

tg = TelegramService(tg_event_handler)

eva_context = {
    'state':'idle', 
    'username':None, 
    'continue_conversation': False, 
    'proactive_question': '', 
    'tg_destination_name': ''
}

pd.start()



print('Start!')
try:
    while True:
        notification = notifications.get()

        transition = notification['transition']
        params = notification.get('params', {})
        process_transition(transition, params)
except KeyboardInterrupt:
    pass
    

wf.stop()
rf.stop()
pd.stop()
mic.stop()
speaker.destroy()
eva_led.stop()
#eva_eyes.stop()
tg.stop()

logging.info(f'UI finished')
