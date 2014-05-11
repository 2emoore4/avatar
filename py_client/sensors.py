import json
import os
import sys
import serial

from serial.tools import list_ports
from websocket import create_connection

# a list of known substrings of serial addresses to try to connect to.
# if None, then skip connecting
serial_addr_subs = ["ACM", "usbmodem", "usbserial"]
# serial connection to arduino, could be None if connection fails
arduino_serial = None

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
    return None # if no matches

# connect to websocket
#websocket = create_connection("ws://18.238.6.29:8080")
#websocket.send(json.dumps({'type': 'light', 'value': 0.5}))

# loops to receive packets from arduino
def process_packets():
    while True:
        header = arduino_serial.read()
        if header == 'a':
            message_size = next_value()
            messages = []

            try:
                for i in xrange(message_size):
                    messages.append(next_value())

                # messages is now an array of readings
                print messages
            except ValueError:
                print "skipping weird packet"

# returns next value from serial port (values delimited by spaces)
def next_value():
    value_str = ""
    next_char = arduino_serial.read()

    while next_char != " ":
        value_str += next_char
        next_char = arduino_serial.read()

    return int(value_str)

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

        process_packets()

    except KeyboardInterrupt:
        print "GOODBYE"
        sys.exit()
