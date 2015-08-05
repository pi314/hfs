#!/usr/bin/env python
import bottle
import os
import show_my_ip
import sys

show_my_ip.output()

bottle.TEMPLATE_PATH = [
    os.path.dirname(os.path.realpath(__file__))]

isdir = os.path.isdir

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
    print('['+ filepath +']')
    file_list = pretty_file_list(filepath, lambda x: not x.startswith('.'))
    hidden_file_list = pretty_file_list(filepath, lambda x: x.startswith('.'))

    args = {
        'upper_dir_list': pretty_upper_dir_list(filepath),
        'curdir': filepath,
        'hidden_file_list': hidden_file_list,
        'file_list': file_list,
        'upper_dir': os.path.dirname(filepath),
        'host': bottle.request.urlparts.netloc,
    }
    return bottle.template('listdir.html', **args)

def pretty_file_list(filepath, hidden_fileter):
    def absdir(x):
        return os.path.join(filepath, x)

    return sorted(
        map(
            lambda x: (x, x + ['', '/'][isdir(absdir(x))]),
            filter(hidden_fileter, os.listdir(filepath))
        ),
        key=lambda x:x[1].endswith('/'),
        reverse=True
    )

def pretty_upper_dir_list(filepath):
    if filepath == '.':
        filepath = ''

    curdir_name_split = list(enumerate(filepath.split('/')))
    upper_dir_list = [('/'.join(map(lambda x:x[1], curdir_name_split[:i+1])), d) for i,d in curdir_name_split]
    return upper_dir_list

port = 8000 if len(sys.argv) == 1 else int(sys.argv[1])
bottle.run(host='0.0.0.0', port=port)
