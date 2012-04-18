#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = (1, 0, 0, 'final', 0)

import os
import sys
import shlex
import runpy
import shutil
import logging
import datetime
import tempfile
import configparser

from subprocess import Popen, PIPE

# exceptions

class FileDoesNotExists(Exception):
    pass

class InvalidConfiguration(Exception):
    pass



# utils

def normalized_configfile_path(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileDoesNotExists()
    return path


def absolute_path(path):
    return os.path.join(os.path.abspath("."), path)



# constants

COMPRESS_COMMAND = "/usr/bin/xz -z6"
RSYNC_COMMAND = "rsync -avr"
SCP_COMMAND = "/usr/bin/scp"


class Environment(object):
    instance = None
    config = {}

    def __new__(cls, *args, **kwargs):
        if cls.instance == None:
            cls.instance = super(Environment, cls).__new__(cls, *args, **kwargs)
        return cls.instance
        
    def __init__(self, **kwargs):
        if kwargs:
            self.config.update(kwargs)

    def name(self):
        if "name" not in self.config:
            raise InvalidConfiguration()
        return self.config['name']

    def command_rsync(self):
        if "rsync_command" not in self.config:
            return RSYNC_COMMAND
        return self.config['rsync_command']

    def remote_host(self):
        if "remote_host" not in self.config:
            raise InvalidConfiguration("remote_host variable does not exist in global scope")
        return self.config['remote_host']

    def remote_path(self):
        if "remote_path" not in self.config:
            raise InvalidConfiguration()

        return os.path.join(
            self.config['remote_path'],
            self.name(),
        )

    def command_compress(self):
        if "compress_cmd" not in self.config:
            return COMPRESS_COMMAND
        return self.config["compress_cmd"]

    def command_scp(self):
        if "scp_cmd" not in self.config:
            return SCP_COMMAND
        return self.config['scp_cmd']

    def extend(self, **kwargs):
        self.config.update(kwargs)


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

# handlers

class BaseHandler(object):
    """
    Base class for all backup handlers.
    """

    _scheduled_for_delete = []

    def __init__(self, name='anonymous', **kwargs):
        self.name = name
        self.config = kwargs
        self.env = Environment()
        self.validate_config()

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


class Postgresql(BaseHandler):
    """
    This is a handler for postgresql backups.
    """

    prefix = "postgresql"
    pgdump_command_template = ("pg_dump --host {host} --port {port} "
                              "-U {user} {dbname}")

    def validate_config(self):
        if "port" not in self.config:
            self.config['port'] = '5432'
        
        if "host" not in self.config:
            self.config['host'] = 'localhost'

        if "user" not in self.config:
            self.config['user'] = os.getlogin()

        if "dbname" not in self.config:
            raise InvalidConfiguration()

        if "compress" not in self.config:
            self.config["compress"] = "1"

    def dump_db(self):
        """
        Runs pg_dump and return tuple when the first element is boolen and second
        the filename.
        """
        command = self.pgdump_command_template.format(**self.config)
        logging.info("%s - exec: %s", self.handler_name, command)

        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            ok =  self.execute(command, stdout=f)
            fname = f.name

        return ok, fname

    def run(self):
        logging.info("%s - starting postgresql handler (%s).", self.handler_name, self.name)
        
        ok, file_path = self.dump_db()
        self.sched_for_delete(file_path)

        if not ok:
            logging.error("%s - pg_dump failed.", self.handler_name)
            return
        
        if self.config["compress"] == "1":
            logging.info("%s - compressing dump file.", self.handler_name)
            
            ok, file_path = self.compress(file_path)
            self.sched_for_delete(file_path)

            if not ok:
                logging.error("%s - compress failed.", self.handler_name)
                return

        _, ext = os.path.splitext(file_path)
        
        final_name = "{name}.{stamp}.postgresql.sql{ext}".format(
            name = self.env.name(),
            ext = ext,
            stamp = self.timestamp(),
        )

        ok = self.scp_put(file_path, final_name)
        if not ok:
            logging.error("%s - failed scp.", self.handler_name)

        return ok


class FileSystem(BaseHandler):
    """
    Handler for filesystem backup with rsync.
    """

    prefix = "filesystem"

    def run(self):
        logging.info("%s - starting filesystem backup handler (%s).", self.handler_name, self.name)

        if "paths" not in self.config:
            raise InvalidConfiguration()

        paths = self.config['paths']

        if isinstance(paths, str):
            paths = paths.split(",")

        for path in paths:
            self.rsync(path)


class BaseBackup(object):
    def __init__(self, args):
        self.args = args

    def handlers(self):
        raise NotImplementedError()

    def init(self):
        for job in self.handlers():
            job.run()


class BackupIni(BaseBackup):
    handler_list = [FileSystem, Postgresql]

    def handlers(self): 
        config = configparser.ConfigParser()
        config_file_path = absolute_path(self.args.configfile)
        config.read([normalized_configfile_path(config_file_path)]) 

        if "global" not in config:
            raise InvalidConfiguration("global section not found on %s",
                normalized_configfile_path(config_file_path))

        Environment().extend(**dict(config['global']))

        for section in config.sections():
            if section == 'global':
                continue
            
            for handler in self.handler_list:
                if section.startswith(handler.prefix):
                    try:
                        prefix, name = section.split(":",1)
                    except ValueError:
                        logging.error("Section %s is not have suffix. "
                                      "Example [section:suffic]", section)
                        continue

                    instance_config = dict(config[section].items())
                    yield handler(name=name, **instance_config)


class BackupDeclarativePython(BaseBackup):
    def handlers(self):
        config_file_path = absolute_path(self.args.python_config)
        config_file_path = normalized_configfile_path(config_file_path)
        
        parsed = runpy.run_path(config_file_path)
        for handler in HandlerManager.handlers:
            yield handler
                    

class Main(object):
    def __init__(self, parser, args):
        self.parser = parser
        self.args = args

    def init(self):
        if self.args.version:
            self.parse_version(self.args)
        
        # parse logging parameters
        self.parse_verbose(self.args)

        # check config file
        if self.args.configfile:
            self.parse_ini_config(self.args)
        elif self.args.python_config:
            self.parse_python_config(self.args)
        else:
            self.parser.print_help()

    def parse_version(self, args):
        print("{name}: {v[0]}.{v[1]}".format(
            name="Bytehold", v=__version__), file=sys.stderr)
        sys.exit(0)

    def parse_verbose(self, args):
        logger = logging.getLogger()
        if args.verbose is not None:
            if args.verbose == 1:
                logger.setLevel(logging.INFO)
            else:
                logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.ERROR)

    def parse_ini_config(self, args):
        backup_instance = BackupIni(args)
        backup_instance.init()

    def parse_python_config(self, args):
        backup_instance = BackupDeclarativePython(args)
        backup_instance.init()
