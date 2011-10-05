
from base import *

class Start(BaseCommand):
    """ Start / switch to a branch in each of the repositories (recursively).

    This should be done before making changes in any of the repositories, so that changes can be tracked
    correctly on the branch. If this is not done, changes that get committed will not be associated with
    any branch, so they will be much harder to track
    """

    def requires_repo(self):
        True
        

    def run(self):
        pass


