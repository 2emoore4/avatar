import os
import serial
import zmq
from serial.tools import list_ports

# Initializing ZeroMQ server
print("Initializing ZeroMQ server")
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5000")

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
print("Initializing arduino connection")
for port in list(serial_ports()):
    try:
        ser = serial.Serial(port)
        print("Attempting to connect to port: " + ser.port)
        ser.timeout = 0.5
        ser.write('c')
        msg = ser.read()
        if msg == 'y':
            continue
    except OSError:
        pass
print("Done. Ready to receive messages.")

def main():
    # Main loop
    while True:
        # Check for incoming message.
        msg = socket.recv()
        print("Received message: " + msg)

        # Send back message to confirm receipt.
        socket.send(msg)

if __name__ == "__main__":
    main()
