
from base import *
from groot.err import RepoNotFound


class Info(BaseCommand):
    """ Info on the current repository

    """

    def requires_repo(self):
        False
        

    def run(self):
        try:
            self.repo = self.groot.find_repo()
        except RepoNotFound:
            print("groot repo: NOT FOUND")


    


