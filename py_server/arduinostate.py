from collections import namedtuple

# named tuple of values for an arduino state.
# all data is numbers in the range [0,1]
# (if a number is out of range, it will be clamped.)
ArduinoState = namedtuple('ArduinoState', ['pump_power', 'ledR', 'ledG', 'ledB'])
