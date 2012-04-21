#!/usr/bin/env python3

import os

from .exceptions import FileDoesNotExists
from .exceptions import InvalidConfiguration


COMPRESS_COMMAND = "/usr/bin/xz -z6"
RSYNC_COMMAND = "rsync -avr"
SCP_COMMAND = "/usr/bin/scp"
TAR_COMMAND = "/bin/tar"


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

    def command_tar(self):  
        if "tar_cmd" not in self.config:
            return TAR_COMMAND
        return self.config['tar_cmd']

    def extend(self, **kwargs):
        self.config.update(kwargs)


