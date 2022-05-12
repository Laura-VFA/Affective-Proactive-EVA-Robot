from threading import Thread

import pyaudio


class Speaker:
    def __init__(self, callback, chunk_size=2048,
                 format=pyaudio.paInt16, channels=1, rate=24000):
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
        print("* Playing response") # TODO logging

        stream = self.p.open(format = self.format,
                        channels = self.channels,
                        rate = self.rate,
                        output = True,
                        output_device_index=1
                        )

        stream.write(audio)
        stream.close()

        self.callback('finish_speak')
    
    def destroy(self):
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

        self.p.terminate()
