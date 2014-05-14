from collections import deque

EXPECTED_VOLUME_ZERO = -155 # basically zero-sound value
EXPECTED_VOLUME_DELTA = 6 # roughly maximum volume change expected
VOLUME_MEM = 10

class Processor(object):
    """
    Interprets and massages data from inputs to format outputs.
    This is a class because it can include persistent storage.
    """
    def __init__(self):
        self.volume = RollingNumber(EXPECTED_VOLUME_ZERO, VOLUME_MEM)

    def on_new_data(self, newdata, last_arduino_state):
        """
        Process new data.

        newdata is of the form {'type': 'audio-volume', 'value': 0.8}
        last_arduino_state is an (unwrapped) arduino state
        returns a new (unwrapped) arduino state
        """
        dtype, dval = newdata['type'], newdata['value']

        # deconstruct old state
        (pump_power,) = last_arduino_state

        if newdata['type'] == 'audio-volume':
            vol = self.volume
            vol.record(dval)
            delta = vol.avg() - EXPECTED_VOLUME_ZERO
            pump_power = delta / EXPECTED_VOLUME_DELTA
            # pump_power = maprange(vol.last(), vol.min(), vol.max(), 0, 1)
        elif newdata['type'] == 'command':
            print "received message: " + newdata['value']

        # construct new state
        return (pump_power,)

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
