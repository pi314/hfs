#!/usr/bin/env python
import argparse
import datetime
import mimetypes
import os
import sys

from contextlib import suppress
from os.path import isdir, join
from shutil import rmtree

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

deletion_level = 0

upload_pool = set()


class FileItem:
    def __init__(self, fpath):
        self.fpath = fpath if fpath else '.'

    @property
    def fname(self):
        return os.path.basename(self.fpath)

    @property
    def ftext(self):
        return self.fname + ('/' if self.isdir else '')

    @property
    def mtime(self):
        t = datetime.datetime.fromtimestamp(os.path.getmtime(self.fpath))
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

    @property
    def parent(self):
        return FileItem(os.path.dirname(self.fpath))

    @property
    def deletable(self):
        if deletion_level == 0:
            return False

        if deletion_level == 1:
            return self.fpath in upload_pool

        return True


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
                fpath = get_uniq_fpath(join(urlpath, f.raw_filename))
                f.save(fpath)
                upload_pool.add(fpath)

        return bottle.redirect('/{}'.format(urlpath))

    elif bottle.request.method == 'DELETE':
        if not deletion_level:
            raise bottle.HTTPError(status=405)

        elif not target.exists:
            raise bottle.HTTPError(status=404)

        elif target.isdir:
            with suppress(OSError):
                rmtree(target.fpath)
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
    }

    if bottle.request.get_header('User-Agent', default='').startswith('curl'):
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


def get_uniq_fpath(filepath):
    fitem = FileItem(filepath)
    if not fitem.exists:
        return fitem.fpath

    probing_number = 1
    root, ext = os.path.splitext(fitem.fpath)
    fitem = FileItem('{}-{}{}'.format(root, probing_number, ext))
    while fitem.exists:
        probing_number += 1
        fitem = FileItem('{}-{}{}'.format(root, probing_number, ext))

    return fitem.fpath


def main():
    global deletion_level

    parser = argparse.ArgumentParser(
        description='Tiny HTTP File Server',
        prog='hfs')
    parser.add_argument('-p', '--port',
        help='The port this server should listen on',
        nargs='?', type=int, default=8000)
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s-' + __version__,
    )

    deletion_group = parser.add_mutually_exclusive_group()
    deletion_group.add_argument(
        '-d', dest='deletion_level', action='store_const', const=1,
        help='Allow HTTP DELETE method, but only uploaded files can be deleted',
    )
    deletion_group.add_argument(
        '-D', dest='deletion_level', action='store_const', const=2,
        help='Allow HTTP DELETE method, all files can be deleted',
    )
    deletion_group.set_defaults(deletion_level=0)

    args = parser.parse_args()

    deletion_level = args.deletion_level

    if deletion_level:
        print('*** Notice: Deletion Level = {} ***'.format(deletion_level))

    show_my_ip.show()

    bottle.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    main()
