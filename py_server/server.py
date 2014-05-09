import json
import os
import sys
import threading
import time
import serial
import Queue
import tornado.ioloop
import tornado.web
import tornado.websocket

from serial.tools import list_ports
from tornado.options import define, options, parse_command_line

ARDUINO_WRITE_FREQ = 100 # approximate Hz

# add command line option for port number
define("port", default=8080, help="run on the given port", type=int)

class AtomicReference(object):
    """
    Threadsafe reference.
    Beware of mutating the data itself.
    """
    def __init__(self, value):
        self._val = value
        self._lock = threading.Lock()

    def get(self, ):
        self._lock.acquire(True)
        value = self._val
        self._lock.release()
        return value

    def set(self, value):
        self._lock.acquire(True)
        self._val = value
        self._lock.release()


## state variables
# threadsafe queue of received data
data_queue = Queue.Queue(maxsize=0) # maxsize=0 means unlimited capacity

# threadsafe container with the state to tell the arduino to be.
# format: (pump_power,) where all data is a number in the range [0,1]
arduino_state = AtomicReference((0,))

# a list of known substrings of serial addresses to try to connect to.
# if None, then skip connecting
serial_addr_subs = ["ACM", "usbmodem", "usbserial"]
# serial connection to arduino, could be None if connection fails
arduino_serial = None

# response handler for web sockets
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        print("received a message: {}".format(message))
        try:
            obj = json.loads(message)
        except ValueError:
            print "INVALID JSON. SKIPPING."
            return
        data_queue.put(obj)

app = tornado.web.Application([
    (r'/', WebSocketHandler),
])


# process new data
# current_arduino_state is an (unwrapped) arduino state
# output a new (unwrapped) arduino state
def process_data(newdata, current_arduino_state):
    print("processing new data: {}".format(newdata))
    dtype = newdata['type']
    dval = newdata['value']

    (pump_power,) = current_arduino_state

    if newdata['type'] == 'audio-volume':
        baseline = -160
        max_delta = 30
        pump_power = (dval - baseline) / max_delta

    return (pump_power,)

# take an (unwrapped) state and write it to the arduino
def write_to_arduino(state):
    print("writing to arduino", state)
    if arduino_serial != None:
        for val in state:
            arduino_serial.write(convert_float_letter(val))


def process_data_thread():
    print "process_data started"
    while True:
        # block on new data
        newdata = data_queue.get()
        print("processing new data: {}".format(newdata))
        current_arduino_state = arduino_state.get()
        newstate = process_data(newdata, current_arduino_state)
        arduino_state.set(newstate)

def write_to_arduino_thread():
    print "write_to_arduino_thread started"
    while True:
        # block on new data
        state = arduino_state.get()
        write_to_arduino(state)
        time.sleep(1 / float(ARDUINO_WRITE_FREQ))

# convert a float to a letter in [a, z]
# ['a', 'z'] maps to [0, 1]
# anything floats out of bounds will be clamped. So 1.7 is 'z'
def convert_float_letter(num):
    num = max(0, min(float(num), 1))
    range_width = ord('z') - ord('a')
    return chr(ord('a') + int(num * range_width))


# Provides all serial port names as strings
def serial_ports():
    if os.name == "nt":
        for i in range(256):
            try:
                s = serial.Serial(i)
                s.close()
                yield 'COM' + str(i + 1)
            except serial.SerialException:
                pass
    else:
        for port in list_ports.comports():
            yield port[0]


# returns a serial object or None
def connect_to_serial(serial_addr_subs):
    for port in list(serial_ports()):
        for sub in serial_addr_subs:
            if sub in port:
                ser = serial.Serial(port)
                print("Conneced to serial port: " + ser.port)
                return ser
                # ser.timeout = 0.5
                # ser.write('c')
                # msg = ser.read()
                # if msg == 'y':
                #     continue
    return None # if no matches


def start_daemon_thread(fn):
    thread = threading.Thread(target=fn)
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    try:
        # Initializing arduino connection
        if serial_addr_subs != None:
            print("Initializing arduino connection...")
            arduino_serial = connect_to_serial(serial_addr_subs)
            if arduino_serial == None:
                print("\n\n")
                print("! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ")
                print("COULD NOT FIND ANY MATCHING SERIAL PORTS")
                print("! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ")
                print("\n\n")
                raw_input("Press <enter> if this is ok.\n")
        else:
            print("Skipping arduino connection")
            arduino_serial = None

        parse_command_line()
        app.listen(options.port)
        start_daemon_thread(write_to_arduino_thread)
        start_daemon_thread(process_data_thread)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print "GOODBYE"
        sys.exit()
