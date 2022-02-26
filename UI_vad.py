import webrtcvad
vad = webrtcvad.Vad()



#https://github.com/jeysonmc/python-google-speech-scripts/blob/master/stt_google.py
import pyaudio
from collections import deque

import time

import server



# recording configs
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1 # con 8 pasa cosa de que lo intenta reproducir a 8 channels
RATE = 16000 #24000

PREV_AUDIO = 1.0  # Previous audio (in seconds) to prepend. When noise
                  # is detected, how much of previously recorded audio is
                  # prepended. This helps to prevent chopping the beggining
                  # of the phrase.


#https://github.com/wiseman/py-webrtcvad/blob/master/example.py
def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    while offset + n < len(audio):
        yield audio[offset:offset + n]
        offset += n

def speak(audio):
        
    print("* playing response")
    # Create an interface to PortAudio
    speaker = pyaudio.PyAudio()

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
#Prepend audio from 0.5 seconds before noise was detected
prev_audio = deque(maxlen=int(PREV_AUDIO * rel)) 
started = False
in_conversation = True

def callback(in_data, frame_count, time_info, flag):
    global prev_audio, rel, audio2send, started
    isSpeech = False

    for frame in frame_generator(30, in_data, RATE):
        if vad.is_speech(frame, RATE):
            isSpeech = True
            break

    if isSpeech:
        if not started:
            audio2send = []
            print ("Starting record of phrase")
            started = True
            audio2send.extend(prev_audio)
        audio2send.append(in_data)
    elif started is True:
        print ("Finished")
        started = False
        prev_audio = deque(maxlen=int(PREV_AUDIO * rel)) 
        return (in_data, pyaudio.paComplete)
        
    else:
        prev_audio.append(in_data)
        
    
    return (in_data, pyaudio.paContinue)


def start_recording():
    #Open stream
    p = pyaudio.PyAudio()
    in_conversation = True

    while in_conversation:
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
            
            # TEMPORAL: TODO: QUITARLO
            break
    
        except KeyboardInterrupt:
            break

    print ("* Done :D")
    p.terminate()

def stop_recording():
    global in_conversation
    in_conversation = False

