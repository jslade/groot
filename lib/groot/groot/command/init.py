
from base import *

class Init(BaseCommand):
    """ Initialize a groot repository.

    Runs 'git init' (if necessary), and also creates the files needed for groot to work with
    the repository

    """

    def requires_repo(self):
        False
        

    def run(self):
        pass


