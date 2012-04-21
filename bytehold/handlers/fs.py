#!/usr/bin/env python3

import logging
import tempfile

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

    def run(self):
        logging.info("%s - starting filesystem backup handler (%s).", self.handler_name, self.name)

        if "paths" not in self.config:
            raise InvalidConfiguration()
        if "base_path" not in self.config:
            self.config['base_path'] = "."
        if "compress_format" not in self.config:
            self.config['compress_format'] = "gz"

        paths = self.config['paths']

        with tempfile.NamedTemporaryFile(suffix="", delete=False) as f:
            file_name = f.name

        ok, file_name = self.tar(
                file_name, paths,
                base_path=self.config['base_path'],
                compress_format=self.config['compress_format']
        )
        self.sched_for_delete(file_name)
        if not ok:
            logging.error("%s - failed tar.", self.handler_name)

        ext = ".".join(file_name.split(".")[1:])

        final_name = "{name}.{stamp}.tarball.{ext}".format(
            name = self.env.name(),
            ext = ext,
            stamp = self.timestamp(),
        )

        ok = self.scp_put(file_name, final_name)
        if not ok:
            logging.error("%s - failed scp.", self.handler_name)

        return ok
