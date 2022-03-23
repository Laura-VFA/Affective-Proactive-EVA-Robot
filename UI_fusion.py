import time
import logging
import server
from services.eva_led import *
from services.wakeface import Wakeface
from services.mic import Recorder
from services.speaker import Speaker
import queue


# Logging configuration
logging.basicConfig(filename='./logs/UI.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
#log = logging.getLogger('STDERR')


notifications = queue.Queue()

def wf_event_handler(event, username=None, progress=None):
    global eva_state, _username
    notification = {
        'transition': '',
        'params': {
            'username':username,
            'progress': progress
        }
    }
    if event == 'face_listen' and eva_state == 'idle':
        notification['transition'] = 'idle2listening'
        notifications.put(notification)
    elif event in ['face_not_listen', 'not_faces'] and eva_state == 'listening':
        notification['transition'] = 'listening2idle'
        notifications.put(notification)

        if event == 'not_faces':
            _username = None
    elif event == 'recording_face':
        notification['transition'] = 'recording_face'
        notifications.put(notification)
    

def mic_event_handler(event, audio=None):
    notification = {
        'transition': '',
        'params': {
            'audio': audio
        }
    }
    if event == 'start_recording' and eva_state in ['listening', 'listening_without_cam']:
        if eva_state == 'listening':
            notification['transition']  = 'listening2recording'
        elif eva_state == 'listening_without_cam':
            notification['transition']  = 'listening_without_cam2recording'
        notifications.put(notification)
    if event == 'stop_recording' and eva_state == 'recording':
        notification['transition']  = 'recording2processingquery'
        notifications.put(notification)
    

def process_transition(transition, params):
    global eva_state, _username

    if transition == 'idle2listening':
        eva_led.set(Listen())
        eva_state = 'listening'
        mic.start()

        username = params['username']

        if username : 
            print(username)
            _username = username
        else:
            _username = None

    elif transition == 'listening2idle':
        eva_led.set(Neutral())
        eva_state = 'idle'
        mic.stop()

    elif transition == 'listening2recording':
        eva_state = 'recording'
        eva_led.set(Recording())
        server.prepare()
        #disconnect camera
        wf.stop()
    
    elif transition == 'listening_without_cam2recording':
        eva_state = 'recording'
        eva_led.set(Recording())
        server.prepare()

    elif transition == 'recording2processingquery':
        eva_state = 'processing_query'
        eva_led.set(Neutral())
        mic.stop()

        audio = params['audio']

        audio_response, action, continue_conversation = server.query(audio, _username)

        if audio_response:
            eva_state = 'speaking'
            eva_led.set(Breath())
            speaker.play(audio_response)

        if action: # Execute associated action
            # Switch con tipos de acciones
            if action[0] == 'record_face':
                wf.record_face(action[1])
        
        if continue_conversation:
            eva_led.set(Listen())
            eva_state = 'listening_without_cam'
            mic.start()

        else:   
            eva_state = 'idle' 
            eva_led.set(Neutral())
            wf.start()
    
    elif transition == 'recording_face':
        eva_led.set(Progress(params['progress']))
    


        
    

eva_led = EvaLed()
wf = Wakeface(wf_event_handler)
speaker = Speaker()
mic = Recorder(mic_event_handler)
eva_state = 'idle'
_username = None
wf.start()


print('Start!')
try:
    while True:
        time.sleep(0.1)
        notification = notifications.get()
        
        transition = notification['transition']
        params = notification['params']
        process_transition(transition, params)
except KeyboardInterrupt:
    pass
    

wf.stop()
mic.stop()
speaker.destroy()
eva_led.stop()

logging.info(f'UI finished')