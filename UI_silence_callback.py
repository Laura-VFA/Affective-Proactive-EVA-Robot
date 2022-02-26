#https://github.com/jeysonmc/python-google-speech-scripts/blob/master/stt_google.py

import pyaudio

import audioop
from collections import deque

import math
import time

import server

# recording configs
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1 # con 8 pasa cosa de que lo intenta reproducir a 8 channels
RATE = 16000 #24000
RECORD_SECONDS = 5


THRESHOLD = 1200  # The threshold intensity that defines silence
                  # and noise signal (an int. lower than THRESHOLD is silence).

SILENCE_LIMIT = 1  # Silence limit in seconds. The max ammount of seconds where
                   # only silence is recorded. When this time passes the
                   # recording finishes and the file is delivered.

PREV_AUDIO = 1.0  # Previous audio (in seconds) to prepend. When noise
                  # is detected, how much of previously recorded audio is
                  # prepended. This helps to prevent chopping the beggining
                  # of the phrase.


def audio_int(num_samples=50):
    """ Gets average audio intensity of your mic sound. You can use it to get
        average intensities while you're talking and/or silent. The average
        is the avg of the 20% largest intensities recorded.
    """

    print ("Getting intensity values from mic.")
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=3)

    values = [math.sqrt(abs(audioop.avg(stream.read(CHUNK), 4))) 
              for x in range(num_samples)] 
    values = sorted(values, reverse=True)
    r = sum(values[:int(num_samples * 0.2)]) / int(num_samples * 0.2)
    print (" Finished ")
    print (" Average audio intensity is ", r)
    stream.close()
    p.terminate()
    return r


def speak(audio):
        
    print("* playing response")
    # Create an interface to PortAudio
    speaker = pyaudio.PyAudio()

    # Open a .Stream object to write the WAV file to
    # 'output = True' indicates that the sound will be played rather than recorded
    #RATE_SPK = 12000
    #CHANNELS_SPK = 2
    RATE_SPK = 24000
    CHANNELS_SPK = 1

    stream_s = speaker.open(format = FORMAT,
                    channels = CHANNELS_SPK,
                    rate = RATE_SPK,
                    output = True,
                    output_device_index=1
                    #,frames_per_buffer=len(audio)
                    )
    
    # Play the audio
    stream_s.write(audio)

    # Close and terminate the stream
    stream_s.close()
    speaker.terminate()


audio2send = []
rel = RATE/CHUNK
slid_win = deque(maxlen=int(SILENCE_LIMIT * rel))
#Prepend audio from 0.5 seconds before noise was detected
prev_audio = deque(maxlen=int(PREV_AUDIO * rel)) 
started = False


def callback(in_data, frame_count, time_info, flag):
    global slid_win, prev_audio, rel, audio2send, started
    slid_win.append(math.sqrt(abs(audioop.avg(in_data, 4))))
    if sum([x > THRESHOLD for x in slid_win]) > 0:
        if not started:
            audio2send = []
            print ("Starting record of phrase")
            started = True
            audio2send.extend(prev_audio)
        audio2send.append(in_data)
    elif started is True:
        print ("Finished")
        started = False
        slid_win = deque(maxlen=int(SILENCE_LIMIT * rel))
        prev_audio = deque(maxlen=int(PREV_AUDIO * rel)) 
        return (in_data, pyaudio.paComplete)
        
    else:
        prev_audio.append(in_data)
    
    return (in_data, pyaudio.paContinue)



#Open stream
p = pyaudio.PyAudio()


while True:
    try:
        print( "* Listening mic. ")
        stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=3,
                stream_callback=callback)


        while stream.is_active():
            time.sleep(0.1)
        
        stream.close()

        print("* sending query")
        r = server.query(b''.join(audio2send)) 

        if r is not None:
            speak(r)
   
    except KeyboardInterrupt:
        break

print ("* Done :D")
p.terminate()

