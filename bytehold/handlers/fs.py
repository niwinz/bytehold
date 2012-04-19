#!/usr/bin/env python3

import logging

from .base import BaseHandler
from ..exceptions import InvalidConfiguration

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
