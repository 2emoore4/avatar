import os
import serial
import tornado.ioloop
import tornado.web
import tornado.websocket

from serial.tools import list_ports
from tornado.options import define, options, parse_command_line

# add command line option for port number
define("port", default=8080, help="run on the given port", type=int)

# response handler for http requests
class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.write("response")
        self.finish()

# response handler for web sockets
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        print("received a message: %s" % (message))

app = tornado.web.Application([
    (r'/', WebSocketHandler),
])

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
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
