#!/usr/bin/env python
import bottle
import os
import show_my_ip
import sys
import datetime

show_my_ip.output()

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

bottle.TEMPLATE_PATH = [
    PROJECT_ROOT,
]

isdir = os.path.isdir


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
        if isdir(urlpath):
            return serve_dir(urlpath)

        return serve_file(urlpath)

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
    import mimetypes
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype is None:
        mimetype='application/octet-stream'

    return bottle.static_file(
        filepath,
        root='.',
        mimetype=mimetype
    )


def serve_dir(filepath):
    args = {
        'upper_dlist': get_upper_dir_list(filepath),
        'curdir': filepath,
        'flist': get_file_list(filepath),
        'upper_dir': os.path.dirname(filepath),
        'host': bottle.request.urlparts.netloc,
    }
    return bottle.template('listdir.html', **args)


def get_file_list(filepath):
    raw_fname_list = list(
        filter(
            lambda x: x.exists,
            map(
                lambda x: FileItem(os.path.join(filepath, x)),
                os.listdir(filepath)
            )
        )
    )

    return sorted(
        raw_fname_list,
        key=lambda x: x.isdir,
        reverse=True
    )


def get_upper_dir_list(filepath):
    if filepath == '.':
        filepath = ''

    curdir_name_split = filepath.split('/')
    upper_dlist = []
    temp = DirectoryItem()
    for i in curdir_name_split:
        temp = temp + i
        upper_dlist.append(temp)

    return upper_dlist


port = 8000 if len(sys.argv) == 1 else int(sys.argv[1])
bottle.run(host='0.0.0.0', port=port)
