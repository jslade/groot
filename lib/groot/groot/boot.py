
import os, sys

from groot.err import *


GIT_REPO_DIR = ".git"


class Groot(object):

  instance = None
  
  def __init__(self):
    Groot.instance = self
    self.root_repo = None
    self.verbose = False
    self.quiet = False
    self.debug_mode = False


  def main(self,argv):
    self.parse_args(argv)
    self.do_cmd()


  def parse_args(self,argv):
    import groot.args  
    self.args = groot.args.ParseArgs(self).parse(argv)
    self.options = self.args.options
    self.command = self.args.command
    

  def do_cmd(self):
    if self.command.requires_repo():
      try: self.find_repo()
      except RepoNotFound, ex:
        self.fatal(ex.message)
    self.command.run()
  

  def log(self,msg):
    if not self.quiet:
      print(msg)
      
  def debug(self,msg):
    if self.debug_mode:
      print(msg)
      
  def warning(self,msg):
    print >> sys.stderr, msg
      
  def error(self,msg):
    print >> sys.stderr, msg
      

  def find_repo(self):
    """Look for a groot-managed repository, starting at the current directory.
    """
    if self.root_repo:
      return self.root_repo

    self.find_repo_from_options() or self.find_repo_from_pwd()
    if not self.root_repo:
      raise RepoNotFound("groot-based git repository not found")

    self.log("# groot repo: %s" % (self.root_repo))

    return self.root_repo


  def find_repo_from_options(self):
    if self.options.repo:
      self.root_repo = self.options.repo
      return True


  def find_repo_from_pwd(self):
    dir = os.getcwd()
    self.root_repo = None

    olddir = None
    while dir != '/' \
          and dir != olddir:

      # First look for git root
      git_repo = os.path.join(dir,GIT_REPO_DIR)
      if os.path.isdir(git_repo):
        # This dir is the top of a git repo
        if self.is_groot_repo(dir,git_repo):
          self.root_repo = dir
          break

      olddir = dir
      dir = os.path.dirname(dir)


  def is_groot_repo(self,dir,git_repo):
    # Currently treats a git repo as a groot repo if it has
    # any submodules, as evidenced by the presence of the .gitmodules file
    modules = os.path.join(dir,'.gitmodules')
    if os.path.exists(modules):
      return True

    
  def fatal(self,msg,exit=1):
    print(msg)
    sys.exit(exit)

