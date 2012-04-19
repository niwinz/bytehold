#!/usr/bin/env python3

import os
import logging
import tempfile

from .base import BaseHandler
from ..exceptions import InvalidConfiguration

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


