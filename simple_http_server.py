#!/usr/bin/env python
from __future__ import print_function
import sys

VERSION = sys.version_info[0]

if VERSION == 3:
    import http.server
    import socketserver
else:
    import SimpleHTTPServer
    import SocketServer

from show_my_ip import show_my_ip


PORT = 8000 if len(sys.argv) == 1 else int(sys.argv[1])

show_my_ip.main()

if VERSION == 3:
    server_address = ('', PORT)
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)
else:
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", PORT), Handler)

try:
    print('Serving at port: %d'%(PORT) )
    httpd.serve_forever()
except KeyboardInterrupt:
    print('KeyboardInterrupt detected, exit.')
    exit()
