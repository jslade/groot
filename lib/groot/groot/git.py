
# Utilities for accessing git
#

import inspect
import os
import pty
import re
import select
import subprocess
import sys
import threading
import tty

from groot.boot import Groot
from groot.err import *
from groot.util import safe_chdir



class Git(object):
    def  __init__(self,path):
        self.groot = Groot.instance
        self.find_git_dir(path)


    def find_git_dir(self,path):
        """ Find the .git dir for the given git repo path """
        git_dir = "%s/.git" % (path)
        if os.path.exists(git_dir):
            self.path = path
            self.git_dir = git_dir
        else:
            self.path = self.git_dir = path


    def do_command(self,git_command,**kwargs):
        self.groot.debug("# In %s: %s" % (self.path,' '.join(git_command)))

        cd = safe_chdir(self.path)

        call_args = {}
        if 'capture' in kwargs and kwargs['capture']:
            call_args['stdout'] = subprocess.PIPE
        if 'capture_all' in kwargs and kwargs['capture_all']:
            call_args['stdout'] = subprocess.PIPE
            call_args['stderr'] = subprocess.PIPE

        if 'tty' in kwargs and kwargs['tty']:
            stdout, stderr, returncode = self.do_command_with_tty(git_command,**call_args)
        else:
            stdout, stderr, returncode = self.do_command_with_pipes(git_command,**call_args)
        self.last_result = (stdout,stderr,returncode)
        if returncode != 0:
            raise GitCommandError(self.path,git_command)

        if self.groot.debug_mode:
            if stderr:
                for line in stderr.rstrip().split('\n'):
                    self.groot.debug("EE> %s" % line)
            if stdout:
                for line in stdout.rstrip().split('\n'):
                    self.groot.debug("--> %s" % line)
        return stdout


    def do_command_with_tty(self,git_command,**call_args):
        """ Run the command as a subprocess using a pseudo-tty, so that it
             behaves as though it were running directly on an (interactive) tty.
             This means it will output default color codes, etc """
        # Adapted from subprocess.communicate and
        # http://code.google.com/p/lilykde/source/browse/trunk/runpty.py?r=314

        # If not running on an interactive terminal already, no reason
        # to fake it for git command subprocesses...
        if not self.isa_tty():
            return self.do_command_with_pipes(git_command,**call_args)


        master, slave = pty.openpty()
        call_args['stdout'] = slave
        master_fh = os.fdopen(master)
        
        #if 'capture_all' in call_args and call_args['capture_all']:
        #    call_args['stderr'] = subprocess.PIPE
        call_args['close_fds'] = True

        # Execute the command with a helper script that ensures we can detect
        # the end of output so it doesn't try to read (and block) forever:
        wrapper = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())),'git-wrapper.sh')
        marker = '___EOF:%s___' % (os.getpid())

        p = subprocess.Popen([wrapper,marker]+git_command,**call_args)

        stdout = ''
        stderr = ''

        monitor = [master]
        nop = []
        
        while monitor:
            fds = select.select(monitor,nop,nop)[0]
            if master in fds:
                line = master_fh.readline()
                if re.match(marker,line):
                    monitor.remove(master)
                else:
                    stdout += line

        p.wait()
        return (stdout, stderr, p.returncode)
    

    def do_command_with_pipes(self,git_command,**call_args):
        """ Run the command as a subprocess using normal pipes. The command
            will therefore not consider itself to be running on a tty/interative mode """
        p = subprocess.Popen(git_command,**call_args)
        stdout, stderr = p.communicate()
        return (stdout, stderr, p.returncode)


    def isa_tty(self):
        """ Returns true if the output of this command is an (interactive)
            terminal """
        return sys.stdout.isatty()

        
    def is_detached(self):
        head = self.get_head()
        if not head.is_ref():
            return True

    def current_branch(self):
        head = self.get_head()
        if head.branch:
            return head.name
        else:
            return None
        
        
    def get_head(self):
        head_path = os.path.join(self.git_dir,'HEAD')
        if not os.path.exists(head_path):
            raise GitStructureError("missing %s" % (head_path))

        fp = open(head_path,'r')
        line = fp.readline()
        return Git.ID(self,line)


    def get_head_of_branch(self,branch):
        branch_head_path = os.path.join(self.git_dir,self.canonical_branch(branch))
        if not os.path.exists(branch_head_path):
            raise GitBranchNotFound(branch)

        fp = open(branch_head_path,'r')
        line = fp.readline()
        return Git.ID(self,line)


    def canonical_branch(self,branch):
        if re.match('refs/heads/',branch): return branch
        return 'refs/heads/%s' % (branch)




    class ID(object):
        ref_re = re.compile(r'^ref: (refs/heads/(\S+))')

        def __init__(self,git,text):
            self.git = git
            self.name = None
            self.branch = False
            self.parse(text)

        def __repr__(self):
            return '<%s: %s>' % ('Branch' if self.branch else 'ID',self.name)


        def __eq__(self,other):
            if not isinstance(other,Git.ID):
                return self.__eq__(Git.ID(self.git,str(other)))

            if self.git != other.git: return False
            if self.name != other.name: return False
            if self.branch != other.branch: return False
            return True
        
            
        def parse(self,raw):
            m = self.ref_re.match(raw)
            if m:
                self.name = m.group(1)
                self.branch = True
                return

            self.name = raw.strip()
            

        def is_ref(self):
            return self.branch
        
            
        

class GitConfig(dict):
    """ Class to parse git config files """
    # TODO: would it be more reliable to use "git config -l -f <path>" to get simplified parsing?

    def parse(self,path):
        fh = open(path,'r')
        section = []

        re_section = re.compile(r'^\[(.+)\]')
        re_value = re.compile(r'^(.+)\s*=\s*(.+)$')

        for line in fh.readlines():
            if '#' in line:
                line, comment = line.split('#',1)
            line = line.strip()

            m = re_section.match(line)
            if m:
                section = self.section_name(m.group(1))
                continue

            m = re_value.match(line)
            if m:
                name = m.group(1).strip()
                value = m.group(2).strip()
                self.add(section,name,value)
                


    def section_name(self,s):
        m = re.match(r'(.+) \"(.+)\"',s)
        if m:
            return [m.group(1),re.sub(' ','_',m.group(2))]
        else:
            return [re.sub(' ','_',s)]


    def add(self,section,name,value):
        #print "%s '%s' = '%s'" % (section,name,value)
        d = self
        for s in section:
            if not s in d: d[s] = {}
            d = d[s]

        d[name.strip()] = value.strip()


            
        
