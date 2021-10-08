import socketserver 
import socket
import threading
import multiprocessing #TODO
import sys
import Handlers     
import ssl
import logging
import OpenSSL
from dnslib import *

class VirtualServer(threading.Thread):

    def __init__(self, port=None):
        threading.Thread.__init__(self)
        self.port = int(port)

    def run(self):
        raise NotImplementedError

class DNSServer(VirtualServer):

    def run(self):
        try:
            loggging.debug("DNS UDP server running on port %d" % self.port)
            DNS = SocketServer.ThreadingUDPServer(("", self.port), Handlers.DNSHandler.UDPRequestHandler)
            DNS.serve_forever()
        except(KeyboardInterrupt):
            logging.warn("Keyboard interrupt detected")
        finally:
            logging.critical("DNS server shutting down")
            DNS.shutdown()
            sys.exit(1)

class HTTPServer(VirtualServer):

    def run(self):
        try:
            logging.debug("Serving HTTP at port %d" % self.port)
            http_server = SocketServer.TCPServer(("", self.port), Handlers.BaseHandler)
            http_server.serve_forever()
        except (KeyboardInterrupt):
            logging.warn("Keyboard interrupt detected")
        finally:
            logging.critical("HTTP server shutting down")
            http_server.shutdown()
            sys.exit(1)

class HTTPSServer(HTTPServer):

    def __init__(self, port=443, cert="./server.crt", key="server.key"):
        super().__init__(port)
        self.cert = cert
        self.key = key

    def run(self):
        try:
            logging.debug("Serving HTTPS at port %s" % self.port)
            https = HTTPServer(("", self.port), Handlers.HTTPShandler)
            https.socket = ssl.wrap_socket(https.socket, self.cert, server_side=True, keyfile=self.key)
            https.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            logging.warn("Keyboard interrupt detected")
        finally:
            logging.critical("HTTPS server shutting down")
            https.shutdown()
            sys.exit(1)

class Server(object):

    def factory(self, name, port=None):
        if name == "DNS": return DNSServer(port)
        elif name == "HTTP": return HTTPServer(port)
        elif name == "HTTPS": return HTTPSServer(port, cert, key)
        else:
            logging.warn("No such type %s" % name)

