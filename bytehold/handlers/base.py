#!/usr/bin/env python3

import os
import shlex
import shutil
import logging
import datetime
import tempfile

from subprocess import Popen, PIPE
from contextlib import contextmanager

from ..env import Environment
from ..exceptions import FileDoesNotExists
from ..exceptions import InvalidConfiguration
from ..exceptions import InvalidCompressFormat


@contextmanager
def chdircm(new_path):
    '''chdir context manager'''
    saved_path = os.getcwd()
    os.chdir(new_path)
    yield
    os.chdir(saved_path)

class HandlerManager(object):
    instance = None
    handlers = []

    def __new__(cls, *args, **kwargs):
        if cls.instance == None:
            cls.instance = super(HandlerManager, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def register(self, handler):
        if isinstance(handler, BaseHandler):
            self.handlers.append(handler)


class BaseHandler(object):
    """
    Base class for all backup handlers.
    """

    _scheduled_for_delete = []

    def __init__(self, name='anonymous', auto_register=True, **kwargs):
        self.name = name
        self.config = kwargs
        self.env = Environment()
        self.validate_config()

        if auto_register:
            manager = HandlerManager()
            manager.register(self)

    def __del__(self):
        """
        On class is destroyed, delete all schedules files for
        deletion.
        """
        logging.debug("%s - cleaning.", self.handler_name)
        for path in set(self._scheduled_for_delete):
            if os.path.exists(path):
                logging.info("%s - deleting: %s", self.handler_name, path)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)

    def sched_for_delete(self, path):
        self._scheduled_for_delete.append(path)

    @property
    def handler_name(self):
        """
        Returns a handler class name.
        """
        return self.__class__.__name__

    def validate_config(self):
        """ 
        This is a hook for validate configuration.
        By default does nothink.
        """
        pass
    
    def run(self):
        """
        This is a main method in handler execution.
        Must be reimplemented on a subclass.
        """
        raise NotImplementedError()

    def execute(self, command, stdout=PIPE, stderr=PIPE, okreturncode=0):
        """
        Execute command and return True if is success.
        """
        with Popen(shlex.split(command), stdout=stdout, stderr=stderr) as p:
            self.print_output(p.communicate())
            returncode = p.returncode

        return returncode == okreturncode

    def compress(self, path):
        """
        This execute a compress comand for path.
        """
        command = "{command} {path}".format(
            command = self.env.command_compress(),
            path = path,
        )

        logging.info("%s - exec: %s", self.handler_name, command)

        ok = self.execute(command)
        if ok:
            return True, "{0}.xz".format(path)
        return False, path

    def tar(self, base_path, paths, tar_name, compress_format=None):
        """
        This execute a compress comand for path.
        
        - ``base_path`` indicates that path is a absolute base. Is passed to -C parameter
          of a tar executable. On make the backup, chdirs to this directory.
        - ``paths`` is a list or unique string indicates relative paths to ``base_path`` for
          more granular backup. You can put "*" for select al files located in ``base_path``.
        - ``tar_name`` is a complete name of resultant tar, without extension

        - ``compress_format`` is a compression format for a tarball, is is None, no compression
          used. Posible values are xz, bzip2 or gzip.

        """

        if isinstance(paths, str):
            if paths != "*":
                paths="'"+paths+"'"

        elif isinstance(paths, (list, tuple)):
            paths="'"+"' '".join(paths)+"'"
       
        flags, ext = "cv{extra}", "tar"
        if compress_format is not None:
            if compress_format == 'xz':
                flags = flags.format(extra='J')
                ext = "tar.xz"
            elif compress_format == 'bzip2':
                flags = flags.format(extra='j')
                ext = "tar.bz2"
            elif compress_format == 'gzip':
                flags = flags.format(extra='z')
                ext = "tar.gz"
            else:
                raise InvalidCompressFormat(compress_format)

        else:
            flags = flags.format(extra='')
        
        tmpdir = tempfile.mkdtemp()
        self.sched_for_delete(tmpdir)

        tar_path = os.path.join(tmpdir, "{name}.{ext}".format(name=tar_name, ext=ext))
        command = "{command} -{flags} -f {tar_path} -C {base_path} {paths}".format(
            command = self.env.command_tar(),
            flags = flags,
            tar_path = tar_path,
            base_path = base_path,
            paths = paths,
        )
            
        logging.info("%s - exec: %s", self.handler_name, command)
        ok = self.execute(command)
        
        if ok:
            return True, tar_path
        return False, None

    def print_output(self, output):
        """
        Prints output and stderr to console.
        Enabled only on high level of verbose.
        """
        if output[0]:
            logging.debug("stdout: %s", output[0].decode('utf-8'))

        if output[1]:
            logging.debug("stderr: %s", output[1].decode('utf-8'))

    def timestamp(self):
        """
        Returns current timestamp.
        """
        return datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    
    def scp_put(self, local_path, final_name):
        """
        Put local file to backup host.
        """
        scp_command = "{command} {path} {host}:{remote_path}/{final_name}"
        scp_command = scp_command.format(
            command = self.env.command_scp(),
            path = local_path,
            host = self.env.remote_host(),
            remote_path = self.env.remote_path(),
            final_name = final_name,
        )

        logging.info("%s - exec: %s", self.handler_name, scp_command)
        return self.execute(scp_command)

    def rsync(self, path):
        command_str = "{command} {path} {host}:{remote_path}".format(
            command = self.env.command_rsync(), 
            path = path,
            host = self.env.remote_host(),
            remote_path = self.env.remote_path()
        )
        logging.info("%s - exec: %s", self.handler_name, command_str)
        return self.execute(command_str)
