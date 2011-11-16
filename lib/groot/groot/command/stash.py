
import re

from base import *
from groot.util import *
from groot.git import *


class Stash(BaseCommand):
    """ Stash changes in all repositories (recursively).
        When creating a stash (stash save), attempts to mark
        all the stashes in the submodules, so when doing a
        pop, all the corresponding stashes can be popped together --
        it's not safe to assume we're just popping the most recent.

    """

    def requires_repo(self):
        True
        

    def parse_args(self,args):
        super(Stash,self).parse_args(args)

        self.command = 'save'
        self.options_list = []
        if self.args:
            if not self.args[0].startswith('-'):
                self.command = self.args.pop(0)

            all_args = self.args
            self.args = []
            for arg in all_args:
                if arg.startswith('-'):
                    self.options_list.append(arg)
                else:
                    self.args.append(arg)
                
        
    def run(self):
        if self.command == 'save':
            stash_tag = self.save_root()
            self.save_submodules(stash_tag)

        elif self.command in ['pop','apply','drop']:
            stash_tag = self.pop_root()
            self.pop_submodules(stash_tag)

        elif self.command in ['clear']:
            self.misc_command_in_root_and_submodules()

        else:
            self.misc_command_in_root()



    def save_root(self):
        """ Run stash save in the root, and return the tag  """
        root = self.get_repo()
        root.banner()

        # Generate a stash ID used to tag corresponding stashes
        tag = '[groot-%s]' % (random_string())

        # The tag needs to go into the message. If no message is
        # given already, have to manually generate one to include
        # the tag, instead of leaving it to git to generate.
        message = ' '.join(self.args)
        if not message:
            log = root.do_git(['log','--pretty=oneline','-1','HEAD'],capture=True)
            sha1, rest = log.strip().split(' ',1)
            message = "%s %s" % (sha1[0:7],rest)


        # Do the stash
        save = ['stash','save']
        save += self.options_list
        save += [message,tag]

        root.do_git(save)


        return tag


    def save_submodules(self,tag):
        """ Run stash save in each submodule, using the given tag
            in the stash message """

        for subm in self.get_submodules():
            subm.banner()

            # The tag needs to go into the message. If no message is
            # given already, have to manually generate one to
            # include the tag
            message = ' '.join(self.args)
            if not message:
                log = subm.do_git(['log','--pretty=oneline','-1','HEAD'],capture=True)
                sha1, rest = log.strip().split(' ',1)
                message = "%s %s" % (sha1[0:7],rest)
            
            # Do the stash
            save = ['stash','save']
            save += self.options_list
            save += [message,tag]

            subm.do_git(save)

        
    def pop_root(self):
        """ Do pop/apply in the root repo.
            Also, extract the tag from the stash message to be able
            to pop the corresponding stashes from the submodules """

        root = self.get_repo()
        root.banner()

        # Prior to doing the pop, have to first get a list of all stashes,
        # in order to extract the tag string from the message -- that info
        # is gone once the pop is done.
        # Just get it and save it, parse it later when it's needed.
        list_output = root.do_git(['stash','list'],capture=True)

        pop = ['stash',self.command] # May not just be pop (also apply)
        pop += self.options_list
        pop += self.args

        root.do_git(pop)


        # Which stash was popped/applied?
        # Always the most recent if not specified:
        stash = 'stash@{0}'
        if self.args:
            stash = self.args[0]

        # Extract the tag from the message for that stash:
        for line in list_output.split("\n"):
            m = re.match(r"(stash@[^:]+): .*\[(groot-.+)\]",line)
            print("extract tag: line=%s" % (line))
            if m: print("    m[1]=%s m[2]=%s" %(m.group(1),m.group(2)))
            if m and m.group(1) == stash:
                tag = m.group(2)
                self.groot.debug("# groot pop stash=%s tag=%s" % (stash,tag))
                return tag

        self.groot.warning("-W- Couldn't find a groot stash tag for %s" % (stash) +
                           ", not performing '%s' in submodules" % (self.command))
        return None

        
    def pop_submodules(self,tag):
        """ Perform pop/apply on each submodule, iff a stash is found with 
            the matching tag in the stash message """
        if not tag: return

        for subm in self.get_submodules():
            subm.banner()

            # Get the list of all stash, find the one matching the given tag:
            stash = None
            list = subm.do_git(['stash','list'],capture=True)
            for line in list.split("\n"):
                m = re.match(r"(stash@[^:]+): .*\[(groot-.+)\]",line)
                if m and m.group(2) == tag:
                    stash = m.group(1)
                    break

            if not stash:
                self.groot.log("# No matching stash tagged as '%s'" % (tag))
                continue

            # Pop/apply the specific stash in this submodule
            pop = ['stash',self.command]
            pop += self.options_list
            pop += [stash]

            subm.do_git(pop)

            
    def misc_command_in_root(self):
        """ Run any of the other misc stash commands, but only
            only the root repo. This should act pretty much like
            calling 'git stash ...' instead of 'groot stash ...' """

        stash = ['stash',self.command] + self.options_list + self.args
        root = self.get_repo()
        root.do_git(stash)


    def misc_command_in_root_and_submodules(self):
        """ Run any of the other misc stash commands, but only
            only the root repo. This should act pretty much like
            calling 'git stash ...' instead of 'groot stash ...' """

        stash = ['stash',self.command] + self.options_list + self.args

        root = self.get_repo()
        root.banner()
        root.do_git(stash)

        for subm in self.get_submodules():
            subm.banner()
            subm.do_git(stash)



