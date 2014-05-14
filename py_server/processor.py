import threading
from collections import deque
from colorsys import hsv_to_rgb, rgb_to_hsv
from arduinostate import ArduinoState

EXPECTED_VOLUME_ZERO = -155 # basically zero-sound value
EXPECTED_VOLUME_DELTA = 6 # roughly maximum volume change expected
VOLUME_MEM = 10

class Processor(object):
    command_states = {
        'reset': ArduinoState(pump_power=0, ledR=0, ledG=0, ledB=0),
        'enter': ArduinoState(pump_power=0.5, ledR=0, ledG=1, ledB=0),
        'exit': ArduinoState(pump_power=0, ledR=1, ledG=0, ledB=0),
        'wake': ArduinoState(pump_power=0, ledR=1, ledG=1, ledB=1),
        'sleep': ArduinoState(pump_power=0, ledR=0, ledG=1, ledB=1),
        'start-talking': ArduinoState(pump_power=0, ledR=0, ledG=0, ledB=1),
        'stop-talking': ArduinoState(pump_power=0, ledR=0, ledG=1, ledB=1),
        'wave-gesture': ArduinoState(pump_power=0, ledR=0, ledG=0, ledB=1),
        'stop-gesture': ArduinoState(pump_power=0, ledR=1, ledG=0, ledB=0),
    }

    """
    Interprets and massages data from inputs to format outputs.
    This is a class because it can include persistent storage.
    """
    def __init__(self):
        self.volume = RollingNumber(EXPECTED_VOLUME_ZERO, VOLUME_MEM)
        self.volume_min = float('inf')

    def set_interval(func, milliseconds):
        def func_wrapper():
            set_interval(func, milliseconds/1000)
            func()
        t = threading.Timer(milliseconds/1000, func_wrapper)
        t.start()
        return t

    def set_timeout(func, milliseconds):
        def func_wrapper():
            func()
        t = threading.Timer(milliseconds/1000, func_wrapper)
        t.start()
        return t

    def on_new_data(self, newdata, last_state):
        """
        Process new data.

        newdata is of the form {'type': 'audio-volume', 'value': 0.8}
        last_state is an (unwrapped) arduino state
        returns a new (unwrapped) arduino state
        """
        dtype, dval = newdata['type'], newdata['value']

        # deconstruct old state
        (pump_power, ledR, ledG, ledB) = last_state.pump_power, last_state.ledR, last_state.ledG, last_state.ledB
        # convert colors
        led_hue, led_sat, led_val = rgb_to_hsv(ledR, ledG, ledB)

        if newdata['type'] == 'audio-volume':
            vol = self.volume
            vol.record(dval)
            self.volume_min = min(self.volume_min, dval)
            delta = vol.avg() - self.volume_min
            pump_power = delta / EXPECTED_VOLUME_DELTA
            # pump_power = maprange(vol.last(), vol.min(), vol.max(), 0, 1)
        elif newdata['type'] == 'light-intensity':
            light_val = maprange(dval, 800, 0, 0, 1)
            ledR = light_val
            ledG = light_val
            ledB = light_val
        elif newdata['type'] == 'command':
            print "received command: " + newdata['value']
            return self.command_states[dval]

        # led tracks pump power
        led_val = pump_power

        # rotate hue
        led_hue = (led_hue + 0.1) % 1.0

        # bound brightness
        led_val = min(led_val, 1.0)

        # convert colors
        ledR, ledG, ledB = hsv_to_rgb(led_hue, led_sat, led_val)
        # construct new state
        return ArduinoState(pump_power=pump_power, ledR=ledR, ledG=ledG, ledB=ledB)

    def debug_print(self):
        print "vol avg*: {}".format(self.volume.avg() - EXPECTED_VOLUME_ZERO)
        print "vol min*: {}".format(self.volume.min() - EXPECTED_VOLUME_ZERO)
        print "vol max*: {}".format(self.volume.max() - EXPECTED_VOLUME_ZERO)
        print "vol var : {}".format(self.volume.variance())
        print "vol lst*: {}".format(self.volume.last() - EXPECTED_VOLUME_ZERO)


def maprange(x, in_min, in_max, out_min, out_max):
    """
    Re-maps a number from one range to another.
    Courtesy of http://arduino.cc/en/Reference/Map
    x: the number to map
    in_min: the lower bound of the value's current range
    in_max: the upper bound of the value's current range
    out_min: the lower bound of the value's target range
    out_max: the upper bound of the value's target range
    """
    x, in_min, in_max, out_min, out_max = float(x), float(in_min), float(in_max), float(out_min), float(out_max)
    if in_min - in_max == 0.0:
        return out_min
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;


class RollingNumber(object):
    """
    A number stream with history.
    Can produce the average, min, and max of the number stream.

    Despite the 'rolling' in the class name, this class computes
    features of the recorded data in naive and slow ways.

    Invariant: 1 <= len(_history) <= mem_size
    """
    def __init__(self, initial_value, mem_size):
        """
        initial_value is the initial value of the number
        mem_size is how many samples to remember
        """
        self.mem_size = mem_size
        self._history = deque()
        self._history.append(initial_value)

    def record(self, value):
        """
        Add a new sample.
        """
        self._history.append(value)
        if len(self._history) > self.mem_size:
            self._history.popleft()

    def avg(self):
        """
        Retrieve the average value.
        """
        return float(sum(self._history)) / len(self._history)

    def min(self):
        """
        Retrieve the minimum value.
        """
        return min(self._history)

    def max(self):
        """
        Retrieve the maximum value.
        """
        return max(self._history)

    def last(self):
        """
        Retrieve the latest sample.
        """
        return self._history[-1]

    def variance(self):
        """
        Variance of the recorded values.
        """
        avg = self.avg()
        mean_of_squares = sum((v*v for v in self._history)) / len(self._history)
        square_of_mean = avg*avg
        return mean_of_squares - square_of_mean
