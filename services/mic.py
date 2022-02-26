from collections import deque
from threading import Event, Thread

import pyaudio
import webrtcvad


class Recorder:
    def __init__(self, callback, chunk_size=2048, format=pyaudio.paInt16, channels=1, rate = 16000, prev_audio_size=1.0) -> None:
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels # con 8 pasa cosa de que lo intenta reproducir a 8 channels
        self.rate = rate
        self.prev_audio_size = prev_audio_size  # Previous audio (in seconds) to prepend. When noise
                                        # is detected, how much of previously recorded audio is
                                        # prepended. This helps to prevent chopping the beggining
                                        # of the phrase.
    
        self.audio2send = []
        #Prepend audio from 1.0 seconds before noise was detected
        self.prev_audio = deque(maxlen=int(prev_audio_size * rate/chunk_size)) 
        
        self.p = pyaudio.PyAudio()
        self.vad = webrtcvad.Vad(3) # maximo agresivo

        self._thread = None
        self.stopped = Event()
        self.start_recording = Event()
        self.stop_recording = Event()
        self.callback = callback

    
    def on_data(self, in_data, frame_count, time_info, flag):
        is_speech = False

        for frame in frame_generator(30, in_data, self.rate):
            if self.vad.is_speech(frame, self.rate):
                is_speech = True
                break

        if is_speech:
            if not self.start_recording.is_set():
                self.audio2send = []
                #print ("Starting record of phrase")
                self.start_recording.set()
                self.audio2send.extend(self.prev_audio)
            self.audio2send.append(in_data)

        elif self.start_recording.is_set():
            #print ("Finished recording")
            self.start_recording.clear()
            self.stop_recording.set()
            self.prev_audio = deque(maxlen=int(self.prev_audio_size * self.rate/self.chunk_size)) 
            return (in_data, pyaudio.paComplete)
            
        else:
            self.prev_audio.append(in_data)
        
        return (in_data, pyaudio.paContinue)


    
    def start(self):
    
        self.stopped.clear()
        self.start_recording.clear()
        self.stop_recording.clear() # evento he parado de grabar

        print( "* Mic opened ")
        self.stream = self.p.open(format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=3,
                stream_callback=self.on_data)
        
        self._thread = Thread(target=self._run)
        self._thread.start()

    def _run(self):

        #while not self.stopped.is_set():
        self.start_recording.wait()
        if self.stopped.is_set():
            return

        self.callback('start_recording')

        self.stop_recording.wait()
        if self.stopped.is_set():
            return

        self.callback('stop_recording', b''.join(self.audio2send))
        self.stream.close()


    def stop(self):

        self.stopped.set()
        self.start_recording.set()
        self.stop_recording.set()
        
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

        self.stream.close()
        self.start_recording.clear()
        self.stop_recording.clear()

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
    
