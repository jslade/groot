
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
        op.add_option("--progress", action="store_true", dest="progress")

        op.add_option("--ff", action="store_true", dest="ff", default=True)
        op.add_option("--no-ff", action="store_false", dest="ff")
        op.add_option("--log", action="store_true", dest="log", default=True)
        op.add_option("--no-log", action="store_false", dest="log")
        op.add_option("--rebase", action="store_true", dest="rebase")
        op.add_option("--no-rebase", action="store_false", dest="rebase")
        op.add_option("--commit", action="store_true", dest="commit", default=True)
        op.add_option("--no-commit", action="store_false", dest="commit")

        op.add_option("--all", action="store_true", dest="all")
        op.add_option("--tags","-t", action="store_true", dest="tags", default=True)
        op.add_option("--no-tags", action="store_false", dest="tags")

        self.options, self.args = op.parse_args(args)


    def pull_args(self,subm):
        args = []
        o = self.options

        # Get submodule-specific options
        if subm:
            pass

        if o.quiet: args += ['--quiet']
        if o.verbose: args += ['--verbose']
        if o.progress: args += ['--progress']

        if o.all: args += ['--all']
        if not o.tags: args += ['--no-tags']

        if not o.ff: args += ['--no-ff']
        if not o.log: args += ['--no-log']
        if o.rebase: args += ['--rebase']
        if o.commit: args += ['--commit']
        else: args += ['--no-commit']
        
        if subm:
            if not o.all:
                args += [subm.preferred_remote()]
                branch = subm.current_branch()
                if branch:
                    args += [branch]
                    

        return args
        

    def run(self):
        """ Run pull in each submodule, then at the root """
        self.pull_submodules()
        self.pull_root()
        if self.options.commit: self.commit_submodules()
        

    def pull_submodules(self):
        """ Run pull in each submodule
        

        """

        self.added_submodules = []
        
        for subm in self.get_submodules():
            subm.banner()
            
            at_head_before = subm.is_at_head()
            self.groot.log("# At head of '%s' before commit? %s" %
                           (subm.preferred_branch(),at_head_before))
            commit_before = subm.get_current_commit()

            self.pull_submodule(subm)

            at_head_after = subm.is_at_head()
            self.groot.log("# At head of '%s' after commit? %s" %
                           (subm.preferred_branch(),at_head_before))
            
            if at_head_before and not at_head_after:
                self.add_submodule(subm)
                self.added_submodules.append((subm,commit_before))
                

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


    def commit_submodules(self):
        """ Make a new commit with the pulled-in changes for each submodule.
            Attempts to duplicate the commit messages from the submodules as well,
            so the commits in the root get meaningful commits.
        """
        if not self.added_submodules:
            return

        msg = ["groot pull:"]
        for s in self.added_submodules:
            subm, commit_before = s
            msg.append(self.message_for_commit(subm,commit_before))

        commit = ['commit','-m',"\n".join(msg)]
        root = self.get_repo()
        stdout = root.do_git(commit,capture=True,tty=True)

        self.groot.log(stdout,deferred=True)


    def message_for_commit(self, subm, commit_before):
        log = ['log','--pretty=oneline', '%s..' % (commit_before)]
        stdout = subm.do_git(log,capture=True)
        return stdout
            

