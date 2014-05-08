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

# add command line option for port number
define("port", default=8080, help="run on the given port", type=int)


## state variables
# queue of received data
data_queue = Queue.Queue(maxsize=0) # maxsize=0 means unlimited capacity

# queue of states to push to arduino
# these are read and written to the arduino as they arrive on the queue
# format: (pump_power,)
arduino_state = Queue.Queue(maxsize=0)
arduino_state.put((0,))

# a substring of the serial address to connect to for example "ACM" will match "/dev/ACM.0.tty"
# leave None to skip connecting to arduino.
serial_addr = None
# serial connection to arduino, could be None if connection fails
arduino_serial = None

# response handler for web sockets
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        print("received a message: %s" % (message))
        obj = json.loads(message)
        data_queue.put(data_queue)

app = tornado.web.Application([
    (r'/', WebSocketHandler),
])


def process_data():
    print "process_data started"
    while True:
        # block on new data
        newdata = data_queue.get()
        print("new data processed!", newdata)

def write_to_arduino():
    print "write_to_arduino started"
    while True:
        # block on new data
        state = arduino_state.get()
        print("writing to arduino", state)


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


# Initializing arduino connection
if serial_addr != None:
    print("Initializing arduino connection")
    for port in list(serial_ports()):
        if serial_addr in port:
            arduino_serial = serial.Serial(port)
            print("Connecting to serial port: " + ser.port)
            # ser.timeout = 0.5
            # ser.write('c')
            # msg = ser.read()
            # if msg == 'y':
            #     continue
    if arduino_serial == None:
        raise RuntimeError("Could not find port with substring: " + serial_addr)
else:
    print("Skipping arduino connection")
    arduino_serial = None


def start_daemon_thread(fn):
    thread = threading.Thread(target=fn)
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    try:
        parse_command_line()
        app.listen(options.port)
        start_daemon_thread(process_data)
        start_daemon_thread(write_to_arduino)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print "GOODBYE"
        sys.exit()
