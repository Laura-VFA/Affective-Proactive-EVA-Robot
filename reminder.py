import time, pyaudio
from google_api  import getSpeechFromText

def speak(audio):
        
    print("* playing response")
    # Create an interface to PortAudio
    speaker = pyaudio.PyAudio()

    FORMAT = pyaudio.paInt16
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


def set_reminder(text, interval_sec):
    time.sleep(interval_sec)

    speak(getSpeechFromText(text))


