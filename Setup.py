import argparse
import sys
import traceback
import socketserver
import datetime
import configparser
import logging
from dnslib import *


def launchOptions(mainObj):
    parser = argparse.ArgumentParser(description="This program forwards DNS requests not found in the blacklist")
    parser.add_argument("-dp", "--dns_port", help="select the port the DNS server runs on. Default port 53", type=int)
    parser.add_argument("-bf", "--blackFile", help="specify the file to be used as the blacklist", type=str)
    parser.add_argument("-hp", "--http_port", help="select the port the HTTP server runs on. Default port 80 or 8080", type=int)
    parser.add_argument("-s", "--save_option", help="saves the launch options selected in the config file, select yes or no", default=False, action="store_true")
    parser.add_argument("-hsp", "--https_port", help="select the port the HTTPS server runs on. Default port 443", type=int)
    parser.add_argument("-cf", "--readfile", help="select the config file to load and save from", type=str)
    arg = parser.parse_args()
    mainObj.set_DNSport(arg.dns_port)
    mainObj.set_bFile(arg.blackFile)
    mainObj.set_HTTPport(arg.http_port) #needed if value is set but did not want to save
    mainObj.set_HTTPSport(arg.https_port)
    mainObj.set_save(arg.save_option)
    if arg.save_option == True: #this function prevents the program from saving garbage values if only -s is selected without params
        null_choices = 0         #if it is run without paramaters to save, don"t save
        logging.debug("Saving enabled")
        arg_size = len(vars(arg)) - 1 #There is a -1 because -s is a save flag and does not take parameters
        for value in vars(arg):
            if getattr(arg, value) == None:
                null_choices += 1
        if arg.readfile is not None and null_choices < arg_size:
            logging.debug("Saving to new config file")
            mainObj.writeToConfig(arg.readfile, str(arg.dns_port), \
                                  arg.blackFile, str(arg.http_port), str(arg.https_port))
        elif arg.readfile is None and null_choices < arg_size:
            loggin.debug("Saving settings")
            mainObj.writeToConfig("config.ini", str(arg.dns_port), \
                                  arg.blackFile, str(arg.http_port), str(arg.https_port))

class Setup(object):
    def __init__(self, dns_port=None, hport=None, hsport=None, blackfile=None, saveOP=False):
        self.dns_port = port
        self.http_port = hport
        self.https_port = hsport
        self.blacklist = blackfile
        self.save = saveOP
        self.config_items = ""


    def setPorts(self):
        if self.save == False and (self.http_port is not None or self.https_port is not None):
             return
        else:
            self.config_items = self.loadConfig()
            self.dns_port = self.config_items["DNSport"]
            self.http_port = self.config_items["HTTPport"]
            self.https_port = self.config_items["HTTPSport"]

    def loadFile(self, currentFile):
        try:
            with open(currentFile) as domains:
                domainList = [tuple(map(str.strip, line.split(","))) for line in domains]
            return domainList
        except IOError:
            logging.critical("File not found, please specify a valid file")
            sys.exit(1)

    def addToCache(self, DomainItem, currentFile):
        try:
            if DomainItem is not None:
                with open(currentFile, "r+") as domains:
                    domainList = [tuple(map(str.strip, line.split(","))) for line in domains]
                    dictList = dict(domainList)
                with open(currentFile, "a+") as fileData:
                    if DomainItem.name in dictList:
                        logging.debug("%s already exists in database" % (Domain.Item.name))
                    elif DomainItem.name not in dictList:
                        fileData.write("%s, %d \n" % (DomainItem.name, DomainItem.IP))
                        logging.debug("%s already exists in database" % (DomainItem.name))
        except IOError:
            logging.critical("File not found, please specify a valid file")
            sys.exit(1)

    def addToBlacklist(self, siteName, IP,  currentFile):
        try:
            if IP is not None and siteName is not None:
                with open(currentFile, "r+") as domains:
                    domainList = [tuple(map(str.strip, line.split(","))) for line in domains]
                    dictList = dict(domainList)
                with open(currentFile, "a+") as fileData:
                    if siteName in dictList:
                        logging.debug("%s already exists in the database" % sitename)
                    elif sitename not in dictList:
                        fileData.write("%s, %d \n" % (siteName, IP))
        except IOError:
            logging.critical("File %s not found, specify a valif file" % sitename)
            sys.exit(1)

    def loadConfig(self, currentFile="config.ini"):
        try:
            readfile = ConfigParser.ConfigParser()
            readfile.read(currentFile)
            serverConfig = {}
            if not readfile.has_section("Run_Time"):
                logging.error("File is missing the Run_Time section, maybe wrong file name?")
            elif readfile.has_section("Run_Time"):
                if readfile.has_option("Run_Time", "DNSport"):
                    serverConfig["DNSport"] = readfile.get("Run_Time", "DNSport")
                if readfile.has_option("Run_Time", "Blacklist"):
                    serverConfig["Blacklist"] = readfile.get("Run_Time", "Blacklist")
                if readfile.has_option("Run_Time", "HTTPport"):
                    serverConfig["HTTPport"] = readfile.get("Run_Time", "HTTPport")
                if readfile.has_option("Run_Time", "HTTPSport"):
                    serverConfig["HTTPSport"] = readfile.get("Run_Time", "HTTPSport")
            return serverConfig
        except IOError:
            logging.critical("File %s not found, please specify a valid file or verify the file name" % currentfile)
            sys.exit(1)

    def writeToConfig(self, currentFile=None, DNSport=None, blackFile=None, http_port=None, https_port=None):
        try:
           config_file = ConfigParser.ConfigParser()
           config_file.read(currentFile)
           if config_file.has_section("Run_Time"):
               logging.debug("Adding items")
               if DNSport is not None:
                   config_file.set("Run_Time", "DNSport", DNSport)
               if blackFile is not None:
                   config_file.set("Run_Time", "Blacklist", blackFile)
               if http_port is not None:
                   config_file.set("Run_Time", "HTTPport", http_port)
               if https_port is not None:
                   config_file.set("Run_Time", "HTTPSport", https_port)
               #Virtual server configs
           elif not config_file.has_section("Run_Time"):
               #create config section if it does not exist
               logging.debug("Adding section and items")
               config_file.add_section("Run_Time")
               if DNSport is not None:
                   config_file.set("Run_Time", "DNSport", DNSport)
               else:
                   config_file.set("Run_Time", "DNSport", "8000")
               if blackFile is not None:
                   config_file.set("Run_Time", "Blacklist", blackFile)
               else:
                   config_file.set("Run_Time", "Blacklist", "blackList.txt")
               if http_port is not None:
                   config_file.set("Run_Time", "HTTPport", http_port)
               else:
                   config_file.set("Run_Time", "HTTPport", "80")
               if https_port is not None:
                   config_file.set("Run_Time", "HTTPSport", https_port)
               else:
                   config_file.set("Run_Time", "HTTPSport", "443")
           logging.debug("Writing to file: %s" % currentFile)
           with open(currentFile, "w") as configfile:
               config_file.write(configfile)
        except IOError:
            logging.critical("Config file %s not found, please specify a valid file" % configfile)
            sys.exit(1)

    def startServers(self):
        #Port for either services will be set at launch on terminal or config file
        # run the DNS services

        #Initialize and run DNS, HTTP and HTTPS
        self.setPorts()
        serverList = Model.Server()

        http_server = serverList.factory("HTTP", self.http_port)
        http_server.daemon = True
        http_server.start()


        #initialize and run HTTPS services
        https_server = serverList.factory("HTTPS", self.https_port)
        https_server.daemon = True
        https_server.start()

        #Move these items to the config file

    def setLists(self):
        self.config_items = self.loadConfig()
        if self.save is None:
            logging.debug('Skipping list save for Blackfile')
        else:
            logging.debug('Saving list for Blackfile')
            self.blacklist = self.config_items['Blacklist']
            return self.blacklist
    #---------------------------------------------Move to separate file to generate JSON header files
    class GenerateHeaders(object):
        def __init__(self, code, server_type, fsize):
            self.http_code = code
            self.server = server_type
            self.file_length = fsize

        def makeHeaders(self):
            header = ''
            if self.http_code == 200:
                header = 'HTTP/1.1 %d OK\r\n' % (self.http_code)
            elif self.http_code == 404:
                header = ' HTTP/1.1 %d Not found\r\n' % (self.http_code)
            current_date = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
            header += 'Date: %s\r\n' % (current_date)
            header += 'Server: %s\r\n' % (self.server)
            header += 'Content-Type: html\r\n'
            header += 'Content-Length: %s\r\n' % (self.file_length)
            header += 'Connection: close \r\n\n'
            data_string = json.dumps(header)
            return data_string
