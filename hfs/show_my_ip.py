import os
import socket
import sys
import importlib

def import_netifaces_module():
    v = os.environ.get('VIRTUAL_ENV', None)
    if v:
        sys.path = [v + '/lib/python3.5/site-packages'] + sys.path

    if importlib.util.find_spec('netifaces'):
        return importlib.import_module('netifaces')


def show():
    netifaces = import_netifaces_module()

    if not netifaces:
        workaround()
        return

    print('Available network interfaces:')
    for iface in netifaces.interfaces():
        info = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in info:
            print()
            if netifaces.AF_LINK in info:
                print('  {} ({})'.format(iface, info[netifaces.AF_LINK][0]['addr']))
            else:
                print('  {}'.format(iface))
            for addr in info[netifaces.AF_INET]:
                print('    IP/Mask: {} / {}'.format(addr['addr'], addr['netmask']))

    print()

def workaround():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()

    print('netifaces module not found, using Python stdlib workaround:')
    print()
    print('  {}'.format(IP))
    print('  {}'.format(socket.gethostbyname(socket.gethostname())))
    print('  {}'.format(socket.gethostbyname(socket.getfqdn())))
    print()
