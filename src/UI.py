# TODO ACABARRRR

import pyaudio
import wave
from server import query


# recording configs
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1 # con 8 pasa cosa de que lo intenta reproducir a 8 channels
RATE = 96000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

# create & configure microphone
mic = pyaudio.PyAudio()


stream = mic.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=3)

print("* recording")

# read & store microphone data per frame read
frames = []

chunk = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1 # con 8 pasa cosa de que lo intenta reproducir a 8 channels
RATE = 16000

