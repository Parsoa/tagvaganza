import os
import pwd
import sys
import argparse

import colorama

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class Configuration:

    kmer_cache_size = 10000

    class __impl:
        def __init__(self,
                        work_dir):
            self.work_dir = work_dir

    __instance = None

    def __init__(self, **kwargs):
        if Configuration.__instance is None:
            Configuration.__instance = Configuration.__impl(**kwargs)

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

# ============================================================================================================================ #
# Configuration
# ============================================================================================================================ #

def init():
    configure(parse_args())

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default = os.path.abspath('/Users/Parsoa/Desktop/tagvaganza'))
    args = parser.parse_args()
    #
    return args

def configure(args):
    colorama.init()
    Configuration(
        work_dir = args.path
    )