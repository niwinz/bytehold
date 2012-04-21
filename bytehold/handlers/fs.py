#!/usr/bin/env python3

import logging
import tempfile
import os

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

class Tarball(BaseHandler):
    """
    Handler for tarball backup
    """

    prefix = "tarball"

    def validate_config(self):
        if "paths" not in self.config:
            raise InvalidConfiguration("path parameter is mandatory.")

        if "base_path" not in self.config:
            self.config['base_path'] = '.'

        if "compress_format" not in self.config:
            self.config['compress_format'] = "xz"

    def run(self):
        logging.info("%s - starting filesystem backup handler (%s).", self.handler_name, self.name)

        paths = self.config['paths']
        base_path = self.config['base_path']
        compress_format = self.config['compress_format']

        final_name = "{name}.{stamp}.tarball".format(
            name = self.env.name(),
            stamp = self.timestamp(),
        )

        ok, path  = self.tar(base_path, paths, final_name, compress_format)
        if not ok:
            logging.error("%s - failed tar.", self.handler_name)
            return None

        self.sched_for_delete(path)
        final_name = os.path.basename(path)
        ok = self.scp_put(path, final_name)
        if not ok:
            logging.error("%s - failed scp.", self.handler_name)

        return ok
