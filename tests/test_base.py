from unittest import TestCase
from bytehold.base import *


class BaseBackupTest(TestCase):
    def test___init__(self):
        base_backup = BaseBackup('test')
        self.assertEqual(base_backup.args, 'test')

    def test_handlers(self):
        with self.assertRaises(NotImplementedError):
            base_backup.handlers()

    def test_init(self):
        with self.assertRaises(NotImplementedError):
            base_backup.init()

class BackupIniTest(TestCase):
    def test___init__(self):
        base_backup = BackupIni('test')
        self.assertEqual(base_backup.args, 'test')

    def test_handlers(self):
        raise NotImplementedError

    def test_init(self):
        raise NotImplementedError

class BackupDeclarativePythonTest(TestCase):
    def test___init__(self):
        base_backup = BackupDeclarativePython('test')
        self.assertEqual(base_backup.args, 'test')

    def test_handlers(self):
        raise NotImplementedError

    def test_init(self):
        raise NotImplementedError

class MainTest(TestCase):
    def test___init__(self):
        raise NotImplementedError

    def test_init(self):
        raise NotImplementedError

    def test_parse_version(self):
        raise NotImplementedError

    def test_parse_verbose(self):
        raise NotImplementedError

    def test_parse_ini_config(self):
        raise NotImplementedError

    def test_parse_python_config(self):
        raise NotImplementedError
