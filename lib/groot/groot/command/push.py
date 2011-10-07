
from optparse import OptionParser

from base import *

class Push(BaseCommand):
    """ Push changes in all repositories (recursively) to the remote

    """

    def requires_repo(self):
        True
        

    def parse_args(self,args):
        op = OptionParser()

        op.add_option("--quiet","-q", action="store_true", dest="quiet")
        op.add_option("--verbose","-v", action="store_true", dest="verbose")

        op.add_option("--all","-a", action="store_true", dest="all")
        op.add_option("--mirror", action="store_true", dest="mirror")
        op.add_option("--delete", action="store_true", dest="delete")
        op.add_option("--tags", action="store_true", dest="tags")
        op.add_option("--dry-run","-n", action="store_true", dest="dry_run")

        op.add_option("--porcelain", action="store_true", dest="porcelain")
        op.add_option("--progress", action="store_true", dest="progress")
        op.add_option("--force","-f", action="store_true", dest="force")

        
        self.options, self.args = op.parse_args(args)


    def run(self):
        pass


