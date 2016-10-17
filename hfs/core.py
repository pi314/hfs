#!/usr/bin/env python
import argparse
import datetime
import mimetypes
import os
import re
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

flist_filters = {
    'hidden': lambda x: x.hidden,
    'shown': lambda x: not x.hidden,
    'file': lambda x: not x.isdir,
    'dir': lambda x: x.isdir,
}

deletion_level = 0

upload_pool = set()

acl = []


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


class ACLRule:
    def __init__(self, rule_str):
        # 0.0.0.0
        # localhost
        # 127.0.0.1/24
        # 127.0.0.1/255.255.255.0
        self.rule_str = rule_str
        m = re.match(r'^(d?)(\d+\.\d+\.\d+\.\d+|localhost)(?:/(\d+|\d+\.\d+\.\d+\.\d+))?$', rule_str)
        if not m:
            self.valid = False
            return

        self.valid = True
        self.deny = (m.group(1) in ('d', 'D'))
        m_addr = re.match(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)|(localhost)$', m.group(2))
        if not m_addr.group(5):
            a = int(m_addr.group(1))
            b = int(m_addr.group(2))
            c = int(m_addr.group(3))
            d = int(m_addr.group(4))
            self.addr = a << 24 | b << 16 | c << 8 | d
        else:
            self.addr = 0x7f000001

        if not m.group(3):
            self.mask = 0x00000000
            return

        m_mask = re.match(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)|(\d+)$', m.group(3))
        if not m_mask.group(5):
            a = int(m_addr.group(1))
            b = int(m_addr.group(2))
            c = int(m_addr.group(3))
            d = int(m_addr.group(4))
            self.mask = a << 24 | b << 16 | c << 8 | d
        else:
            self.mask = int(m_mask.group(5))

    def __repr__(self):
        if not self.valid:
            return '<ACLRule: invalid rule: "{}">'.format(self.rule_str)

        return '<ACLRule: "{}">'.format(self.rule_str)

    def match(self, addr):
        m_addr = re.match(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)$', addr)
        if not m_addr:
            return False

        a = int(m_addr.group(1))
        b = int(m_addr.group(2))
        c = int(m_addr.group(3))
        d = int(m_addr.group(4))
        addr = a << 24 | b << 16 | c << 8 | d
        return ((addr ^ self.addr) ^ self.mask) == 0


def is_user_agent_curl():
    return bottle.request.get_header('User-Agent', default='').startswith('curl')


def is_client_denied(client_addr):
    for rule in acl:
        if rule.match(client_addr):
            return rule.deny

    return False


@bottle.route('/', method=('GET', 'POST'))
def root():
    return serve('.')


@bottle.route('/static/<urlpath:path>')
def static(urlpath):
    return bottle.static_file(urlpath, root=join(PROJECT_ROOT, 'static'))


@bottle.route('/<urlpath:path>', method=('GET', 'POST', 'DELETE'))
def serve(urlpath):
    target = FileItem(urlpath)
    bottle.request.get('REMOTE_ADDR')
    if is_client_denied(bottle.request.get('REMOTE_ADDR')):
        raise bottle.HTTPError(status=403, body='Permission denied')

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
        if not deletion_level or not target.deletable:
            raise bottle.HTTPError(status=405, body='Deletion not permitted')

        elif not target.exists:
            raise bottle.HTTPError(status=404, body='File "{}" does not exist'.format(target.fpath))

        elif target.isdir:
            with suppress(OSError):
                rmtree(target.fpath)

            return serve_dir(target.parent.fpath)

        else:
            os.remove(target.fpath)
            return serve_dir(target.parent.fpath)


@bottle.error(403)
@bottle.error(404)
@bottle.error(405)
def error_page(error):
    status = error.status
    reason = error.body
    if isinstance(status, int):
        status = '{} {}'.format(
                status,
                bottle.HTTP_CODES.get(status, bottle.HTTP_CODES[500])
        )

    if not is_user_agent_curl():
        return '<h1>Error: {}</h1><h2>{}</h2>'.format(status, reason)

    if reason:
        return 'Error: {}\n{}\n'.format(status, reason)

    return 'Error: {}\n'.format(status)


def serve_file(filepath):
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype is None:
        mimetype='application/octet-stream'

    target_file = bottle.static_file(
        filepath,
        root='.',
        mimetype=mimetype
    )

    if target_file.status_code == 404:
        raise bottle.HTTPError(status=target_file.status, body='File "{}" does not exist'.format(filepath))

    elif target_file.status_code >= 400:
        raise bottle.HTTPError(status=target_file.status)

    return target_file


def serve_dir(filepath):
    filters = bottle.request.urlparts.query.split('?')

    args = {
        'ancestors_dlist': get_ancestors_dlist(filepath),
        'curdir': filepath,
        'flist': get_flist(filepath, filters),
        'host': bottle.request.urlparts.netloc,
        'pipe': 'pipe' in filters,
    }

    if is_user_agent_curl():
        return bottle.template('curl-listdir.html', **args)

    return bottle.template('listdir.html', **args)


def get_flist(filepath, filters):
    raw_flist = filter(
        lambda x: x.exists,
        map(
            lambda x: FileItem(join(filepath, x)),
            os.listdir(filepath)
        )
    )

    for f in filters:
        raw_flist = filter(
            flist_filters.get(f, lambda x: x),
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
    global acl
    parser = argparse.ArgumentParser(
        description='Tiny HTTP File Server',
        prog='hfs')
    parser.add_argument('-p', '--port',
        help='The port this server should listen on',
        nargs='?', type=int, default=8000)
    parser.add_argument(
        '-a', '--acl',
        help='Access Control List (first match), in the following format: "127.0.0.1", "127.0.0.1/24", "127.0.0.1/255.255.255.0". Prefix a "d" to deny a subnet',
        nargs='*', default=[])
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s-' + __version__)

    deletion_group = parser.add_mutually_exclusive_group()
    deletion_group.add_argument(
        '-d', dest='deletion_level', action='store_const', const=1,
        help='Allow HTTP DELETE method, but only uploaded files can be deleted')
    deletion_group.add_argument(
        '-D', dest='deletion_level', action='store_const', const=2,
        help='Allow HTTP DELETE method, all files can be deleted')
    deletion_group.set_defaults(deletion_level=0)

    args = parser.parse_args()

    deletion_level = args.deletion_level
    if deletion_level:
        print('*** Notice: Deletion Level = {} ***'.format(deletion_level))

    acl = [ACLRule(rule) for rule in args.acl]
    print(acl)

    show_my_ip.show()

    bottle.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    main()
