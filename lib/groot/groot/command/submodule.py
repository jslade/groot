
from base import *
from ..err import *

import os


class Submodule(BaseCommand):
    """ For the most part, equivalent to git submodule ....

        Special case for git submodule add: add doing the add, checkout the
        configured branch, if possible.
        """

    def requires_repo(self):
        return True
    

    def parse_args(self,args):
        if len(args):
            self.sub_command = args.pop(0)
        else:
            self.sub_command = None
        self.args = args

        
    def run(self):
        # Do the command
        root = self.get_repo()

        cmd = [self.cmd_name]
        if self.sub_command: cmd.append(self.sub_command)
        cmd += self.args
        root.do_git(cmd)

        # Special handling for add:
        if self.sub_command == 'add':
            self.checkout_new_submodule(root)


    def checkout_new_submodule(self,repo):
        subm_name = self.determine_submodule_name(repo)
        subm = self.get_submodule(subm_name)

        if subm.update():
            branch = self.branch_to_checkout(subm)

            kwargs = { 'new_branch': False }
            if not subm.branch_exists(branch): kwargs['new_branch'] = True

            self.groot.log("# Checking out branch on new submodule: %s" % (branch))
            subm.checkout(branch,**kwargs)



    def determine_submodule_name(self,repo):
        """ Find out the name of the submodule added via the 'add' command.
            It may be given on the command line (if add was called with the final path
            argument that says where to put it). Otherwise, have to look at the .gitmodules
            file to find the submodule that corresponds to the submodule repo
            """


        # Was the submodule path given on the command-line? If so, it's the last argument,
        # and it should correspond to an actual disk path now:
        last_arg = self.args[-1]
        self.groot.debug("# determine name of added submodule: last_arg=%s" % (last_arg))
        if os.path.exists(last_arg) and \
           os.path.abspath(last_arg).startswith(self.get_repo().path):
            self.groot.debug("# found submodule %s by path" % (last_arg))
            return last_arg

        # Doesn't appear that the submodule path was given at the end of the command line,
        # so now have to parse it out of the .gitmodules
        for subm in repo.submodules:
            if subm.url == last_arg:
                self.groot.debug("# found submodule %s by url" % (subm.rel_path))
                return subm.rel_path

        self.groot.debug("# No matching submodule: %s" % (last_arg))
        return None


    def branch_to_checkout(self,subm):
        """ What branch should it check out?
            TODO: A specific branch may have been given on the command-line
            """

        return subm.preferred_branch()
                         
        

        
