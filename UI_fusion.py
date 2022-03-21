import time
import logging
import server
from services.eva_led import *
from services.wakeface import Wakeface
from services.mic import Recorder
from services.speaker import Speaker


# Logging configuration
logging.basicConfig(filename='./logs/UI.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
#log = logging.getLogger('STDERR')


def wf_event_handler(event, username=None, progress=None):
    global eva_state, _username
    logging.info(f'WF Event {event}')
    if event == 'face_listen' and eva_state in ['idle', 'recording_face']:
        eva_led.set(Listen())
        # open mic here!
        eva_state = 'listening'
        mic.start()
        logging.info('WF Eva listening - Mic started')

        if username : 
            print(username)
            _username = username
            logging.info(f'WF username updated {username}')
        else:
            _username = None
        
    elif event in ['face_not_listen', 'not_faces'] and eva_state == 'listening':
        eva_led.set(Neutral())
        # close mic here
        eva_state = 'idle'
        mic.stop()
        logging.info('WF Eva Idle - Mic stopped')

        if event == 'not_faces':
            _username = None

    elif event == 'recording_face':
        eva_led.set(Progress(progress))
    

def mic_event_handler(event, audio=None):
    global eva_state, _username
    logging.info(f'MIC Event {event}')
    if event == 'start_recording' and eva_state == 'listening':
        eva_state = 'recording'
        eva_led.set(Recording())
        server.prepare()
        #disconnect camera
        wf.stop()

        logging.info(f'MIC Eva Recording - Wf stopped')
        
    if event == 'stop_recording' and eva_state == 'recording':
        eva_state = 'processing_query'
        eva_led.set(Neutral())
        audio_response, action = server.query(audio, _username)

        logging.info(f'MIC Eva Processing Query')

        if audio_response:
            logging.info(f'MIC Eva Speaking')
            eva_state = 'speaking'
            eva_led.set(Breath())
            speaker.play(audio_response)

        if action: # Execute associated action
            logging.info(f'MIC Eva Executing action {action}')
            # Switch con tipos de acciones
            if action[0] == 'record_face':
                #eva_led.set(Recording_face())
                wf.record_face(action[1])

        eva_state = 'idle' # TEMPORAL
        eva_led.set(Neutral())
        wf.start()

        logging.info(f'MIC Eva Idle - Wf started')



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

logging.info(f'UI finished')