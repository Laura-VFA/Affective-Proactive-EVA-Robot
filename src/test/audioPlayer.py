# SOLUCIONAR POPPING

import pyaudio
import wave

filename = 'output.wav'

# Set chunk size of 1024 samples per data frame
CHUNK = 2048
FORMAT = pyaudio.paInt16
#CHANNELS = 2 # con 8 pasa cosa de que lo intenta reproducir a 8 channels
CHANNELS = 1
#RATE = 8000
RATE = 16000 

# Open the sound file 
wf = wave.open(filename, 'rb')

# Create an interface to PortAudio
p = pyaudio.PyAudio()

# Open a .Stream object to write the WAV file to
# 'output = True' indicates that the sound will be played rather than recorded
'''
stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                output = True,
                output_device_index=1,
                frames_per_buffer=CHUNK)
'''

stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=1
                #,frames_per_buffer=CHUNK
                )
                

# Read data in chunks
data = wf.readframes(CHUNK)

# Play the sound by writing the audio data to the stream
while data != b'':
    stream.write(data)
    data = wf.readframes(CHUNK)

# Close and terminate the stream
stream.close()
p.terminate()


# Popping raro, y encima peta ... algo pasa