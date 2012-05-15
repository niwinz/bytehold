# -*- coding: utf-8 -*-

import os
from subprocess import Popen, PIPE
from .exceptions import FileDoesNotExists

def normalized_configfile_path(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileDoesNotExists()
    return path


def absolute_path(path):
    return os.path.join(os.path.abspath("."), path)


def lazy(fn):
    def new(*args, **kwargs):
        ret = lambda *a, **k: fn(*args)
        ret.__name__ = "lazy-" + fn.__name__
        return ret
    return new


@lazy
def resolve_absolute_path(name, params="", returncodeok=0):
    proc = Popen(['which', name], stdout=PIPE, stderr=PIPE)
    return_code = p.wait()

    if return_code != returncodeok:
        return ''
    
    out, err = proc.communicate()
    cmd = out.strip().decode('utf-8')
    if params:
        return "{cmd} {params}".format(cmd=cmd, params=params)
    return cmd
