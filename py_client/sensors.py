import datetime
import json
import numpy
import os
import sys
import serial

from serial.tools import list_ports
from websocket import create_connection

connection_active = False

def on_open(ws):
    connection_active = True

def on_close(ws):
    connection_active = False

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

# receives packet from arduino
def next_packet():
    while True and arduino_serial != None:
        header = arduino_serial.read()
        if header == 'a':
            try:
                message_size = next_value()
                messages = []

                for i in xrange(message_size):
                    messages.append(next_value())

                # messages is now an array of readings
                return messages
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

pots = []
lights = []
temps = []
dists = []

def process_packet(packet):
    print "packet"
    save_measurement(lights, packet[0])
    state_change(lights)

    save_measurement(temps, packet[1])
    state_change(temps)

    save_measurement(dists, packet[2])
    state_change(dists)

    save_measurement(pots, packet[3])
    state_change(pots)

    websocket.send(json.dumps({'type': 'light-intensity', 'value': packet[0]}))
    websocket.send(json.dumps({'type': 'temperature', 'value': packet[1]}))
    websocket.send(json.dumps({'type': 'distance', 'value': packet[2]}))
    websocket.send(json.dumps({'type': 'potentiometer', 'value': packet[3]}))

# saves measurement to list, dequeues oldest measurement
def save_measurement(history, value):
    history.append(value)
    if len(history) > 1000:
        history.pop(0)

# returns true if most recent measurements show a state change
def state_change(history):
    size = len(history)
    if size > 800:
        recents = []
        for i in xrange(size - 100, size):
            recents.append(history[i])

        recent_mean = numpy.mean(recents)
        full_mean = numpy.mean(history)

        diff = abs(recent_mean - full_mean)
        percent_change = diff / full_mean

        # state change
        if percent_change > 0.25:
            print "state change " + str(full_mean) + " to " + str(recent_mean)
            del history[:]
            return True
    else:
        return False

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
                arduino_serial.baudrate = 115200
        else:
            print("Skipping arduino connection.")
            arduino_serial = None

        # connect to websocket
        websocket = create_connection("ws://milessteele.com:8080")
        print "done"

        while True:
            packet = next_packet()
            if packet != None: process_packet(packet)

    except KeyboardInterrupt:
        print "GOODBYE"
        sys.exit()
