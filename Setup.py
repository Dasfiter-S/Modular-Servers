import argparse
from Controller import *
from Model import *
import sys
import traceback
import SocketServer
import datetime
import Model
import urlparse
import ConfigParser
import logging
from dnslib import *


def launchOptions(mainObj):
    parser = argparse.ArgumentParser(description='This program forwards DNS requests not found in the whitelist or blacklist')
    parser.add_argument('-dp', '--dns_port', help='select the port the DNS server runs on. Default port 53', type=int)
    parser.add_argument('-wf', '--whiteFile', help='specify the file to be used as the whitelist', type=str)
    parser.add_argument('-bf', '--blackFile', help='specify the file to be used as the blacklist', type=str)
    parser.add_argument('-hp', '--http_port', help='select the port the HTTP server runs on. Default port 80 or 8080', type=int)
    parser.add_argument('-s', '--save_option', help='saves the launch options selected in the config file, select yes or no', default=False, action='store_true')
    parser.add_argument('-hsp', '--https_port', help='select the port the HTTPS server runs on. Default port 443', type=int)
    parser.add_argument('-cf', '--readfile', help='select the config file to load and save from', type=str)
    arg = parser.parse_args()
    mainObj.set_DNSport(arg.dns_port)
    mainObj.set_wFile(arg.whiteFile)
    mainObj.set_bFile(arg.blackFile)
    mainObj.set_HTTPport(arg.http_port) #needed if value is set but did not want to save
    mainObj.set_HTTPSport(arg.https_port)
    mainObj.set_save(arg.save_option)
    if arg.save_option == True: #this function prevents the program from saving garbage values if only -s is selected without params
        null_choices = 0         #if it is run without paramaters to save, don't save
        print 'Save is true'
        arg_size = len(vars(arg)) - 1 #There is a -1 because -s is a save flag and does not take parameters
        for value in vars(arg):
            if getattr(arg, value) == None:
                null_choices += 1
        if arg.readfile is not None and null_choices < arg_size:
            print 'Saving to new config file'
            mainObj.writeToConfig(arg.readfile, str(arg.dns_port), \
                    arg.whiteFile, arg.blackFile, str(arg.http_port), str(arg.https_port))
        elif arg.readfile is None and null_choices < arg_size:
            print 'Saving settings'
            mainObj.writeToConfig('config.ini', str(arg.dns_port), \
                    arg.whiteFile, arg.blackFile, str(arg.http_port), str(arg.https_port))

class IOitems(object):
    def __init__(self, port=None, hport=None, hsport=None, whiteFile=None, blackFile=None, saveOP=False):
        self.port = port
        self.http_port = hport
        self.https_port = hsport
        self.whitelist = whiteFile
        self.blacklist = blackFile
        self.save = saveOP


    def setPorts(self):
        if self.saveOp == False and (self.http_port is not None or self.https_port is not None):
             return
        else:
            temp = IOitems()
            items = temp.loadConfig()
            self.port = items['DNSport']
            self.http_port = items['HTTPport']
            self.https_port = items['HTTPSport']

    def loadFile(self, currentFile):
        try:
            with open(currentFile) as domains:
                domainList = [tuple(map(str.strip, line.split(','))) for line in domains]
            return domainList
        except IOError:
            print 'File not found, specify a valid file'
            logging.error('File not found, please specify a valid file')
            sys.exit(1)

    def addToCache(self, DomainItem, currentFile):
        try:
            if DomainItem is not None:
                with open(currentFile, 'r+') as domains:
                    domainList = [tuple(map(str.strip, line.split(','))) for line in domains]
                    dictList = dict(domainList)
                with open(currentFile, 'a+') as fileData:
                    if DomainItem.name in dictList:
                        print '%s already exists in database' % (DomainItem.name)
                        logging.debug('%s already exists in database' % (Domain.Item.name))
                    elif DomainItem.name not in dictList:
                        fileData.write('%s, %d \n' % (DomainItem.name, DomainItem.IP))
                        print '%s with IP %s has been added to the database' % (DomainItem.name, DomainItem.IP)
                        logging.debug('%s already exists in database' % (DomainItem.name))
        except IOError:
            print 'File not found, specify a valid file'
            logging.error('File not found, please specify a valid file')
            sys.exit(1)

    def addToBlacklist(self, siteName, IP,  currentFile):
        try:
            if IP is not None and siteName is not None:
                with open(currentFile, 'r+') as domains:
                    domainList = [tuple(map(str.strip, line.split(','))) for line in domains]
                    dictList = dict(domainList)
                with open(currentFile, 'a+') as fileData:
                    if siteName in dictList:
                        print '%s already exists in database' % (sitename)
                        logging.debug('%s already exists in the database' % (sitename))
                    elif sitename not in dictList:
                        fileData.write('%s, %d \n' % (siteName, IP))
        except IOError:
            print 'File not found, specify a valid file'
            logging.debug('%s already exists in database' % (sitename))
            sys.exit(1)

    def loadConfig(self, currentFile='config.ini'):
        try:
            readfile = ConfigParser.ConfigParser()
            readfile.read(currentFile)
            serverConfig = {}
            if not readfile.has_section('Run_Time'):
                print 'File missing:\n --Run_Time section--'
                logging.debug('File missing Run_Time section')
            elif readfile.has_section('Run_Time'):
                if readfile.has_option('Run_Time', 'DNSport'):
                    serverConfig['DNSport'] = readfile.get('Run_Time', 'DNSport')
                if readfile.has_option('Run_Time', 'Whitelist'):
                    serverConfig['Whitelist'] = readfile.get('Run_Time', 'Whitelist')
                if readfile.has_option('Run_Time', 'Blacklist'):
                    serverConfig['Blacklist'] = readfile.get('Run_Time', 'Blacklist')
                if readfile.has_option('Run_Time', 'HTTPport'):
                    serverConfig['HTTPport'] = readfile.get('Run_Time', 'HTTPport')
                if readfile.has_option('Run_Time', 'HTTPSport'):
                    serverConfig['HTTPSport'] = readfile.get('Run_Time', 'HTTPSport')
            return serverConfig
        except IOError:
            print 'File not found, please specify a valid file or verify the file name'
            logging.debug('File not found, please specify a valid file or verify the file name')
            sys.exit(1)

    def writeToConfig(self, currentFile=None, DNSport=None, whiteFile=None, blackFile=None, http_port=None, https_port=None):
        try:
           config_file = ConfigParser.ConfigParser()
           config_file.read(currentFile)
           if config_file.has_section('Run_Time'):
               print 'Adding items'
               logging.debug('Adding items')
               if DNSport is not None:
                   config_file.set('Run_Time', 'DNSport', DNSport)
               if whiteFile is not None:
                   config_file.set('Run_Time', 'Whitelist', whiteFile)
               if blackFile is not None:
                   config_file.set('Run_Time', 'Blacklist', blackFile)
               if http_port is not None:
                   config_file.set('Run_Time', 'HTTPport', http_port)
               if https_port is not None:
                   config_file.set('Run_Time', 'HTTPSport', https_port)
               #Virtual server configs
           elif not config_file.has_section('Run_Time'):
               #create config section
               print 'Adding section and items with specified values or defaults'
               logging.debug('Adding section and items')
               config_file.add_section('Run_Time')
               if DNSport is not None:
                   config_file.set('Run_Time', 'DNSport', DNSport)
               else:
                   config_file.set('Run_Time', 'DNSport', '8000')
               if whiteFile is not None:
                   config_file.set('Run_Time', 'Whitelist', whiteFile)
               else:
                   config_file.set('Run_Time', 'Whitelist', 'DNSCache.txt')
               if blackFile is not None:
                   config_file.set('Run_Time', 'Blacklist', blackFile)
               else:
                   config_file.set('Run_Time', 'Blacklist', 'blackList.txt')
               if http_port is not None:
                   config_file.set('Run_Time', 'HTTPport', http_port)
               else:
                   config_file.set('Run_Time', 'HTTPport', '80')
               if https_port is not None:
                   config_file.set('Run_Time', 'HTTPSport', https_port)
               else:
                   config_file.set('Run_Time', 'HTTPSport', '443')
           print 'Writing to file: %s' % (currentFile)
           logging.debug('Writing to file: %s' % (currentFile))
           with open(currentFile, 'w') as configfile:
               config_file.write(configfile)
        except IOError:
            print 'File not found, specify a valid file'
            logging.debug('File not found, please specify a valid file')
            sys.exit(1)

    def set_DNSport(self, port):
        if port is not None:
            self.port = port

    def set_HTTPport(self, port):
        if port is not None:
            self.http_port = port

    def set_HTTPSport(self, port):
        self.https_port = port

    def set_save(self, save=None):
        if save is not None:
            self.saveOp = save

    def set_wFile(self, inFile):
        if inFile is not None:
             self.whitelist = inFile
             print 'WFin: %s' % inFile

    def set_bFile(self, inFile):
        if inFile is not None:
             self.blacklist = inFile
             print 'BFin: %s' % inFile

    def startServers(self):
        #Port for either services will be set at launch on terminal or config file
        # run the DNS services

        #Initialize and run DNS, HTTP and HTTPS
        self.setPorts()
        serverList = Model.Server()

        http_server = serverList.factory('HTTP', self.http_port)
        http_server.daemon = True
        http_server.start()


        #initialize and run HTTPS services
        https_server = serverList.factory('HTTPS', self.https_port)
        https_server.daemon = True
        https_server.start()

        #Move these items to the config file
