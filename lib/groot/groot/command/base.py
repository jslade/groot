
from groot.repo import Repo


class BaseCommand(object):
    """ All of the command handlers derive from this class """

    @classmethod
    def command_names(cls):
        try:
            return cls.__aliases__
        except AttributeError:
            return [ cls.__name__.lower() ]

    @classmethod
    def find_command(cls,cmd_name):
        for sub in cls.__subclasses__():
            for alias in sub.command_names():
                if alias == cmd_name:
                    return sub


    def __init__(self,groot):
        self.groot = groot
        self.root_repo = None
        self.init()
        

    def init(self):
        pass


    def parse_args(self,args):
        """ Parse all the args specific to the command """
        self.args = args


    def requires_repo(self):
        """ Whether this command requires a current repo to operate """
        raise NotImplementedError("%s.requires_repo() is missing" % (self.__class__.__name__))

    
    def run(self):
        """ Perform the actual command """
        raise NotImplementedError("%s.run() is missing" % (self.__class__.__name__))

            
    def get_repo(self):
        """ Return a Repo instance representing the root repository """
        if not self.root_repo:
            self.root_repo = Repo(self.groot,self.groot.find_repo())

        return self.root_repo


    def get_submodule(self,name):
        """ Return a Repo instance representing the specific submodule """
        repo = self.get_repo()
        return repo.get_submodule(name)


    def get_submodules(self):
        """ Return an array Repo instances representing the child repositories """
        repo = self.get_repo()
        return repo.get_submodules()


    def which_submodule(self,path):
        """ Return the submodule that the given path maps into. Also returns the path relative
            to the matched submodule.
            
            If it is not a submodule path, returns None """

        for subm in self.get_submodules():
            rel_path = subm.relative_path(path)
            if rel_path is not None:
                return (subm,rel_path)

        return (None,path)


    def map_args_to_submodules(self,**kwargs):
        """ For each file/path in the argument list, determine which submodule it maps into """

        map = {}
        for arg in self.args:
            if arg.endswith('/'):
                arg = arg[:-1]
            
            subm, sub_path = self.which_submodule(arg)
            if subm:
                if not subm.rel_path in map:
                    map[subm.rel_path] = {'subm': subm, 'paths': []}
                if sub_path != '':
                    map[subm.rel_path]['paths'].append(sub_path)
                
            else:
                if not '' in map:
                    map[''] = {'subm':None, 'paths': []}
                map['']['paths'].append(arg)


        # Add empty mapping for the root if no other mappings were made
        if len(map) == 0:
            if 'default_root' in kwargs and kwargs['default_root']:
                map[''] = {'subm':None, 'paths':[]}
            
        return map
    

    def map_all_submodules(self):
        """ For case where args is empty, create a map the includes all submodules """

        map = {}
        map[''] = { 'subm': None, 'paths': [] }
        for subm in self.get_submodules():
            map[subm.rel_path] = {'subm':subm, 'paths':[]}
        return map

    
