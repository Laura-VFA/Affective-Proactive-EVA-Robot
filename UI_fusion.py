import time

import server
from services.eva_led import *
from services.wakeface import Wakeface
from services.mic import Recorder
from services.speaker import Speaker


def wf_event_handler(event):
    global eva_state
    if event == 'face_listen' and eva_state == 'idle':
        eva_led.set(Listen())
        # open mic here!
        eva_state = 'listening'
        mic.start()
        
    elif event in ['face_not_listen', 'not_faces'] and eva_state == 'listening':
        eva_led.set(Neutral())
        # close mic here
        eva_state = 'idle'
        mic.stop()
    

def mic_event_handler(event, audio=None):
    global eva_state
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
        #audio_response = server.query(audio)
        audio_response = audio

        if audio_response:
            eva_state = 'speaking'
            eva_led.set(Breath())
            speaker.play(audio_response)

        eva_state = 'idle' # TEMPORAL
        eva_led.set(Neutral())
        wf.start()



eva_led = EvaLed()
wf = Wakeface(wf_event_handler)
speaker = Speaker()
mic = Recorder(mic_event_handler)
eva_state = 'idle'
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
