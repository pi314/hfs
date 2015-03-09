#!/usr/bin/env python
from __future__ import print_function
import sys

VERSION = sys.version_info[0]

if VERSION == 2:
    print('This program only supports Python3, please use Python3 instead.')
    exit()

import http.server
import socketserver
import io
import urllib.parse

import show_my_ip
import time
import os
import urllib
import cgi
import re

PORT = 8000 if len(sys.argv) == 1 else int(sys.argv[1])

show_my_ip.output()

def milli_time ():
    return int(round(time.time()*1000))

color_codes = ['\033[1;3'+i+'m' for i in '01234567']

Handler = http.server.SimpleHTTPRequestHandler

def write (f, s):
    f.write(bytes(s, 'utf8'))

class myHandler (Handler):

    def do_GET (self):
        t = milli_time()
        session_id = hex(t)
        print('Session', color_codes[t%8] + session_id + '\033[m', 'start')
        super(myHandler, self).do_GET()
        print('Session', color_codes[t%8] + session_id + '\033[m', 'end')

    def do_HEAD (self):
        session_id = hex(milli_time())
        print('Session', color_codes[t%8] + session_id + '\033[m', 'start')
        super(myHandler, self).do_HEAD()
        print('Session', color_codes[t%8] + session_id + '\033[m', 'end')

    def do_POST(self):
        print('POST from {}'.format(self.client_address))
        r, info = self.deal_post_data()
        print(r, info)
        new_url = ('{}?success={}&reason={}'.format(urllib.parse.urlparse(self.path).path, r, info))
        print(new_url)
        self.send_response(302)
        self.send_header('Location', new_url)
        self.end_headers()

    def deal_post_data (self):
        content_length = int(self.headers['Content-Length'])
        print('content-length: {}'.format(content_length))
        content_type = self.headers['Content-Type']

        m = re.match(r'^multipart/form-data; *boundary=(.*)$', content_type)
        if not m: return (False, 'Boundary not found')
        boundary = bytes(m.group(1), 'utf8')

        raw_line = self.rfile.readline()
        if boundary not in raw_line: return (False, 'Content not begin with boundary')
        content_length -= len(raw_line)

        raw_line = self.rfile.readline()
        m = re.match(r'^Content-Disposition:.*name="file"; *filename="(.*)"$', str(raw_line, 'utf8').rstrip())
        if not m: return (False, 'File name not found')
        filename = m.group(1)
        if filename == '': return (False, 'Empty file name')
        print('Upload filename: {}'.format(filename))
        content_length -= len(raw_line)

        raw_line = self.rfile.readline()
        # skip more lines until a empty line, and then the file begins
        while len(raw_line.strip()) != 0:
            content_length -= len(raw_line)
            raw_line = self.rfile.readline()
        content_length -= len(raw_line)

        real_root = os.getcwd()
        chrooted_path = urllib.parse.urlparse(self.path).path
        real_upload_file_path = self.get_proper_file_path(real_root + chrooted_path + filename)
        print('Filepath: {}'.format(real_upload_file_path))

        try:
            out = open(real_upload_file_path, 'wb')
        except IOError:
            raw_line = self.rfile.readline()
            content_length -= len(raw_line)
            while content_length > 0:
                raw_line = self.rfile.readline()
                content_length -= len(raw_line)
            return (False, 'Cannot create file')

        # here comes the file
        preline = self.rfile.readline()
        content_length -= len(preline)
        while content_length > 0:
            raw_line = self.rfile.readline()
            content_length -= len(raw_line)
            if boundary in raw_line:
                preline = preline[:-1]
                preline = preline[:-1] if preline.endswith(b'\r') else preline
                out.write(preline)
                out.close()
                return (True, 'File upload success')
            out.write(preline)
            preline = raw_line

        os.remove(real_upload_file_path)
        return (False, 'Unexpected ends of data')

    def get_proper_file_path (self, path):
        if not os.path.exists(path): return path
        dirname =  os.path.dirname(path)
        basename = os.path.basename(path)
        filename, fileext = os.path.splitext(path)
        postfix_number = 1
        ret = os.path.join(dirname, '{}_{}{}'.format(filename, postfix_number, fileext))
        while os.path.exists(ret):
            postfix_number += 1
            ret = os.path.join(dirname, '{}_{}{}'.format(filename, postfix_number, fileext))
        return ret

    def list_directory (self, real_path):
        res = urllib.parse.urlparse( cgi.escape(urllib.parse.unquote(self.path)) )
        displaypath = res.path
        success = None
        reason =  None
        if res.query != '':
            pq = urllib.parse.parse_qs(res.query)
            success = pq['success'][0]
            reason =  pq['reason'][0].rstrip('/')

        title = 'Directory listing for '+ displaypath
        p = io.BytesIO()
        write(p, '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">')
        write(p, '<html>')
        write(p, '<head>')
        write(p, '<title>{}</title>'.format(title))
        write(p, '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
        write(p, '<style>body { font-family: monospace; }</style>')
        write(p, '<style>ul { font-size: 15px; list-style: none; }</style>')
        write(p, '<style>li { margin: 5px; }</style>')
        write(p, '<style>.error { color: red; }</style>')
        write(p, '<style>.succ { color: lime; }</style>')
        write(p, '</head>')
        write(p, '<body>')
        write(p, '<h1>{}</h1>'.format(title))
        write(p, '<hr>')
        write(p, '<ul>')

        try:
            file_list = sorted(os.listdir(real_path), key=lambda a: a.lower())
            file_list = file_list
            write(p, '<li><a href="..">..</a></li>')
            for name in file_list:
                fullpath = os.path.join(real_path, name)
                displayname = name
                linkname = name
                if os.path.isdir(fullpath):
                    displayname = name +'/'
                    linkname = name +'/'
                elif os.path.islink(fullpath):
                    displayname = name +'@'

                write(p, '<li><a href="{}">{}</a></li>'.format( urllib.parse.quote(linkname), cgi.escape(displayname) ))

        except os.error:
            write(p, '<li class="error">Permission denied</li>')

        write(p, '</ul>')
        write(p, '<hr>')
        write(p, '<form ENCTYPE="multipart/form-data" method="post">')
        write(p, '<input name="file" type="file"/>')
        write(p, '<input type="submit" value="upload"/>')
        if success != None:
            if success == 'True':
                write(p, '<h2 class="succ">Upload successed</h2>')
            else:
                write(p, '<h2 class="error">Upload failed: {}</h2>'.format(reason))
        write(p, '</form>')
        write(p, '</body>')
        write(p, '</html>')
        length = p.tell()
        p.seek(0)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(length))
        self.end_headers()
        return p

# httpd = socketserver.TCPServer(("", PORT), Handler)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("", PORT), myHandler)

try:
    print('Serving at port: ', PORT)
    httpd.serve_forever()
except KeyboardInterrupt:
    print('KeyboardInterrupt detected, exit.')
    httpd.shutdown()
    exit()
