
from base import *

class Submodule(BaseCommand):
    """ Alias for git submodule 

    """

    def requires_repo(self):
        return True
        

    def run(self):
        root = self.get_repo()
        root.do_git('submodule',*self.args)
        
