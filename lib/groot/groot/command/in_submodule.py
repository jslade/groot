
from base import *

class In(BaseCommand):
    """ Run a git command in a submodule, essentially the same as saying
        ( cd submodule; git some_command ... )

    """

    def requires_repo(self):
        return True

    def parse_args(self,args):
        self.subm_path = args[0]
        self.args = args[1:]

    def run(self):
        root = self.get_repo()
        subm = root.get_submodule(self.subm_path)
        subm.banner()
        subm.do_git(self.args)
        
