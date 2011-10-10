
from optparse import OptionParser

from base import *

class Pull(BaseCommand):
    """ Pull in changes from the remotes for all repositories (recursively)

    """

    def requires_repo(self):
        return True
    

    def parse_args(self,args):
        op = OptionParser()

        op.add_option("--quiet","-q", action="store_true", dest="quiet")
        op.add_option("--verbose","-v", action="store_true", dest="verbose")

        op.add_option("--all", action="store_true", dest="all")
        op.add_option("--rebase", action="store_true", dest="rebase")

        self.options, self.args = op.parse_args(args)


    def pull_args(self,subm):
        args = []
        o = self.options

        # Get submodule-specific options
        if subm:
            pass

        if o.quiet: args += ['--queiet']
        if o.verbose: args += ['--verbose']

        if o.all: args += ['--all']
        if o.rebase: args += ['--rebase']

        if subm:
            if not o.all:
                args += [subm.preferred_remote(),subm.preferred_branch()]

        return args
        

    def run(self):
        """ Run pull in each submodule, then at the root """
        self.pull_submodules()
        self.pull_root()
        

    def pull_submodules(self):
        """ Run pull in each submodule
        

        """

        for subm in self.get_submodules():
            subm.banner()
            
            at_head_before = subm.is_at_head()
            self.groot.log("# At head of '%s' before commit? %s" %
                           (subm.preferred_branch(),at_head_before))

            self.pull_submodule(subm)

            at_head_after = subm.is_at_head()
            self.groot.log("# At head of '%s' after commit? %s" %
                           (subm.preferred_branch(),at_head_before))
            
            if at_head_before: #and not at_head_after:
                self.add_submodule(subm)


    def pull_submodule(self,subm):
        pull = ['pull']
        pull += self.pull_args(subm)
        
        stdout = subm.do_git(pull)

        #if stdout: #and \
        #       #(self.options.verbose or \
        #        #not self.submodule_is_clean(stdout)):
        #self.groot.log(stdout,deferred=True)
        #else:
        #    self.groot.log("# Nothing to pull",deferred=True)
            
        
    def add_submodule(self,subm):
        add = ['add',subm.rel_path]
        root = self.get_repo()
        stdout = root.do_git(add,capture=True,tty=True)

        self.groot.log(stdout,deferred=True)

            
    def pull_root(self):
        root = self.get_repo()
        root.banner()

        pull = ['pull']
        pull += self.pull_args(None)

        root.do_git(pull)

