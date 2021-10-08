import argparse
from Controller import *
from Model import *

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
    print 'Starting HTTP/HTTPS web servers...'
    mainItem = IOitems()
    launchOptions(mainItem)
    Model.setLists(mainItem)
    mainItem.startServers()
    try:
        while(keepRunning()):
           time.sleep(1)
           sys.stderr.flush()
           sys.stdout.flush()
    except (KeyboardInterrupt, SystemExit):
        print('Terminated via SIGNINT')
#        logging.debug('Terminated via SIGINT')
#        raise
    finally:
        sys.exit(1)
