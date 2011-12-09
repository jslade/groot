
import os
from optparse import OptionParser
from tempfile import NamedTemporaryFile

from base import *
from commit import *

class Pull(BaseCommand,CommitMessages):
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

        self.remote = None
        self.refspecs = []
        if len(self.args) > 0:
            self.remote = self.args[0]
            if len(self.args) > 1:
                self.refspecs = self.args[1:]


    def pull_args(self,subm):
        args = []
        o = self.options

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
            args += self.pull_submodule_args(subm)
        else:
            args += self.args

        return args

    
    def pull_submodule_args(self,subm):
        """ When pulling in a submodule, doesn't necessarily make sense to use the same
            remote and refspecs as for the root, but maybe...

            The default behavior for submodules is to pull everything from the default
            remote. If the user needs to do something other than that, they have to
            do expliciy git pulls instead of using groot.

            To pull everything from the default remote -- have to have a default remote
            configured. """

        # TODO: ...
        return []
        
            

    def run(self):
        """ Run pull in each submodule, then at the root """
        self.require_clean()
        self.pull_submodules()
        self.pull_root()
        if self.options.commit: self.commit_submodules()
        


    def require_clean(self):
        """ Require that the repos are all 'clean' before pulling """

        self.groot.log("# Checking that repository is clean...")
        clean = True
        for subm in self.get_submodules():
            subm.banner(deferred=True,tick=True)
            if not subm.is_clean():
                self.groot.error("-E- There are uncommitted changes.")
                clean = False

        if clean:
            self.groot.clear_log()
            root = self.get_repo()
            if not root.is_clean(ignore_submodules=True):
                self.groot.error("-E- There are uncommitted changes.")
                clean = False

        if not clean:
            self.groot.fatal("-E- The repo must be clean before pulling")

            
    def pull_submodules(self):
        """ Run pull in each submodule
        

        """
        self.groot.log("# Starting pull")
        
        self.added_submodules = []
        
        for subm in self.get_submodules():
            subm.banner(deferred=True,tick=True)
            
            at_head_before = subm.is_at_head()
            self.groot.debug("# At head of '%s' before pull? %s" %
                             (subm.preferred_branch(),at_head_before))
            commit_before = subm.get_current_commit()

            self.pull_submodule(subm)

            at_head_after = subm.is_at_head()
            self.groot.debug("# At head of '%s' after pull? %s" %
                             (subm.preferred_branch(),at_head_before))
            
            if at_head_before and not at_head_after:
                self.added_submodules.append((subm,commit_before))
                

    def pull_submodule(self,subm):
        pull = ['pull']
        pull += self.pull_args(subm)
        
        stdout = subm.do_git(pull,capture=True)

        if stdout and \
           (self.options.verbose or \
            not self.submodule_is_clean(stdout)):
            self.groot.log(stdout)


    def submodule_is_clean(self,stdout):
        m = re.search("Current branch .+ is up to date.",stdout)
        if m: return True
        
        
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
        root = self.get_repo()
        if not self.added_submodules:
            return

        msg = ["groot pull:\n"]
        for s in self.added_submodules:
            subm, commit_before = s
            msg.append(self.message_for_commit(subm,from_commit=commit_before,to_commit='HEAD'))
            self.add_submodule(subm)

        if root.is_index_clean():
            return

        msg_tmp = NamedTemporaryFile(prefix="groot-",delete=False)
        msg_tmp.write(''.join(msg))
        msg_tmp.close()
            
        commit = ['commit','-F',msg_tmp.name]
        stdout = root.do_git(commit,capture=True,tty=True)

        self.groot.log(stdout,deferred=True)

        self.cleanup_files.append(msg_tmp.name)

