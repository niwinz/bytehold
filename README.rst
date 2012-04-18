========
Bytehold
========

Simple backup tool written in python3, which helps not to repeat scripts.

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

Usage examples:
---------------

This is a example using ini configuration file::
    
    [niwi@vaio.niwi.be][~/devel/bytehold]% ./bh -c backup.ini -v
    Postgresql - starting postgresql handler (test).
    Postgresql - exec: pg_dump --host localhost --port 5432 -U niwi test
    Postgresql - compressing dump file.
    Postgresql - exec: /usr/bin/xz -z4 /tmp/tmprn01tf.sql
    Postgresql - exec: /usr/bin/scp /tmp/tmprn01tf.sql.xz niwi@localhost:/tmp/mormont/mormont.2012-04-18_2310.postgresql.sql.xz
    FileSystem - starting filesystem backup handler (test).
    FileSystem - exec: rsync -avr /home/niwi/pyrasite niwi@localhost:/tmp/mormont

And, this is a example using declarative python module::
    
    [niwi@vaio.niwi.be][~/devel/bytehold]% ./bh -p backup.py.example -v
    FileSystem - starting filesystem backup handler (My Temporal directory).
    FileSystem - exec: rsync -avr /home/niwi/tmp niwi@localhost:/tmp/mormont


How to install
--------------

Yo can pull the git repo and execute ``python setup.py install`` or ``easy_install-3.2 bytehold``.
