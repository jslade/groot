
from optparse import OptionParser

from base import *

import re


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


    def push_args(self):
        args = []
        o = self.options

        if o.quiet: args += ['--quiet']
        if o.verbose: args += ['--verbose']
        
        if o.all: args += ['--all']
        if o.mirror: args += ['--mirror']
        if o.delete: args += ['--delete']
        if o.tags: args += ['--tags']

        if o.dry_run: args += ['--dry-run']
        if o.porcelain: args += ['--porcelain']
        if o.progress: args += ['--progress']
        if o.force: args += ['--force']

        return args
        
        

    def run(self):
        self.push_submodules()
        self.push_root()


    def push_submodules(self):
        for subm in self.get_submodules():
            subm.banner(deferred=True,tick=True)

            push = ['push']
            push += self.push_args()

            subm.do_git(push,capture_all=True)
            stdout, stderr, returncode = subm.last_git_result()
            
            if (stdout or stderr) and \
               (self.options.verbose or \
                not self.submodule_is_clean(stdout,stderr)):
                self.groot.log(stdout)
                self.groot.warning(stderr)


    def submodule_is_clean(self,stdout,stderr):
        m = re.search("Everything up-to-date",stderr)
        if m: return True
    

    def push_root(self):
        root = self.get_repo()
        root.banner()

        push = ['push']
        push += self.push_args()

        root.do_git(push)
