import argparse
import logging
from Servers import *

def keepRunning():
    running = True
    try:
        running = True
    except (KeyboardInterrupt, SystemExit):
        running = False
        raise

    return running

#TODO: build standalone for DNS
if __name__ == '__main__':
    logging.basicConfig(filename='debugging.log', level=logging.DEBUG)
    logging.debug('Starting HTTP/HTTPS web servers...')
    #mainItem = IOitems()
    #launchOptions(mainItem)
    #Model.setLists(mainItem)
    #mainItem.startServers()
    test = Server()
    my_server = test.factory("HTTP", 8080)
    my_server.run() 
    try:
        while(keepRunning()):
           time.sleep(1)
           sys.stderr.flush()
           sys.stdout.flush()
    except (KeyboardInterrupt, SystemExit):
        logging.critical('Terminated via SIGNINT')
    finally:
        sys.exit(1)
