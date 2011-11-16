
from base import *

class Log(BaseCommand):
    """ Stash changes in all repositories (recursively)

    """

    def requires_repo(self):
        True
        

    def parse_args(self,args):
        super(Log,self).parse_args(args)

        all_args = self.args
        self.options_list = []
        self.args = []
        for arg in all_args:
            if arg.startswith('-'):
                self.options_list.append(arg)
            else:
                self.args.append(arg)
                
        
    def run(self):
        map = self.map_args_to_submodules(default_root=True)
        self.log_per_submodule(map,self.options_list)


    def log_per_submodule(self,map,opts):
        """ Run log for each of the mapped submodules """
        for key in sorted(map.keys()):
            m = map[key]
            subm = m['subm']
            paths = m['paths']

            if subm:
                self.log_in_submodule(subm,paths,opts)
            else:
                self.log_in_root(paths,opts)


    def log_in_root(self,paths,opts):
        root = self.get_repo()
        root.banner()

        log = ['log'] + opts + paths
        root.do_git(log)


    def log_in_submodule(self,subm,paths,opts):
        subm.banner()
        self.groot.log(" log: %s" % (' '.join(paths)))

        log = ['log'] + opts + paths
        subm.do_git(log)



        


