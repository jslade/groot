
from optparse import OptionParser
import re

from groot.err import *

from base import *


class Checkout(BaseCommand):
    """ Checkout a branch, tag, or specific commit in the root, and checkout
        corresponding branches, tags, or commits in submodules.

    """

    __aliases__ = ['checkout','co']


    def init(self):
        self.target_submodules = []


    def parse_args(self,args):
        op = OptionParser()
        op.add_option("-b", type="string", dest="new_branch")
        op.add_option("-t", "--track", action="store_true", dest="track")
        op.add_option("-f", "--force", action="store_true", dest="force")
        op.add_option("-N", "--no-update", action="store_true", dest="no_update")

        self.options, args = op.parse_args(args)

        self.commit = self.options.new_branch
        if self.commit:
            self.options.new_branch = True
        elif len(args):
            if not self.is_path(args[0]):
                self.commit = args.pop(0)
                self.options.new_branch = False

        # Any remaining args are specific submodules to checkout
        # TODO: perhaps they should be treated as pathspecs, and need to be mapped
        # to specific submodules (e.g. to reset a modified file)
        self.target_submodules = args

        self.groot.debug("commit options=%s" % (self.options))
        self.groot.debug("commit commit=%s" % (self.commit))
        self.groot.debug("commit submodules=%s" % (self.target_submodules))
        

    def is_path(self,pathspec):
        if re.search('/',pathspec): return True
        
        
    def requires_repo(self):
        return True
        

    def run(self):
        if not self.commit:
            if not len(self.target_submodules):
                # Re-checkout the current branch:
                self.commit = self.get_repo().current_branch()

        if self.target_submodules:
            self.checkout_submodules()
        else:
            self.checkout_root_and_submodules()


    def checkout_submodules(self):
        for subm_name in self.target_submodules:
            subm = self.get_submodule(subm_name)
            if not subm:
                self.groot.warning("-W- No such submodule: %s" % (subm_name))
                continue

            subm.banner()
            if self.update_submodule(subm):
                self.checkout_matching(subm,self.commit)
            

            
    def checkout_root_and_submodules(self):
        """ Checkout the root repository to a specific commit or branch, then recursively
            update and checkout each submodule """
        self.checkout_root()
        for subm in self.get_submodules():
            subm.banner()
            if self.update_submodule(subm):
                self.checkout_matching(subm)


    def checkout_root(self):
        """ Perform a normal git checkout of the root repository """
        root = self.get_repo()

        kwargs = { 'new_branch': self.options.new_branch,
                   'track': self.options.track,
                   'force': self.options.force }
        root.checkout(self.commit,**kwargs)

        
    def update_submodule(self,subm):
        if self.options.no_update:
            self.groot.log("# Not updating submodule: %s" % (subm.rel_path))
            return True

        return subm.update()
        
        
    def checkout_matching(self,subm,commit=None):

        preferred_branch = subm.preferred_branch()
        self.groot.debug("# Submodule %s preferred branch: %s" % (subm.rel_path,preferred_branch))

        kwargs = { 'new_branch': self.options.new_branch,
                   'track': self.options.track,
                   'force': self.options.force }

        # Can't add new_branch here, because the branch may get created in some cases before trying to
        # check it out
        #if not subm.branch_exists(preferred_branch):
        #   kwargs['new_branch'] = preferred_branch

        try:
            if subm.is_detached():
                self.groot.log("# Submodule %s is detached, looking for alternative checkout" % (subm.rel_path))

                if subm.is_at_head():
                    self.groot.log("# Submodule commit is at the head of branch '%s' --> checking out branch" %
                                   (preferred_branch))
                    if not subm.branch_exists(preferred_branch):
                        kwargs['new_branch'] = preferred_branch
                    subm.checkout(preferred_branch,**kwargs)
                elif self.options.force:
                    self.groot.log("# Submodule commit is not the head of branch '%s' --> forcing checkout of branch" %
                                   (preferred_branch))
                    if not subm.branch_exists(preferred_branch):
                        kwargs['new_branch'] = preferred_branch
                    subm.checkout(preferred_branch,**kwargs)
                else:
                    self.groot.log("# Submodule commit is not the head of branch '%s' --> Leaving detached" %
                                   (preferred_branch))
                    
            else:
                if preferred_branch and subm.current_branch() != preferred_branch:
                    self.groot.log("# Switching submodule %s to branch: %s" %
                                   (subm.rel_path,preferred_branch))
                    if not subm.branch_exists(preferred_branch):
                        kwargs['new_branch'] = preferred_branch
                    subm.checkout(preferred_branch,**kwargs)

                else:
                    self.groot.log("# Submodule %s on branch: %s" % (subm.rel_path,subm.current_branch()))


            if subm.is_detached():
                self.groot.warning("-W- Submodule in detached-head state after checkout: %s" % (subm.rel_path))

    
        except GitBranchNotFound, ex:
            self.groot.error("-E- Specified branch doesn't exist: %s" % (ex))
            return
