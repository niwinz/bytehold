========
Bytehold
========

Simple backup tool written in python3, which helps not to repeat scripts.

Is based on handlers, and is very simple to extend. Creating a new handler and use it. The syntax is simplar to scons (declarative classes).

The simplest and most direct is to use a python module. But if you like. Ini files backups can define a very simple way.
In general, the script only needs to know that data store and how to access that data.


**Implemented handlers**

- FileSystem (use rsync for sincronize)
- PostgreSQL (use pg_dump for database dump, xz for compression and scp for transport)
- MySQL (mysqldump and mysqlhotcopy)
- Tarball (Simple compressed tarball)

**Compression format handling supported**

- Gzip
- Bzip2
- XZ (default)


**Sample python declarative configuration**::
    
    from bytehold import Environment
    from bytehold.handlers import FileSystem
    
    Environment(name="mormont", remote_host="niwi@localhost", remote_path="/tmp/")
    FileSystem(name="My Temporal directory", paths=['/home/niwi/tmp'])


Environment
-----------

``Environment`` is a mandatory class, this stores all global variables need by handlers.

**Arguments reference**

``name`` 

    Is a name that represents a backup, if not specified, hostname is used.

``remote_host``

    Is a complete host and username string that representing the backup server.

``remote_path``

    Is a base path on remote backup server on stores all backups. On this directory
    now need create other subdirectory that matches with envoronment name.

    The backup files genetated by this script, are stored on ``{remote_path}/{environ:name}/``


Usage examples:
---------------

And, this is a example::
    
    [niwi@vaio.niwi.be][~/devel/bytehold]% ./bh -p backup.py.example -v
    FileSystem - starting filesystem backup handler (My Temporal directory).
    FileSystem - exec: rsync -avr /home/niwi/tmp niwi@localhost:/tmp/mormont


How to install
--------------

Yo can pull the git repo and execute ``python setup.py install``.


TODO
----

* Sphinx documentation.
* Automaticaly create remote directory on demand. (Fix first execution fail if remote directory not exists)
* Version check handler.

