#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import runpy
import logging
import configparser

from .util import normalized_configfile_path
from .util import absolute_path
from .env import Environment

# temporary handlers import
from .handlers import FileSystem, Postgresql, MySQL, Tarball

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

        from .handlers.base import HandlerManager
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
