# -*- coding: utf-8 -*-

import os
from .exceptions import FileDoesNotExists

def normalized_configfile_path(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileDoesNotExists()
    return path


def absolute_path(path):
    return os.path.join(os.path.abspath("."), path)

