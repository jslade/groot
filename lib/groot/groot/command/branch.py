
from base import *

class Branch(BaseCommand):
    """ Alias for git branch 

    """

    def requires_repo(self):
        return True
        

    def run(self):
        root = self.get_repo()
        root.do_git(['branch'] + self.args)
        
