import SocketServer
import socket
import multiprocessing #TODO
import sys
#import Controller     #TODO
#import View           #TODO
#import BaseHTTPServer #TODO
import ssl
import logging
#import Util
import re
import OpenSSL
from dnslib import *

class VirtualServer:

    def __init__(self, port=None):
        self.port = int(port)

    def run(self):
        raise NotImplementedError

class DNSServer(VirtualServer):

    def run(self):
        try:
            loggging.debug("DNS UDP server running on port %d " % self.port)
            #DNS = SocketServer.ThreadingUDPServer(("", self.port), Controller.Controller.UDPRequestHandler)
            #DNS.serve_forever()
        except(KeyboardInterrupt):
            logging.warn("Process stopped with key press")
        finally:
            logging.warn("System shutting down")
            #DNS.shutdown()
            sys.exit(1)

class HTTPServer(VirtualServer):

    def run(self):
        try:
            logging.debug("Serving HTTP at port %d" % self.port)
            #http_server = SocketServer.TCPServer(("", self.port)), View.BaseHandler)
            #http_server.serve_forever()
        except (KeyboardInterrupt):
            logging.warn("Process stopped with key press")
        finally:
            logging.warn("System shutting down")
            #http_server.shutdown()
            sys.exit(1)

class Server(object):

    def factory(self, name, port=None):
        if name == 'HTTP': return HTTPServer(port)
        elif name == 'HTTPS': return HTTPSServer(port)
        elif name == 'DNS': return DNSServer(port)
        elif name == 'Easy': return EasyHTTPSServer(port)
        else:
            logging.debug('No such type %s' % (name))
            print 'No such type %s' % (name)

class EasyHTTPSServer(BaseServer):
    def run(self):
        try:
            print 'Serving HTTPS at port %s' % (self.port)
            logging.debug('Serving HTTPS at port %s' % (self.port))
            https = BaseHTTPServer.HTTPServer(('', int(self.port)), View.HTTPShandler)
            https.socket = ssl.wrap_socket(https.socket, certfile='./server.crt', server_side=True, keyfile='server.key')
            https.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            https.shutdown()
            https.server_close()
