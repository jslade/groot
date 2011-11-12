
from optparse import OptionParser

from base import *

class Clone(BaseCommand):
    """ Make a clone of a remote repository, and all of the submodules.

    """

    def requires_repo(self):
        False
        

    def parse_args(self,args):
        op = OptionParser()

        op.add_option("--origin", type="string", dest="origin", default="origin")
        op.add_option("--branch","-b", type="string", dest="branch")

        op.add_option("--reference", type="string", dest="reference")
        op.add_option("--template", type="string", dest="template")
        op.add_option("--local","-l", action="store_true", dest="local")
        op.add_option("--shared","-s", action="store_true", dest="shared")
        op.add_option("--no-hardlinks", action="store_true", dest="no_hardlinks")

        op.add_option("--quiet","-q", action="store_true", dest="quiet")
        op.add_option("--verbose","-v", action="store_true", dest="verbose")
        op.add_option("--progress", action="store_true", dest="progress")

        self.options, self.args = op.parse_args(args)


    def run(self):
        self.clone_repo()

        # Originally I thought it would make sense for clone to also automatically
        # do a 'checkout', to get the submodules checked out on a branch as well, instead
        # of having them in detached-head state. But I've reconsidered and think that
        # should be a separate, explicit operation after the clone is done.
        #self.checkout_submodules()


    def clone_repo(self):
        clone = ['clone','--recursive']
        
        if self.options.origin:
            clone += ['--origin',self.options.origin]
        if self.options.branch:
            clone += ['--branch',self.options.branch]
        if self.options.reference:
            clone += ['--reference',self.options.reference]
        if self.options.template:
            clone += ['--template',self.options.template]

        if self.options.local: clone += ['--local']
        if self.options.shared: clone += ['--shared']
        if self.options.no_hardlinks: clone += ['--no-hardlinks']

        if self.options.quiet: clone += ['--quiet']
        if self.options.verbose: clone += ['--verbose']
        if self.options.progress: clone += ['--progress']

        clone += self.args

        repo = Repo(self.groot,None)
        repo.do_git(clone)


