
import os


class safe_chdir(object):
    def __init__(self,newpath):
        self.save_pwd = os.getcwd()
        os.chdir(newpath)

    def __del__(self):
        os.chdir(self.save_pwd)

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        return False # Pass exceptions

