

class RepoNotFound(Exception):
    """ Error indication that no groot-based repository could be found """
    pass

  

class InvalidUsage(Exception):
    """ Error with command-line arguments """
    pass


class GitCommandError(Exception):
    """ Error indicating an error when executing a git command """
    def __init__(self,repo,command,msg=''):
        Exception.__init__(self,msg)
        self.repo = repo
        self.command = command

        last_cmd, self.args = repo.last_command
        self.stdout, self.stderr, self.returncode = repo.last_result

    def command_str(self):
        import pipes
        return ' '.join(pipes.quote(s) for s in self.command)


class GitStructureError(Exception):
    """ Error indicating git files missing or have unexpected contents """
    pass


class GitOutputError(Exception):
    """ Error indicating git command returned unexpected output """
    pass


class GitBranchNotFound(Exception):
    """ Error indicating specified branch doesn't exist in the repository """
    pass

