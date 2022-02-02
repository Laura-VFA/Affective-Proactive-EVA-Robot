# SOLUCIONAR POPPING

import pyaudio
import wave

filename = 'output.wav'

# Set chunk size of 1024 samples per data frame
chunk = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1 # con 8 pasa cosa de que lo intenta reproducir a 8 channels
RATE = 16000

# Open the sound file 
wf = wave.open(filename, 'rb')

# Create an interface to PortAudio
p = pyaudio.PyAudio()

# Open a .Stream object to write the WAV file to
# 'output = True' indicates that the sound will be played rather than recorded
stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                output = True,
                output_device_index=1)

# Read data in chunks
data = wf.readframes(chunk)

# Play the sound by writing the audio data to the stream
while data != '':
    stream.write(data)
    data = wf.readframes(chunk)

# Close and terminate the stream
stream.close()
p.terminate()