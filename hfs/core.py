#!/usr/bin/env python
import argparse
import datetime
import mimetypes
import os
import sys

from . import __version__
from . import bottle
from . import show_my_ip

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

bottle.TEMPLATE_PATH = [
    PROJECT_ROOT,
]

isdir = os.path.isdir

filters = {
    'hidden': lambda x: x.hidden,
    'shown': lambda x: not x.hidden,
    'file': lambda x: not x.isdir,
    'dir': lambda x: x.isdir,
}


class FileItem:
    def __init__(self, fpath):
        self.fpath = fpath

    @property
    def fname(self):
        return os.path.basename(self.fpath)

    @property
    def ftext(self):
        return self.fname + ('', '/')[self.isdir]

    @property
    def mtime(self):
        t = datetime.datetime.fromtimestamp(os.path.getctime(self.fpath))
        return '{:04}/{:02}/{:02} {:02}:{:02}:{:02}'.format(
            t.year, t.month, t.day,
            t.hour, t.minute, t.second,
        )

    @property
    def size(self):
        return os.path.getsize(self.fpath)

    @property
    def hidden(self):
        return self.fname.startswith('.')

    @property
    def isdir(self):
        return isdir(self.fpath)

    @property
    def exists(self):
        return os.path.exists(self.fpath)

    def __repr__(self):
        return '<FileItem: "{}">'.format(self.ftext)


class DirectoryItem:
    def __init__(self, dname='', dpath=''):
        self.dname = dname
        self.dpath = dpath

    def __add__(self, dname):
        return DirectoryItem(dname, self.dpath + '/' + dname)

    def __repr__(self):
        return '<DirectoryItem: "{}">'.format(self.dpath)


@bottle.route('/', method=('GET', 'POST'))
def root():
    return serve('.')


@bottle.route('/static/<urlpath:path>')
def static(urlpath):
    return bottle.static_file(urlpath, root=os.path.join(PROJECT_ROOT, 'static'))


@bottle.route('/<urlpath:path>', method=('GET', 'POST'))
def serve(urlpath):
    if bottle.request.method == 'GET':
        return (serve_dir if isdir(urlpath) else serve_file)(urlpath)

    elif bottle.request.method == 'POST':
        if isdir(urlpath):
            upload = bottle.request.files.getall('upload')
            if not upload:
                # client did not provide a file
                return bottle.redirect('/{}'.format(urlpath))

            for f in upload:
                filepath = os.path.join(urlpath, f.raw_filename)
                front, back = os.path.splitext(filepath)
                filename_probing_str = ''
                filename_probing_number = 1

                def alternative_filename():
                    return '{}{}{}'.format(front, filename_probing_str, back)

                while os.path.exists(alternative_filename()):
                    filename_probing_str = '-{}'.format(filename_probing_number)
                    filename_probing_number += 1

                f.save(alternative_filename())

        return bottle.redirect('/{}'.format(urlpath))


def serve_file(filepath):
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype is None:
        mimetype='application/octet-stream'

    return bottle.static_file(
        filepath,
        root='.',
        mimetype=mimetype
    )


def serve_dir(filepath):
    display_filters = bottle.request.urlparts.query.split('?')

    args = {
        'ancestors_dlist': get_ancestors_dlist(filepath),
        'curdir': filepath,
        'flist': get_flist(filepath, display_filters),
        'host': bottle.request.urlparts.netloc,
    }

    if bottle.request.get_header('User-Agent').startswith('curl'):
        return bottle.template('curl-listdir.html', **args)

    return bottle.template('listdir.html', **args)


def get_flist(filepath, display_filters):
    raw_flist = filter(
        lambda x: x.exists,
        map(
            lambda x: FileItem(os.path.join(filepath, x)),
            os.listdir(filepath)
        )
    )

    for f in display_filters:
        raw_flist = filter(
            filters.get(f, lambda x: x),
            raw_flist,
        )

    return sorted(
        raw_flist,
        key=lambda x: x.isdir,
        reverse=True
    )


def get_ancestors_dlist(filepath):
    if filepath == '.':
        filepath = ''

    curdir_name_split = filepath.split('/')
    ancestors_dlist = []
    temp = DirectoryItem()
    for i in curdir_name_split:
        temp = temp + i
        ancestors_dlist.append(temp)

    return ancestors_dlist


def main():
    parser = argparse.ArgumentParser(description='Tiny HTTP File Server')
    parser.add_argument('-p', '--port',
            help='The port this server should listen on',
            nargs='?', type=int, default=8000)
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s-' + __version__,
    )
    args = parser.parse_args()

    show_my_ip.show()

    bottle.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    main()
