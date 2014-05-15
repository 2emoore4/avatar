"""
This machine talks to the fountain arduino
and receives data over the network from clients with sensors.
"""

import json
import os
import sys
import threading
import traceback
import time
import serial
import Queue
import tornado.ioloop
import tornado.web
import tornado.websocket

from serial.tools import list_ports
from tornado.options import define, options, parse_command_line

from atomicreference import AtomicReference
from arduinostate import ArduinoState
from processor import Processor

DEBUG_NET_COMM = True
DEBUG_ARDUINO_COMM = False
DEBUG_PROCESSOR = True

ARDUINO_WRITE_FREQ = 100 # approximate Hz

# add command line option for port number
define("port", default=8080, help="run on the given port", type=int)

## state variables
# threadsafe queue of received data
data_queue = Queue.Queue(maxsize=0) # maxsize=0 means unlimited capacity

# threadsafe container with the state to tell the arduino to be.
# see ArduinoState for data format
arduino_state = AtomicReference(ArduinoState(pump_power=0, ledR=0, ledG=0, ledB=0))

# data processor (not threadsafe)
# the processor stores persistent data and figures out how
# to turn data received into an output state
processor = Processor(arduino_state)

# a list of known substrings of serial addresses to try to connect to.
# if None, then skip connecting
serial_addr_subs = ["ACM", "usbmodem", "usbserial"]
# serial connection to arduino, could be None if connection fails
arduino_serial = None

# response handler for web sockets
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        if DEBUG_NET_COMM: print("received a message: {}".format(message))
        try:
            obj = json.loads(message)
        except ValueError:
            if DEBUG_NET_COMM: print "INVALID JSON. SKIPPING."
            return
        data_queue.put(obj)

app = tornado.web.Application([
    (r'/', WebSocketHandler),
])


# take an (unwrapped) state and write it to the arduino
def write_to_arduino(state):
    if DEBUG_ARDUINO_COMM: print("writing to arduino", state)
    if arduino_serial != None:
        try:
            arduino_serial.write('*')
            for val in state:
                arduino_serial.write(convert_float_letter(val))
            arduino_serial.flush()
        except serial.SerialException as ex:
            print ex
            traceback.print_exc()
            os._exit(1)


def process_data_thread():
    print "process_data started"
    while True:
        # block on new data
        newdata = data_queue.get()
        if DEBUG_NET_COMM: print("processing new data: {}".format(newdata))
        current_arduino_state = arduino_state.get()
        try:
            newstate = processor.on_new_data(newdata, current_arduino_state)
            if DEBUG_PROCESSOR: print "-- frame --"
            if DEBUG_PROCESSOR: processor.debug_print()
            if DEBUG_PROCESSOR: print newstate
            # enforce bounds
            newstate = ArduinoState(*(max(0, min(val, 1)) for val in newstate))
        except Exception as ex:
            print ex
            traceback.print_exc()
            os._exit(1)
        arduino_state.set(newstate)

def write_to_arduino_thread():
    print "write_to_arduino_thread started"
    while True:
        # block on new data
        state = arduino_state.get()
        write_to_arduino(state)
        time.sleep(1 / float(ARDUINO_WRITE_FREQ))

def read_from_arduino_thread():
    print "read_from_arduino_thread started"
    while True:
        if arduino_serial != None:
            message = arduino_serial.readline()
            if DEBUG_ARDUINO_COMM: print("arduino serial: {}".format(message.strip()))

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
            print("Skipping arduino connection.")
            arduino_serial = None

        parse_command_line()
        app.listen(options.port)
        start_daemon_thread(write_to_arduino_thread)
        start_daemon_thread(read_from_arduino_thread)
        start_daemon_thread(process_data_thread)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print "GOODBYE"
        sys.exit()
