from matrix_lite import led
import time

# Get LED count
print('This device has ' + str(led.length) + ' Leds')

# A single string, object, or tuple will set all LEDs
# Below are different ways of expressing a color (number values are from 0-255)
led.set('blue')
led.set('#0000ff')
# Objects and tuples can utilize the white LED
led.set({'r':0, 'g':0, 'b':255, 'w':0 })
led.set((0,0,255,0))

# LEDs off
led.set('black')
led.set([])
led.set()
led.set({})

# Arrays set individual LEDs
led.set(['red', 'gold', 'purple', {}, 'black', '#6F41C1', 'blue', {'g':255}])

# Arrays can simulate motion
everloop = ['black'] * led.length
everloop[0] = {'b':100}

try:
    while True:
        everloop.append(everloop.pop(0))
        led.set(everloop)
        time.sleep(0.050)
except KeyboardInterrupt:
    led.set(['black'] * led.length)
