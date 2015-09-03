#!/usr/bin/env python
import bottle
import os
import show_my_ip
import sys
import datetime

show_my_ip.output()

bottle.TEMPLATE_PATH = [
    os.path.dirname(os.path.realpath(__file__))]

isdir = os.path.isdir


class FileItem:
    def __init__(self, fname):
        self.fname = fname
        self.isdir = False
        self.mtime = '----/--/-- --:--:--'

    @property
    def ftext(self):
        return self.fname + ('', '/')[self.isdir]

    @property
    def hidden(self):
        return self.fname.startswith('.')

    def setmtime(self, mtime):
        t = datetime.datetime.fromtimestamp(mtime)
        self.mtime = '{:04}/{:02}/{:02} {:02}:{:02}:{:02}'.format(
            t.year, t.month, t.day,
            t.hour, t.minute, t.second,
        )

    def __repr__(self):
        return '<FileItem: "{}">'.format(self.ftext)


class UpperDir:
    def __init__(self, dname='', dpath=''):
        self.dname = dname
        self.dpath = dpath

    def __add__(self, dname):
        return UpperDir(dname, self.dpath + '/' + dname)

    def __repr__(self):
        return '<UpperDir: "{}">'.format(self.dpath)


@bottle.route('/', method=('GET', 'POST'))
def root():
    return serve('.')


@bottle.route('/<urlpath:path>', method=('GET', 'POST'))
def serve(urlpath):
    if bottle.request.method == 'GET':
        if isdir(urlpath):
            return serve_dir(urlpath)

        return serve_file(urlpath)

    elif bottle.request.method == 'POST':
        if isdir(urlpath):
            upload = bottle.request.files.get('upload')
            filepath = os.path.join(urlpath, upload.filename)
            front, back = os.path.splitext(filepath)
            filename_probing_str = ''
            filename_probing_number = 1

            def alternative_filename():
                return '{}{}{}'.format(front, filename_probing_str, back)

            while os.path.exists(alternative_filename()):
                filename_probing_str = '-{}'.format(filename_probing_number)
                filename_probing_number += 1

            upload.save(alternative_filename())

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
    def absdir(x):
        return os.path.join(filepath, x)

    raw_fname_list = list(map(
        lambda x: FileItem(x),
        os.listdir(filepath)
    ))

    for f in raw_fname_list:
        f.isdir = isdir(absdir(f.fname))
        f.setmtime(os.path.getctime(absdir(f.fname)))

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
    temp = UpperDir()
    for i in curdir_name_split:
        temp = temp + i
        upper_dlist.append(temp)

    return upper_dlist


port = 8000 if len(sys.argv) == 1 else int(sys.argv[1])
bottle.run(host='0.0.0.0', port=port)
