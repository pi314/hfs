#!/usr/bin/env python
from __future__ import print_function
import sys

VERSION = sys.version_info[0]

if VERSION == 3:
    import http.server as HttpServerModule
    import socketserver as SocketServerModule
else:
    import SimpleHTTPServer as HttpServerModule
    import SocketServer as SocketServerModule

import show_my_ip

PORT = 8000 if len(sys.argv) == 1 else int(sys.argv[1])

show_my_ip.output()

Handler = HttpServerModule.SimpleHTTPRequestHandler
class myHandler (Handler):

    def do_GET (self):
        super(myHandler, self).do_GET()
        print("Request ends")

    def do_HEAD (self):
        super(myHandler, self).do_HEAD()
        print("Request ends")

# httpd = SocketServerModule.TCPServer(("", PORT), Handler)
httpd = SocketServerModule.TCPServer(("", PORT), myHandler)

try:
    print('Serving at port: %d'%(PORT) )
    httpd.serve_forever()
except KeyboardInterrupt:
    print('KeyboardInterrupt detected, exit.')
    httpd.shutdown()
    exit()
