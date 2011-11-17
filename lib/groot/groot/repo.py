import os
import subprocess

from groot.git import *

class Repo(object):
    """ Interface for working with a git repository """

    def __init__(self,groot,path):
        self.groot = groot
        self.path = path
        self.git = Git(self.path)
        self.submodules = None

    
    def get_submodules(self):
        self.parse_modules()
        return self.submodules


    def get_submodule(self,rel_path):
        if rel_path.endswith('/'):
            rel_path = rel_path[:-1]
        for subm in self.get_submodules():
            if subm.rel_path == rel_path:
                return subm
            

    def parse_modules(self):
        if self.submodules:
            return

        self.submodules = []

        modules_path = os.path.join(self.path,'.gitmodules')
        if not os.path.exists(modules_path):
            self.groot.log("# No submodules file: %s" % (modules_path))
            return

        self.groot.debug("# Reading %s" % (modules_path))
        cfg = GitConfig()
        cfg.parse(modules_path)
        
        if 'submodule' in cfg:
            cfg_submodules = cfg['submodule']
            for subm in sorted(cfg_submodules.keys()):
                subm = cfg_submodules[subm]
                submodule_path = os.path.join(self.path,subm['path'])
                self.submodules.append(Submodule(self,submodule_path,**subm))
                

    def do_git(self,command,**kwargs):
        git_command = ['git']
        git_command.extend(command)
        return self.git.do_command(git_command,**kwargs)
    

    def exists(self):
        return os.path.exists(self.path)


    def banner(self,msg=None,deferred=False):
        self.groot.log("\n# ---[ %s ]---" % (self.banner_path()),deferred=deferred)
        if msg:
            self.groot.log(msg,deferred=deferred)


    def footer(self,msg='',deferred=False):
        self.groot.log(msg,deferred=deferred)


    def banner_path(self):
        return self.path
    

    def checkout(self,commit,**kwargs):
        git_command = ['checkout']
        if 'track' in kwargs and kwargs['track']: git_command.append('--track')
        if 'force' in kwargs and kwargs['force']: git_command.append('--force')
        if 'new_branch' in kwargs and kwargs['new_branch']: git_command.append('-b')
        
        git_command.append(commit)
        git_command.append('--') # End of options

        if 'paths' in kwargs and kwargs['paths']: git_command.extend(kwargs['paths'])
        
        return self.do_git(git_command)
        

    def is_clean(self):
        return self.git.is_clean()

    def is_index_clean(self):
        return self.git.is_index_clean()
    

    def is_detached(self):
        return self.git.is_detached()


    def current_branch(self):
        return self.git.current_branch()

    def get_head_commit(self):
        return self.git.get_head_of_branch(self.git.current_branch())


class Submodule(Repo):
    """ Subclass of Repo representing a submodule """
    def __init__(self,root,full_path,**kwargs):
        super(Submodule,self).__init__(root.groot,full_path)
        self.root = root
        
        if 'url' in kwargs:
            self.url = kwargs['url'] 
        else:
            self.url = None

        if 'path' in kwargs:
            self.rel_path = kwargs['path']
        else:
            self.rel_path = None

        if 'branch' in kwargs:
            self.branch = kwargs['branch']
        else:
            self.branch = 'master'

        if 'remote' in kwargs:
            self.remote = kwargs['remote']
        else:
            self.remote = 'origin'



    def __repr__(self):
        return '[submodule "%s"]' % (self.rel_path)


    def banner_path(self):
        return self.rel_path
    

    def preferred_branch(self):
        """ Returns the name of the branch that is 'preferred' for this submodule,
            as defined by the sumbodule.$path.branch config value in .gitmodules """
        return self.branch


    def preferred_remote(self):
        """ Returns the name of the remote that is 'preferred' for this submodule,
            as defined by the sumbodule.$path.origin config value in .gitmodules """
        return self.remote


    def is_detached(self):
        return self.git.is_detached()

    
    def is_at_head(self):
        """ Returns true if the current commit for this submodule is equivalent
            to the head of the submodule's preferred branch """
        return self.is_at_head_of_branch(self.preferred_branch())


    def is_at_head_of_branch(self,branch):
        """ Returns true if the current commit for this submodule is equivalent
            to the head of the specified branch """
        current_commit = Git.ID(self.git,self.get_current_commit())
        branch_head = self.git.get_head_of_branch(branch)
        self.groot.debug("# is_at_head_of_branch(%s)? %s == %s" % (branch,current_commit,branch_head))
        return current_commit == branch_head
            

    def get_current_commit(self):
        """ Returns the SHA-1 ID of the submodule's current commit (what's specified in the
            root's index, not what's currently checked-out in the submodule) """
        output = self.root.do_git(['submodule','status','--cached',self.rel_path],capture=True)

        m = re.match('([ +\-])([a-z0-9]{40}) (.+)(| \((.+)\))',output)
        if not m:
            raise GitOutputError("Didn't recognized output of 'git submodule status --cached")

        sha1 = m.group(2)
        return sha1
    
    
    def update(self):
        """ Update the submodule so it has the current commit checked out """
        self.root.do_git(['submodule','update',self.rel_path])
        return True

    

    def relative_path(self,path):
        """ Return the portion of the given path relative to this submodule's path """

        # If the path is in this submodule, it will start with the submodule directory
        if not path.startswith(self.rel_path):
            return None

        # Remove the submodule path.
        # That should leave a string that is:
        # - empty -- the submoule path itself
        # - starts with '/'
        # If the remaining path does not start with '/',
        # the path under question is not part of this submodule.
        path = path[len(self.rel_path):]
        if not (path == '' or path.startswith('/')):
            return None

        if path.startswith('/'): path = path[1:]
        if path.endswith('/'): path = path[:-1]

        return path


            
