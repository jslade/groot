

class RepoNotFound(Exception):
    """ Error indication that no groot-based repository could be found """
    pass

  

class InvalidUsage(Exception):
    """ Error with command-line arguments """
    pass


class GitCommandError(Exception):
    """ Error indicating an error when executing a git command """
    def __init__(self,repo_path,command,msg=''):
        super(GitCommandError,self).__init__(msg)
        self.repo_path = repo_path
        self.command = command


class GitStructureError(Exception):
    """ Error indicating git files missing or have unexpected contents """
    pass


class GitOutputError(Exception):
    """ Error indicating git command returned unexpected output """
    pass


class GitBranchNotFound(Exception):
    """ Error indicating specified branch doesn't exist in the repository """
    pass

