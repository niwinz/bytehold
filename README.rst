========
Bytehold
========

Simple backup tool, which helps not to repeat scripts.

Is based on handlers, and is very simple to extend. Creating a new handler and use it. Also, there are 2 sets of settings to use:

- Configuration files .ini
- Declarative python modules.

The simplest and most direct is to use a python module. But if you like. Ini files backups can define a very simple way.
In general, the script only needs to know that data store and how to access that data.


**Implemented handlers**

- Filesystem (use rsync for sincronize)
- Postgresql (use pg_dump for database dump, xz for compression and scp for transport)


**Sample python declarative configuration**::
    
    from bytehold import Environment, Filesystem

    Environment(name="mormont", remote_host="niwi@localhost", remote_path="/tmp/")
    FileSystem(name="My Temporal directory", paths=['/home/niwi/tmp'])


**Sample ini configuration**::

    [global]
    name=mormont
    compress_cmd=/usr/bin/xz -z4
    remote_host=niwi@localhost
    remote_path=/tmp/

    [postgresql:test]
    host=localhost
    port=5432
    user=niwi
    dbname=test

    [filesystem:test]
    paths=/home/niwi/pyrasite


How to install
--------------

Yo can pull the git repo and execute ``python setup.py install``.
