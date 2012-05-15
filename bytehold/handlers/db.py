#!/usr/bin/env python3

import os
import logging
import tempfile

from .base import BaseHandler
from ..exceptions import InvalidConfiguration
from ..util import resolve_absolute_path

class PostgreSQL(BaseHandler):
    """
    This is a handler for postgresql backups.

    This accepts this parameters:

    * `dbname`set database name.
    * `host`: set database host.
    * `port`: set database port.
    * `compress`: set '1' if need compress pgdump output.
    * `pg_dump_command`: set a full path for a pg_dump command.

    By default, pg_dump command is resolved with `which` system command.
        
    """

    prefix = "postgresql"
    pg_dump_command = resolve_absolute_path('pg_dump')
    pg_dump_command_template = ("{pg_dump_command} --host {host} --port {port} "
                               "-U {user} {dbname}")

    default_port = 5432
    default_host = '/tmp' # used for unix socket trusted connections.

    def validate_config(self):
        if "port" not in self.config:
            self.config['port'] = self.default_port
        
        if "host" not in self.config:
            self.config['host'] = self.default_host

        if "user" not in self.config:
            self.config['user'] = os.getlogin()

        if "dbname" not in self.config:
            raise InvalidConfiguration()

        if "compress" not in self.config:
            self.config["compress"] = True
        else:
            conf_compress = self.config['compress']
            if isinstance(conf_compress, bool):
                pass
            elif conf_compress.strip() in  ('1', 'true'):
                self.config['compress'] = True
            else:
                self.config['compress'] = False

        if "pg_dump_command" not in self.config:
            if callable(self.pg_dump_command):
                self.config['pg_dump_command'] = self.pg_dump_command()
            else:   
                self.config['pg_dump_command'] = self.pg_dump_command

    def dump_db(self):
        """
        Runs pg_dump and return tuple when the first element is boolen and second
        the filename.
        """
        command = self.pg_dump_command_template.format(**self.config)
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
        
        if self.config["compress"]:
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

class MySQL(BaseHandler):
    """
    This is a handler for MySQL backups.
    """

    prefix = "mysql"

    mysqldump_command = resolve_absolute_path('mysqldump')
    mysqldump_command_template = ("{mysqldump_command} --host={host} --port={port} "
                                  "--user={user} --password={password} {dbname}")
    
    hotcopy_command = resolve_absolute_path('mysqlhotcopy')
    hotcopy_command_template = ("{hotcopy_command} --host={host} --port={port} "
                                "--user={user} {dbname} {_tmp_dir}")

    hotcopy_withpw_command_template = ("{hotcopy_command} --host={host} "
                                       "--port={port} --user={user} "
                                       "--password={password} {dbname} {_tmp_dir}")

    default_host = 'localhost'
    default_port = '3306'

    def validate_config(self):
        if "port" not in self.config:
            self.config['port'] = self.default_port
        
        if "host" not in self.config:
            self.config['host'] = self.default_host

        if "user" not in self.config:
            self.config['user'] = os.getlogin()

        if "password" not in self.config:
            self.config['password'] = ''

        if "dbname" not in self.config:
            raise InvalidConfiguration()

        if "type" not in self.config:
            raise InvalidConfiguration()

        if self.config['type'] not in ['sql', 'binary']:
            raise InvalidConfiguration()

        if "compress" not in self.config:
            self.config["compress"] = "1"

        if "hotcopy_command" not in self.config:
            if callable(self.hotcopy_command):
                self.config["hotcopy_command"] = self.hotcopy_command()
            else:
                self.config["hotcopy_command"] = self.hotcopy_command

        if "mysqldump_command" not in self.config:
            if callable(self.mysqldump_command):
                self.config['mysqldump_command'] = self.mysqldump_command()
            else:
                self.config['mysqldump_command'] = self.mysqldump_command


    def binary_backup(self):
        """
        Runs mysqlhotcopy and return tuple when the first element is boolen and second
        the filename.
        """
        dname = tempfile.mkdtemp(suffix="")
        if self.config['password'] == '':
            command = self.hotcopy_command_template.format(
                    _tmp_dir=dname,
                    **self.config
            )
        else:
            command = self.hotcopy_withpw_command_template.format(
                    _tmp_dir=dname,
                    **self.config
            )
        logging.info("%s - exec: %s", self.handler_name, command)
        ok =  self.execute(command)

        return ok, dname

    def sql_backup(self):
        """
        Runs mysqldump and return tuple when the first element is boolen and second
        the filename.
        """
        command = self.mysqldump_command_template.format(**self.config)
        logging.info("%s - exec: %s", self.handler_name, command)

        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            ok =  self.execute(command, stdout=f)
            fname = f.name

        return ok, fname

    def run(self):
        logging.info("%s - starting MySQL handler (%s).", self.handler_name, self.name)
        
        if self.config['type'] == 'sql':
            backup_command = 'mysqldump'
            ok, file_path = self.sql_backup()
            name_append = 'mysqldump'
            self.sched_for_delete(file_path)
        elif self.config['type'] == 'binary':
            backup_command = 'mysqlhotcopy'
            ok, dir_path = self.binary_backup()
            self.sched_for_delete(dir_path)
            if ok:
                ok, file_path = self.tar(dir_path, dir_path)
                self.sched_for_delete(file_path)
                name_append = 'mysqlhotcopy.tar'
        else:
            ok = False

        if not ok:
            logging.error("%s - %s failed.", self.handler_name, backup_command)
            return
        
        if self.config["compress"] == "1":
            logging.info("%s - compressing dump file.", self.handler_name)
            
            ok, file_path = self.compress(file_path)
            self.sched_for_delete(file_path)

            if not ok:
                logging.error("%s - compress failed.", self.handler_name)
                return

        _, ext = os.path.splitext(file_path)
        
        final_name = "{name}.{stamp}.mysql.{name_append}{ext}".format(
            name = self.env.name(),
            ext = ext,
            stamp = self.timestamp(),
            name_append = name_append
        )

        ok = self.scp_put(file_path, final_name)
        if not ok:
            logging.error("%s - failed scp.", self.handler_name)

        return ok
