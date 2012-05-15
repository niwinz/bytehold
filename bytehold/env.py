#!/usr/bin/env python3

import os

from .exceptions import FileDoesNotExists
from .exceptions import InvalidConfiguration

from .util import resolve_absolute_path

class Environment(object):
    instance = None
    config = {}

    default_compress_command = resolve_absolute_path('xz', '-z6')
    default_rsync_command = resolve_absolute_path('rsync', '-avr')
    default_scp_command = resolve_absolute_path('scp')
    default_tar_command = resolve_absolute_path('tar')

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
        if "compress_command" not in self.config:
            return self.default_compress_command()
        return self.config["compress_command"]

    def command_scp(self):
        if "scp_command" not in self.config:
            return self.default_scp_command()
        return self.config['scp_command']

    def command_tar(self):  
        if "tar_command" not in self.config:
            return self.default_tar_command()
        return self.config['tar_command']
    
    def command_rsync(self):
        if "rsync_command" not in self.config:
            return self.default_rsync_command()
        return self.config['rsync_command']

    def extend(self, **kwargs):
        self.config.update(kwargs)


