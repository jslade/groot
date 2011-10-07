
from optparse import OptionParser
import re

from base import *

class Status(BaseCommand):
    """ Report status of all repositories (recursively)

    """

    __aliases__ = ['status','st','stat']


    def requires_repo(self):
        return True
        

    def parse_args(self,args):
        op = OptionParser()
        op.add_option("--short","-s", action="store_true", dest="short")
        op.add_option("--verbose","-v", action="store_true", dest="verbose")

        self.options, self.args = op.parse_args(args)
        

    def run(self):
        self.root_status()
        for subm in self.get_submodules():
            self.submodule_status(subm)
        #self.root_footer()
        

    def root_status(self):
        root = self.get_repo()
        root.banner()

        status = ['status']
        if self.options.short: status.append('--short')
        status.extend(self.args)

        root.do_git(status)


    def root_footer(self):
        root = self.get_repo()
        root.footer()
        

    def submodule_status(self,subm):
        if not subm.exists():
            self.groot.warning("-W- Missing submodule: %s" % (subm.rel_path))
            return

        args = self.args
        if self.options.short: args.append('--short')

        cmd = ['status']
        cmd.extend(args)
        stdout = subm.do_git(cmd,capture=True,tty=True)

        if stdout and \
               (self.options.verbose or \
                not self.submodule_is_clean(stdout)):
            subm.banner()
            print stdout


    def submodule_is_clean(self,stdout):
        m = re.search("Not currently on any branch",stdout)
        if m: return False
        
        m = re.search("nothing to commit \(working directory clean\)",stdout)
        if m: return True




