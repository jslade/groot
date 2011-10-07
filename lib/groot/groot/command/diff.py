
from optparse import OptionParser

from base import *

class Diff(BaseCommand):
    """ Shortcut for running diff.
    """

    def requires_repo(self):
        return True
        

    def parse_args(self,args):
        op = OptionParser()

        op.add_option("--quiet","-q", action="store_true", dest="quiet")
        op.add_option("--verbose","-v", action="store_true", dest="verbose")

        self.options, self.args = op.parse_args(args)


    def diff_args(self):
        args = []
        o = self.options

        return args
        

    def run(self):
        if self.args:
            map = self.map_args_to_submodules()
        else:
            map = self.map_all_submodules()

        self.diff_root(map)
        self.diff_submodules(map)
        

    def diff_root(self,map):
        try: paths = map['']['paths']
        except KeyError: paths=[]

        root = self.get_repo()
        root.banner()

        diff = ['diff']
        diff += self.diff_args()
        diff += paths

        root.do_git(diff)


    def diff_submodules(self,map):
        """ Run diff in each submodule
        """

        for subm in self.get_submodules():
            self.groot.flush_log()
            subm.banner(deferred=True)
            
            if not subm.rel_path in map:
                self.groot.debug("# Skipping submodule: %s" % (subm.rel_path))
                self.groot.clear_log()
                continue

            if not self.diff_submodule(subm,map[subm.rel_path]['paths']):
                self.groot.clear_log()

        self.groot.flush_log()
            

    def diff_submodule(self,subm,paths):
        diff = ['diff']
        diff += self.diff_args()
        diff += paths
        
        stdout = subm.do_git(diff,capture=True,tty=True)

        if stdout and \
               (self.options.verbose or \
                not self.submodule_is_clean(stdout)):
            self.groot.log(stdout,deferred=True)
            return True
        else:
            self.groot.log("# No changes",deferred=True)
            return self.options.verbose
            
        
    def submodule_is_clean(self,stdout):
        return stdout.strip() == ''

