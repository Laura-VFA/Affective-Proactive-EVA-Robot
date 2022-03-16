import time

import server
from services.eva_led import *
from services.wakeface import Wakeface
from services.mic import Recorder
from services.speaker import Speaker


def wf_event_handler(event, username=None):
    global eva_state, _username
    if event == 'face_listen' and eva_state in ['idle', 'recording_face']:
        eva_led.set(Listen())
        # open mic here!
        eva_state = 'listening'
        mic.start()

        if username : 
            print(username)
            _username = username
        
    elif event in ['face_not_listen', 'not_faces'] and eva_state == 'listening':
        eva_led.set(Neutral())
        # close mic here
        eva_state = 'idle'
        mic.stop()

        if event == 'not_faces':
            _username = None
    

def mic_event_handler(event, audio=None):
    global eva_state, _username
    print(event)
    if event == 'start_recording' and eva_state == 'listening':
        eva_state = 'recording'
        eva_led.set(Recording())
        server.prepare()
        #disconnect camera
        wf.stop()
        
    if event == 'stop_recording' and eva_state == 'recording':
        eva_state = 'processing_query'
        eva_led.set(Neutral())
        #audio_response, action = server.query(audio, _username)
        audio_response, action = audio, ('record_face', 'laura')

        if audio_response:
            eva_state = 'speaking'
            eva_led.set(Breath())
            speaker.play(audio_response)

        if action: # Execute associated action
            # Switch con tipos de acciones
            if action[0] == 'record_face':
                eva_led.set(Recording_face())
                wf.record_face(action[1])

        eva_state = 'idle' # TEMPORAL
        eva_led.set(Neutral())
        wf.start()



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
except KeyboardInterrupt:
    pass

wf.stop()
mic.stop()
speaker.destroy()
eva_led.stop()
