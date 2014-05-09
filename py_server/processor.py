class Processor(object):
    """
    Interprets and massages data from inputs to format outputs.
    This is a class because it can include persistent storage.
    """
    def __init__(self):
        pass

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
            baseline = -154 # basically zero-sound value
            max_delta = 6 # roughly maximum loudness change expected
            delta = dval - baseline
            print delta
            pump_power = delta / max_delta

        # construct new state
        return (pump_power,)
