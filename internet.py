import socket
from time import sleep

def is_connected():
    hostname = "www.google.com"
    try:
        # see if we can resolve the host name -- tells us if there is
        # # a DNS listening
    host = socket.gethostbyname(hostname)
    # connect to the host -- tells us if the host is actually
    # reachable
    s = socket.create_connection((host, 80), 2)
    s.close()
    return True
    except:
        pass
    return False

def wait_until_connection_becames_available():
    while not is_connected:
        sleep(10)
