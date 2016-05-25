#!/usr/bin/env python
import argparse
import datetime
import mimetypes
import os
import sys

from contextlib import suppress
from os.path import isdir, join

from hfs import bottle
from hfs import show_my_ip
from hfs.constants import __version__

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

bottle.TEMPLATE_PATH = [
    join(PROJECT_ROOT, 'html'),
]

filters = {
    'hidden': lambda x: x.hidden,
    'shown': lambda x: not x.hidden,
    'file': lambda x: not x.isdir,
    'dir': lambda x: x.isdir,
}

allow_deletion = False


class FileItem:
    def __init__(self, fpath):
        self.fpath = fpath if fpath else '.'

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
    def is_empty_dir(self):
        if not self.isdir:
            return False

        return len(os.listdir(self.fpath)) == 0

    @property
    def exists(self):
        return os.path.exists(self.fpath)

    def __repr__(self):
        return '<FileItem: "{}">'.format(self.ftext)

    @property
    def parent(self):
        return FileItem(os.path.dirname(self.fpath))


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
    return bottle.static_file(urlpath, root=join(PROJECT_ROOT, 'static'))


@bottle.route('/<urlpath:path>', method=('GET', 'POST', 'DELETE'))
def serve(urlpath):
    target = FileItem(urlpath)
    if bottle.request.method == 'GET':
        return (serve_dir if target.isdir else serve_file)(urlpath)

    elif bottle.request.method == 'POST':
        if target.isdir:
            upload = bottle.request.files.getall('upload')
            if not upload:
                # client did not provide a file
                return bottle.redirect('/{}'.format(urlpath))

            for f in upload:
                filepath = join(urlpath, f.raw_filename)
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

    elif bottle.request.method == 'DELETE':
        if not allow_deletion:
            raise bottle.HTTPError(status=405)

        elif not target.exists:
            raise bottle.HTTPError(status=404)

        elif target.isdir:
            with suppress(OSError):
                os.rmdir(target.fpath)
            return serve_dir(target.parent.fpath)

        else:
            os.remove(target.fpath)
            return serve_dir(target.parent.fpath)


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
        'allow_deletion': allow_deletion,
    }

    if bottle.request.get_header('User-Agent').startswith('curl'):
        return bottle.template('curl-listdir.html', **args)

    return bottle.template('listdir.html', **args)


def get_flist(filepath, display_filters):
    raw_flist = filter(
        lambda x: x.exists,
        map(
            lambda x: FileItem(join(filepath, x)),
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
    global allow_deletion

    parser = argparse.ArgumentParser(description='Tiny HTTP File Server')
    parser.add_argument('-p', '--port',
            help='The port this server should listen on',
            nargs='?', type=int, default=8000)
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s-' + __version__,
    )
    parser.add_argument(
        '-d', '--allow-deletion',
        help='Allow HTTP DELETE method',
        action='store_true',
    )
    args = parser.parse_args()

    allow_deletion = args.allow_deletion

    if allow_deletion:
        print('*** Notice: file deletion is allowed ***')

    show_my_ip.show()

    bottle.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    main()
