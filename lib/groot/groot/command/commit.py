
from optparse import OptionParser
from tempfile import NamedTemporaryFile
import re

from base import *


class CommitMessages(object):
    def message_for_commit(self, subm, from_commit,to_commit=None):
        if from_commit and to_commit:
            version='%s..%s' % (from_commit,to_commit)
        else:
            version='%s^..%s' % (from_commit,from_commit)
            
        log = ['log','--pretty=oneline', version]
        stdout = subm.do_git(log,capture=True)

        lines = []
        for line in stdout.split("\n"):
            if line == '': lines.append('')
            else: lines.append("%s: %s" % (subm.rel_path, line))
        return "\n".join(lines)
            
    


class Commit(BaseCommand,CommitMessages):
    """ Commit modules already added to the index per submodule.

        Also, if before the commit, the submodule commit is at the
        head of the submodule branch, automatically advance the submodule
        commit to the new head.
        
    """

    def requires_repo(self):
        return True
        

    def parse_args(self,args):
        op = OptionParser()

        op.add_option("--quiet","-q", action="store_true", dest="quiet")
        op.add_option("--verbose","-v", action="store_true", dest="verbose")

        # Message options
        op.add_option("--message","-m", type="string", dest="message")
        op.add_option("--file","-F", type="string", dest="message_file")
        op.add_option("--author", type="string", dest="author")
        op.add_option("--date", type="string", dest="date")
        op.add_option("--reedit-message","-c", type="string", dest="reedit")
        op.add_option("--reuse-message","-C", type="string", dest="reuse")

        # Include options
        op.add_option("--all","-a", action="store_true", dest="all")
        op.add_option("--only","-o", action="store_true", dest="only")
        op.add_option("--include","-i", action="store_true", dest="include")

        self.options, self.args = op.parse_args(args)
        self.added_submodules = []
        
    def commit_args(self):
        args = []
        o = self.options

        if o.quiet: args += ['--queiet']
        if o.verbose: args += ['--verbose']
        
        if o.message: args += ['--message',o.message]
        if o.message_file: args += ['--file',o.message_file]
        if o.author: args += ['--author',o.author]
        if o.date: args += ['--date',o.date]
        if o.reedit: args += ['--reedit-message',o.reedit]
        if o.reuse: args += ['--reuse-message',o.reuse]

        if o.all: args += ['--all']
        if o.only: args += ['--only']
        if o.include: args += ['--include']
        
        return args
        

    def run(self):
        if self.args:
            map = self.map_args_to_submodules()
        else:
            map = self.map_all_submodules()

        self.commit_submodules(map)
        self.commit_root(map)
        

    def commit_submodules(self,map):
        """ Run commit it each submodule, then at the root

            At each submodule, checks before if the submodule is currently at the
            head of the submodule's configured branch. If it is, add the submodule
            to the index for the root repo, so that the commit at the root will
            automatically include the submodule updates.

        """

        self.groot.debug("commit_submodules: map=%s" % (map))
        
        for subm in self.get_submodules():
            subm.banner(deferred=True,tick=True)
            
            if not subm.rel_path in map:
                self.groot.debug("# Skipping submodule: %s" % (subm.rel_path))
                continue

            at_head_before = subm.is_at_head()
            self.groot.debug("# At head of '%s' before commit? %s" %
                             (subm.preferred_branch(),at_head_before),deferred=True)
            commit_before = subm.get_current_commit()
            
            self.commit_submodule(subm,map[subm.rel_path]['paths'])

            at_head_after = subm.is_at_head()
            self.groot.log("# At head of '%s' after commit? %s" %
                           (subm.preferred_branch(),at_head_before),deferred=True)
            
            if at_head_before and not at_head_after:
                self.add_submodule(subm,commit_before)


    def commit_submodule(self,subm,paths):
        commit = ['commit']
        commit += self.commit_args()
        commit += paths

        if subm.is_clean():
            if self.options.verbose:
                self.groot.log("# Nothing to commit", deferred=True)

        kwargs = { 'tty': True,
                   'expected_returncode': [0,1] }
        subm.do_git(commit,**kwargs)
            
        
    def add_submodule(self,subm,commit_before):
        add = ['add',subm.rel_path]
        root = self.get_repo()
        stdout = root.do_git(add,capture=True,tty=True)
        self.added_submodules.append((subm,commit_before))
        
        self.groot.log(stdout,deferred=True)

            
    def commit_root(self,map):
        try: paths = map['']['paths']
        except KeyError: paths = []
        
        root = self.get_repo()
        root.banner()

        # Special case:
        # If --all option is given, but additional paths are also given:
        # Assume the additional path(s) are submodule name(s), and the --all
        # option is intended only for the submodule.
        # This has to be done before calling commit_args() for the root level only
        if self.options.all and self.args:
            self.groot.debug("# Ignoring --all option for root level")
            self.options.all = False

        # Special case:
        # If --include/--only option is given: If some of the paths mapped to submodules,
        # then include those submodules in the paths list for the root as well.
        if self.options.include or self.options.only:
            for subm_name in sorted(map.keys()):
                if not subm_name: continue # skip root
                m = map[subm_name]
                subm_paths = m['paths']
                if len(subm_paths) > 0:
                    paths.append(subm_name)

        # Special case:
        # If no commit message is given on the command line, use the commit message(s) from the
        # committed submodules
        has_message = False
        if self.options.message: has_message=True
        if self.options.message_file: has_message=True
        if self.options.reuse: has_message=True
        if self.options.reedit: has_message=True
        if not has_message:
            self.generate_commit_message_for_root()
        
        commit = ['commit']
        commit += self.commit_args()
        commit += paths

        root.do_git(commit,expected_returncode=[0,1])


    def generate_commit_message_for_root(self):
        msg = []
        for s in self.added_submodules:
            subm, commit_before = s
            msg.append(self.message_for_commit(subm,from_commit=commit_before,to_commit='HEAD'))

        if len(msg):
            msg_tmp = NamedTemporaryFile(prefix="groot-",delete=False)
            msg_tmp.write(''.join(msg))
            msg_tmp.close()

            self.options.message_file = msg_tmp.name
            self.cleanup_files.append(msg_tmp.name)
        
                       
