
from base import *

class Init(AliasedCommand):

    """ Initialize a groot repository.

    Runs 'git init' (if necessary), and also creates the files needed for groot to work with
    the repository

    """

    def requires_repo(self):
        False
        

