import pyaudio
from threading import Thread

class Speaker:
    def __init__(self, callback, chunk_size=2048, format=pyaudio.paInt16, channels=1, rate=24000) :
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels
        self.rate = rate  

        self.callback = callback
        self._thread = None

        self.p = pyaudio.PyAudio() # Create an interface to PortAudio
    
    def start(self, audio):
        self._thread= Thread(target=self.play, args=(audio,))
        self._thread.start()

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

        self.callback('finish_speak')
    
    def destroy(self):
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

        self.p.terminate()



