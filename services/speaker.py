import pyaudio

class Speaker:
    def __init__(self, chunk_size=2048, format=pyaudio.paInt16, channels=1, rate=24000) :
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels
        self.rate = rate  

        self.p = pyaudio.PyAudio() # Create an interface to PortAudio
    
    def play(self, audio):
        print("* Playing response")

        stream = self.p.open(format = self.format,
                        channels = self.channels,
                        rate = self.rate,
                        output = True,
                        output_device_index=1
                        #,frames_per_buffer=len(audio)
                        )
        
        # Play the audio
        stream.write(audio)

        # Close and terminate the stream
        stream.close()
    
    def destroy(self):
        self.p.terminate()



