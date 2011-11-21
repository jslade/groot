
from base import *

class Reset(BaseCommand):
    """ Alias for git reset

    """

    def requires_repo(self):
        return True
        

    def run(self):
        root = self.get_repo()
        root.do_git(['reset'] + self.args)
        
