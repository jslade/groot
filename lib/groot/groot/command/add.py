
from base import *

class Add(BaseCommand):
    """ Add files for commit in submodules, or in the root.
        Will automatically determine whether the files are in the root project,
        or in a submodule, and will run 'git add' in the appropriate submodule.
    """

    def requires_repo(self):
        return True
        

    def parse_args(self,args):
        super(Add,self).parse_args(args)

        all_args = self.args
        self.options_list = []
        self.args = []
        for arg in all_args:
            if arg.startswith('/'):
                self.options_list.append(arg)
            else:
                self.args.append(arg)
                
        
    def run(self):
        map = self.map_args_to_submodules()
        self.add_per_submodule(map,self.options_list)


    def add_per_submodule(self,map,opts):
        """ For each mapped submodule, run 'git add' locally """
        for key in sorted(map.keys()):
            m = map[key]
            subm = m['subm']
            paths = m['paths']

            if subm:
                self.add_in_submodule(subm,paths,opts)
            else:
                self.add_in_root(paths,opts)


    def add_in_root(self,paths,opts):
        root = self.get_repo()
        root.banner()

        add = ['add'] + opts + paths
        root.do_git(add)
        

    def add_in_submodule(self,subm,paths,opts):
        subm.banner()
        self.groot.log("# add: %s" % (' '.join(paths)))
        

        add = ['add'] + opts + paths
        subm.do_git(add)

        
        
