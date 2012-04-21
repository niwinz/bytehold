#!/usr/bin/env python3

import os
import shlex
import shutil
import logging
import datetime

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

    def tar(self, tar_path, paths, base_path="/tmp", compress_format="none"):
        """
        This execute a compress comand for path.
        """
        if isinstance(paths, str) and paths=="*":
            paths = '*'
        elif isinstance(paths, str):
            paths="'"+paths+"'"
        elif isinstance(paths, list) or isinstance(paths, tuple):
            paths="'"+"' '".join(paths)+"'"
       
        compress_options = "cf"

        if compress_format == "none":
            extension = "tar"
        elif compress_format == "xz":
            compress_options = 'J'+compress_options
            extension = "tar.xz"
        elif compress_format == "bz2":
            compress_options = 'j'+compress_options
            extension = "tar.bz2"
        elif compress_format == "gz":
            compress_options = 'z'+compress_options
            extension = "tar.gz"
        else:
            raise InvalidCompressFormat(compress_format)

        command = "tar -{compress_options} {tar_path}.{extension} {paths}".format(
                tar_path=tar_path,
                compress_options=compress_options,
                extension=extension,
                paths=paths
        )

        logging.info("%s - exec: %s", self.handler_name, command)

        with chdircm(base_path):
            ok = self.execute(command)

        if ok:
            return True, "{0}.{1}".format(tar_path, extension)
        return False, path

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
