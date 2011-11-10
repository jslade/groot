
from base import *

class Clone(BaseCommand):
    """ Make a clone of a remote repository, and all of the submodules.

    """

    def requires_repo(self):
        False
        

    def run(self):
        self.clone_repo()
        self.update_submodules()
        self.checkout_branch()


    def clone_repo(self):
        pass


    def update_submodules(self):
        pass


    def checkout_branch(self):
        pass
