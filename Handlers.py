import socketserver
import socket
import threading
import sys
import ssl
import logging
import Util
import re
import os
import time
import json
import shutil
import traceback
import OpenSSL
from http.server import BaseHTTPRequestHandler
from dnslib import *


class BaseHandler(BaseHTTPRequestHandler):
    """
    This is the base handler for requests, does a basic job of
    taking in requests and processing them. 
    """
    server_version = ''
    sys_version = ''

    def do_GET(self):
        self.serve_page()

    #host_head is used for http virtual hosting. If a blacklisted request is redirected to 127.0.0.1 then it is
    #resolved here and displayed while staying on port 80. Example cnn.com or foo.com
    def serve_page(self):
        location = ''
        logging.debug('Serving GET request')
        host = self.headers.get('Host')
        logging.debug('Current host: %s' % (host))
        logging.debug('Headers: %s' % (self.headers))
        tool = Util.Util()
        #filter out IP address that cannot be parsed as localhost file paths
        if not tool.valid_addr(host):
            if 'http://' in host:
                host = host.split('http://')[1]
            sub_string = re.search('\Awww', host)
            if sub_string is not None:
                if 'www'  not in sub_string.group(0):
                    host = 'www.%s' % (host)
            hostPath = re.sub('\.', '/', host)
            if os.path.isdir(hostPath):
                for index in 'index.html', 'index.htm':
                    index = os.path.join(hostPath, index)
                    if os.path.exists(index):
                        location = index
                        break
            try:
                location = re.sub('/index', '/./index', location)
                logging.debug('Index location: %s' % (location))
                with open(location, 'rb') as f:
                     self.send_response(200)
                     self.send_header('Content-type', 'text/html')
                     fs = os.fstat(f.fileno())
                     self.send_header('Content-Length', str(fs.st_size))
                     self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
                     self.end_headers()
                     shutil.copyfileobj(f, self.wfile)

            except IOError:
                logging.error('404 File not found')
                self.send_error(404, 'File not found')
        else:
            logging.error('404 Address %s not found' % (host))
            self.send_error(404, 'The address %s was not found' % (host))


class NginxServerHandler(BaseHandler):
    server_version = 'nginx'

class ApacheServerHandler(BaseHandler):
    server_version = 'Apache'

class GwsServerHandler(BaseHandler):
    server_version = 'gws'

class IISServerHandler(BaseHandler):
    server_version = 'IIS'

class HTTPShandler(object):
    def __init__(self, str_request, client_connection, host_name, server_type='Test cat'):
        self.request = str_request
        self.connection = client_connection
        self.host = host_name
        self.server = server_type
#------------------------------------------------Move to JSON file
    def __generateHeaders(self, code):
        header = ''
        if code == 200:
            header = 'HTTP/1.1 %d OK\n' % (code)
        elif code == 404:
            header = 'HTTP/1.1 %d Not Found\n' % (code)
        current_date = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
        header += 'Date: %s\n' % (current_date)
        header += 'Server: %s\n' % (self.server)
        header += 'Connection: close\n\n'
        return header
#-----------------------------------------------------------------
    def handler(self):
        response_content = ''
        request_method = self.request.split(' ')[0]
        if (request_method == 'GET') or (request_method == 'HEAD'):
            file_requested = self.request.split(' ')
            file_requested = file_requested[1]
            logging.debug('Request type: %s' % request_method)
            if file_requested == '/':
                subString = re.search('\Awww', self.host)
                if subString is not None:
                    if 'www' not in subString.group(0):
                        self.host = 'www.%s' % (self.host)
                hostPath = re.sub('\.', '/', self.host)
                if os.path.isdir(hostPath):
                    for index in 'index.html', 'index.htm':
                        index = os.path.join(hostPath, index)
                        if os.path.exists(index):
                            location = index
                            break
                try:
                    logging.debug("File location: %s" % location)
                    location = re.sub('/index', '/./index', location)
                    with open(location, 'rb') as file_handler:
                        if (request_method == 'GET'):
                            logging.debug('Fetching index to serve')
                            response_content = file_handler.read()
                    logging.debug('Sending response 200')
                    response_headers = self.__generateHeaders(200)
                except Exception as e:
                    logging.error('File not found')
                    response_headers = self.__generateHeaders(404)

                server_response = response_headers.encode()
                if request_method == 'GET':
                    server_response += response_content
                self.connection.sendall(server_response)

class DNSHandler():
    """
    Receives the raw DNS query data and extracts the name of the address. Checks the address agaisnt specified
    lists. If the address is not found then it is forwarded to an external DNS to resolve. Forwarded
    requests send the raw query data and receive raw data.
    """
    def __init__(self):
        self.setup_data = Setup()
        
    def dns_response(self, data):
        request = DNSRecord.parse(data)
        logging.debug('Searching: \n %s' % (str(request)))
        reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)
        query_name = request.q.qname                     #is preserved so that we can reply with proper formatting later
        str_query = repr(query_name)                     #remove class formatting
        str_query = str_query[12:-2]                     #DNSLabel type, strip class and take out string
        logging.debug("Query: %s" % str_query)
        #Dictionary is loaded as such because of ease of access for the domain names
        black_dictionary = dict(self.setup_data.setLists())
        #Keep the domain name and an IP address in the blacklist. This way you can change line 282 and instead of redirecting
        #to address 127.0.0.1 for all blacklist addresses you can personally choose where to send each of those. Just copy
        #rdata=A(black_dictionary[str_query]))) instead of the current rdata=A('217.0.0.1')))
        address = urlparse.urlparse(str_query)
        if black_dictionary.get(str_query):
            reply.add_answer(RR(rname=query_name, rtype=1, rclass=1, ttl=300, rdata=A('127.0.0.1')))
        else:
            try:
                real_dns = socket.socket( socket.AF_INET, socket.SOCK_DGRAM)
                real_dns.sendto(data,('8.8.8.8', 53))
                answer_data, fromaddr = real_dns.recvfrom(1024)
                real_dns.close()
                readable_answer = DNSRecord.parse(answer_data)
                logging.debug('DNS Reply: \n %s' % (str(readable_answer)))
                return answer_data
            except socket.gaierror:
                logging.error('Not a valid address %s' % (str_query))

        logging.debug('DNS Reply: \n %s' % (str(reply)))
        return reply.pack()   # replies with an empty pack if address is not found


    def printThreads(self, currentThread, tnum):
        logging.debug('Current thread: %s \n Current threads alive: %d' % (str(currentThread), tnum))


    class BaseRequestHandler(socketserver.BaseRequestHandler):

        def get_data(self):
            raise NotImplementedError

        def send_data(self, data):
            raise NotImplementedError

        def handle(self):
            now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
            logging.debug('\n\n%s request %s (%s %s):' % (self.__class__.__name__[:3], now, self.client_address[0], self.client_address[1]))

            try:
                data = self.get_data()
                logging.debug('Length: %d %s' % (len(data), data.encode('hex')))
                self.send_data(Controller().dns_response(data))
            except Exception:
                traceback.print_exc(file=sys.stderr)
            except KeyboardInterrupt:
                sys.exit(1)

    class UDPRequestHandler(BaseRequestHandler, ):

        def get_data(self):
            return self.request[0]

        def send_data(self, data):
            return self.request[1].sendto(data, self.client_address)

class HandlerFactory(object):

    def http_factory(self, name):
        if name == 'nginx': return View.NginxServerHandler
        elif name == 'Apache': return View.ApacheServerHandler
        elif name == 'gws': return View.GwsServerHandler
        elif name == 'IIS': return View.IISServerHandler
        else:
            logging.debug('%s type of handler not found.' % (name))

    def https_factory(self):
        return View.HTTPShandler
