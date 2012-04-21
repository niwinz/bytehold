from unittest import TestCase
from bytehold.util import *
from bytehold.exceptions import FileDoesNotExists
import os


class UtilTest(TestCase):
    def test_normalize_configfile_path(self):
        with self.assertRaises(FileDoesNotExists):
            normalized_configfile_path("not-existing-file")
        current_dir = os.getcwd()
        self.assertEqual(
                normalized_configfile_path("setup.py"),
                os.path.join(current_dir, "setup.py")
        )

    def test_absolute_path(self):
        current_dir = os.getcwd()
        self.assertEqual(
                absolute_path("setup.py"), 
                os.path.join(current_dir, "setup.py")
        )
        self.assertEqual(
                absolute_path("not-existing-file"), 
                os.path.join(current_dir, "not-existing-file")
        )
