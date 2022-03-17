from matrix_lite import led
from math import pi, sin
from threading import Thread, Event
import time

class LedState:
    def __init__(self):
        pass

    def update(self):
        pass
'''
class Joy(LedState):
    def __init__(self):
        super().__init__()
        led.set('yellow')
'''
class Joy(LedState):
    def __init__(self):
        super().__init__()
        self.interval = int(255 / led.length)
        self.bright = [255 - i*self.interval for i in range(led.length)]
        self.bright.extend(self.bright[::-1])
        self.index = 0

    def update(self):
        led.set({'r': self.bright[self.index], 'g': self.bright[self.index]})
        self.index = (self.index + 1) % len(self.bright)


'''
class Anger(LedState):
    def __init__(self):
        super().__init__()
        led.set('red')
'''

class Anger(LedState):
    def __init__(self):
        super().__init__()
        self.interval = int(255 / led.length)
        self.bright = [255 - i*self.interval for i in range(led.length)]
        self.bright.extend(self.bright[::-1])
        self.index = 0

    def update(self):
        led.set({'r': self.bright[self.index]})
        self.index = (self.index + 1) % len(self.bright)

class Listen(LedState):
    def __init__(self):
        super().__init__()
        self.index = 0
        interval = int(255 / led.length)

        self.bright = [{'b': 255 - i * interval} for i in range(led.length)] * 2
        

    def update(self):

        led.set(self.bright[self.index : self.index + led.length])
        self.index = (self.index + 1) % led.length 

class Recording(LedState):
    def __init__(self):
        super().__init__()
        self.index = 0
        interval = int(255 / led.length)

        self.bright = [{'w': 255 - i * interval} for i in range(led.length)] * 2
        

    def update(self):

        led.set(self.bright[self.index : self.index + led.length])
        self.index = (self.index + 1) % led.length 

class Recording_face(LedState):
    def __init__(self):
        super().__init__()
        self.index = 0
        interval = int(255 / led.length)

        self.bright = [{'g': 255 - i * interval} for i in range(led.length)] * 2
        

    def update(self):

        led.set(self.bright[self.index : self.index + led.length])
        self.index = (self.index + 1) % led.length 

class Progress(LedState):
    def __init__(self, percentage=0):
        super().__init__()
        n_leds_light = int(percentage * led.length / 100)

        led.set(['green']*n_leds_light)

class Breath(LedState):
    def __init__(self):
        super().__init__()
        self.interval = int(255 / led.length)
        self.bright = [255 - i*self.interval for i in range(led.length)]
        self.bright.extend(self.bright[::-1])
        self.index = 0

    def update(self):
        led.set({'b': self.bright[self.index]})
        self.index = (self.index + 1) % len(self.bright)

class Neutral(LedState):
    def __init__(self):
        super().__init__()
        led.set('black')

class Rainbow(LedState):

    def __init__(self):
        self.everloop = ['black'] * led.length

        self.ledAdjust = 1.01 # MATRIX Voice

        self.frequency = 0.375
        self.counter = 0.0

    def update(self):
        for i in range(len(self.everloop)):
            r = round(max(0, (sin(self.frequency*self.counter+(pi/180*240))*155+100)/10))
            g = round(max(0, (sin(self.frequency*self.counter+(pi/180*120))*155+100)/10))
            b = round(max(0, (sin(self.frequency*self.counter)*155+100)/10))

            self.counter += self.ledAdjust

            self.everloop[i] = {'r':r, 'g':g, 'b':b}

        led.set(self.everloop)


class EvaLed:
    def __init__(self):
        self.state = Neutral()
        self.stopped = Event()
        self.start()
    
    def set(self, ledState:'LedState'):
        if self.state.__class__ != ledState.__class__:
            self.state = ledState
    
    def _run(self):
        while not self.stopped.is_set():
            self.state.update()
            time.sleep(0.050)
        
    def start(self):
        self.thread = Thread(target = self._run)
        self.stopped.clear()
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join()
        led.set('black')


