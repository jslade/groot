
from base import *

class Add(BaseCommand):
    """ Add files for commit in submodules, or in the root.
        Will automatically determine whether the files are in the root project,
        or in a submodule, and will run 'git add' in the appropriate submodule.
    """

    def requires_repo(self):
        return True
        

    def run(self):
        map,opts = self.map_args_to_submodules()
        self.add_per_submodule(map,opts)


    def map_args_to_submodules(self):
        """ For each file/path to be added, determine which submodule it maps into """

        map = {}
        opts = []
        
        for arg in self.args:
            if arg[0] == '-':
                opts.append(arg)
                continue

            if arg.endswith('/'):
                arg = arg[:-1]
            
            subm, sub_path = self.which_submodule(arg)
            print "arg=%s subm=%s %s" % (arg,subm,sub_path)
            if subm:
                if not subm.rel_path in map:
                    map[subm.rel_path] = {'subm': subm, 'paths': []}
                map[subm.rel_path]['paths'].append(sub_path)
                
            else:
                if not '' in map:
                    map[''] = {'subm':None, 'paths': []}
                map['']['paths'].append(arg)
                    
            
        return map,opts
    
            
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

        
        
