This toy-project was abandoned because ``python3 -m http.server`` works fine mostly.

If you need (or just want) a fancy local HTTP server, https://github.com/svenstaro/miniserve may be useful.

================
HTTP File Server
================

A simple HTTP server command line tool implemented in Python 3 with `bottle.py <http://bottlepy.org>`_.

With file uploading feature.

With curl support.

With filter support:

* hidden
* shown
* file
* dir

Example ::

  $ curl http://localhost:8000?hidden?file
  $ curl --form "upload=@<filename>" http://localhost:8000
