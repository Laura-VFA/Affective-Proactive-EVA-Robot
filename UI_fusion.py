import logging
import queue
import threading
import time

import server
from services.camera_service import FaceDB, PresenceDetector, RecordFace, Wakeface
from services.eva_led import *
from services.mic import Recorder
from services.speaker import Speaker

# Logging configuration
logging.basicConfig(filename='./logs/UI.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
#log = logging.getLogger('STDERR')


notifications = queue.Queue()
listen_timer = None
DELAY_TIMEOUT = 5 # in sec


def wf_event_handler(event, username=None):
    global eva_context

    if event == 'face_listen' and eva_context['state'] == 'idle_presence':
        notifications.put({'transition': 'idle_presence2listening'})
    
    elif event in ['face_not_listen', 'not_faces']:
        eva_context['username'] = None

        if eva_context['state'] == 'listening':
            notifications.put({'transition': 'listening2idle_presence'})
        
    elif event == 'face_recognized':
        eva_context['username'] = username


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



def listen_timeout_handler():
    global eva_context
    notifications.put({'transition': 'listening_without_cam2idle_presence'})


def process_transition(transition, params):
    global eva_context, listen_timer

    if transition == 'idle2idle_presence' and eva_context['state'] == 'idle':
        eva_led.set(StaticColor('purple'))
        eva_context['state'] = 'idle_presence'
        wf.start()
    
    if transition == 'idle_presence2idle' and eva_context['state'] == 'idle_presence':
        eva_led.set(Neutral())
        eva_context['state'] = 'idle'
        wf.stop()

    if transition == 'idle_presence2listening' and eva_context['state'] == 'idle_presence':
        eva_led.set(Listen())
        eva_context['state'] = 'listening'
        pd.stop()
        mic.start()

    elif transition == 'listening2idle_presence' and eva_context['state'] == 'listening':
        eva_led.set(Neutral())
        eva_context['state'] = 'idle_presence'
        mic.stop()
        pd.start()

    elif transition == 'listening2recording' and eva_context['state'] == 'listening':
        eva_context['state'] = 'recording'
        eva_led.set(Recording())
        server.prepare()
        #disconnect camera
        wf.stop()
    
    elif transition == 'listening_without_cam2recording' and eva_context['state'] == 'listening_without_cam':
        eva_context['state'] = 'recording'
        eva_led.set(Recording())
        server.prepare()

        listen_timer.cancel()

    elif transition == 'recording2processingquery' and eva_context['state'] == 'recording':
        eva_context['state'] = 'processing_query'
        eva_led.set(Neutral())
        mic.stop()

        audio = params['audio']

        audio_response, action, continue_conversation = server.query(audio, eva_context['username'])

        eva_context['continue_conversation'] = continue_conversation

        if action: # Execute associated action
            # Switch con tipos de acciones
            if action[0] == 'record_face':
                eva_context['username'] = action[1]
                rf.start(action[1])

        if audio_response:
            eva_context['state'] = 'speaking'
            eva_led.set(Breath())
            speaker.start(audio_response)
        else:
            eva_led.set(Neutral())
            eva_context['state'] = 'idle_presence'
            pd.start()
            wf.start()

    elif transition == 'speaking2listening_without_cam' and eva_context['state'] == 'speaking':
        eva_context['state'] = 'listening_without_cam'
        eva_led.set(Listen())
        mic.start()

        # Add a timeout to execute a transition funcion due to inactivity
        listen_timer = threading.Timer(DELAY_TIMEOUT, listen_timeout_handler)
        listen_timer.start()

    elif transition == 'speaking2idle_presence' and eva_context['state'] == 'speaking':
        eva_context['state'] = 'idle_presence' 
        eva_led.set(Neutral())
        pd.start()
        wf.start()
    
    elif transition == 'listening_without_cam2idle_presence'and eva_context['state'] == 'listening_without_cam':
        eva_context['state'] = 'idle_presence'
        eva_led.set(Close())
        mic.stop()
        pd.start()
        wf.start()
    

    elif transition == 'recording_face':
        eva_led.set(Progress(params['progress']))

        if params['progress'] == 100:
            if eva_context['state'] == 'listening_without_cam':
                eva_led.set(Listen())
            elif eva_context['state'] == 'recording':
                eva_led.set(Recording())
            else:
                eva_led.set(Neutral())

    


        
    

eva_led = EvaLed()
FaceDB.load()

wf = Wakeface(wf_event_handler)
rf = RecordFace(rf_event_handler)
pd = PresenceDetector(pd_event_handler)

speaker = Speaker(speaker_event_handler)
mic = Recorder(mic_event_handler)

eva_context = {'state':'idle', 'username':None, 'continue_conversation': False}
#wf.start()
pd.start()



print('Start!')
try:
    while True:
        time.sleep(0.1)
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

logging.info(f'UI finished')
