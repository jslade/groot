
# Utilities for accessing git
#

import inspect
import os
import pty
import re
import select
import signal
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
        self.refs = None
        self.config = None
        

    def find_git_dir(self,path,bare=False):
        """ Find the .git dir for the given git repo path """
        if not path:
            self.path = self.git_dir = None
            return
        
        if bare: git_dir = path
        else: git_dir = os.path.join(path,'.git')
        
        if os.path.exists(git_dir):
            self.path = path
            self.git_dir = git_dir
        elif os.path.exists(os.path.join(path,'HEAD')):
            # Looks to be a bare repo:
            self.path = self.git_dir = path
        else:
            self.path = path
            self.git_dir = git_dir


    def initialized(self):
        return self.git_dir and os.path.exists(self.git_dir)

    
    def do_command(self,git_command,**kwargs):
        self.groot.debug("# In %s: %s (%s)" % (self.path,' '.join(git_command),kwargs))

        # Run the command in the root directory of the git repo
        if self.path:
            cd = safe_chdir(self.path)

        # Set up the command line and args for creating the subprocess
        call_args = {}
        if 'capture' in kwargs and kwargs['capture']:
            call_args['stdout'] = subprocess.PIPE
        if 'capture_all' in kwargs and kwargs['capture_all']:
            call_args['stdout'] = subprocess.PIPE
            call_args['stderr'] = subprocess.PIPE

        # Execute the command as a subprocess
        if 'tty' in kwargs and kwargs['tty']:
            stdout, stderr, returncode = self.do_command_with_tty(git_command,**call_args)
        else:
            stdout, stderr, returncode = self.do_command_with_pipes(git_command,**call_args)
        self.last_result = (stdout,stderr,returncode)
        self.last_command = (git_command,kwargs)

        # Some debugging output
        if self.groot.debug_mode:
            if stderr:
                for line in stderr.rstrip().split('\n'):
                    self.groot.debug("EE> %s" % line)
            if stdout:
                for line in stdout.rstrip().split('\n'):
                    self.groot.debug("--> %s" % line)

        # Check the result of the command
        expected_returncode=[0]
        if 'expected_returncode' in kwargs:
            expected_returncode=kwargs['expected_returncode']
        if type(expected_returncode) != type([]): expected_returncode=[expected_returncode]
        if not returncode in expected_returncode:
            raise GitCommandError(self,git_command)

        # Always returns stdout, which will be empty if capture=False
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

        self.groot.debug("# With TTY: %s" % (' '.join(git_command)))

        echo = False
        if 'echo' in call_args: echo=call_args['echo']
        
        master, slave = pty.openpty()
        call_args['stdout'] = slave
        master_fh = os.fdopen(master)
        
        #if 'capture_all' in call_args and call_args['capture_all']:
        #    call_args['stderr'] = subprocess.PIPE
        call_args['close_fds'] = True

        # Don't inherit the PAGER env var for the git subprocess.
        # That causes problems for things like multi-page output from git diff
        env = dict(os.environ)
        #if 'PAGER' in env: del env['PAGER']
        env['PAGER'] = ''
        call_args['env'] = env
        
        # Execute the command with a helper script that ensures we can detect
        # the end of output so it doesn't try to read (and block) forever:
        wrapper = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())),'git-wrapper.sh')
        marker = '___EOF:%s___' % (os.getpid())
        re_marker = re.compile(r'%s:([0-9]+)' % (marker))
        
        p = subprocess.Popen([wrapper,marker]+git_command,**call_args)

        stdout = ''
        stderr = ''

        monitor = [master]
        nop = []
        returncode = None
        
        while monitor:
            fds = select.select(monitor,nop,nop)[0]
            if master in fds:
                line = master_fh.readline()
                m = re_marker.search(line)
                if m:
                    monitor.remove(master)
                    returncode = int(m.group(1))
                    os.kill(p.pid,signal.SIGKILL)
                else:
                    stdout += line
                    if echo: print(line)

        p.wait()
        return (stdout, stderr, returncode)
    

    def do_command_with_pipes(self,git_command,**call_args):
        """ Run the command as a subprocess using normal pipes. The command
            will therefore not consider itself to be running on a tty/interative mode """
        self.groot.debug("# With pipes: %s" % (' '.join(git_command)))
        
        p = subprocess.Popen(git_command,**call_args)
        stdout, stderr = p.communicate()
        return (stdout, stderr, p.returncode)


    def isa_tty(self):
        """ Returns true if the output of this command is an (interactive)
            terminal """
        return sys.stdout.isatty()


    def is_clean(self,**kwargs):
        """ Returns true if both the index and working tree are clean """
        return self.is_index_clean(**kwargs) and self.is_working_tree_clean(**kwargs)


    def is_index_clean(self,**kwargs):
        cmd = ['git','diff-index','--cached','--quiet']
        if 'ignore_submodules' in kwargs and kwargs['ignore_submodules']:
            cmd += ['--ignore-submodules']
        cmd += ['HEAD']
        self.do_command(cmd,expected_returncode=[0,1])
        return self.last_result[2] == 0


    def is_working_tree_clean(self,**kwargs):
        cmd = ['git','status','-uno','--short']
        # TODO: Should use -z for more machine-friendly output for parsing?
        #if 'ignore_submodules' in kwargs and kwargs['ignore_submodules']:
        #    cmd += ['--ignore-submodules']
        stdout = self.do_command(cmd,capture=True)
        return stdout.strip() == ''
        
        
    def is_detached(self):
        head = self.get_head()
        if not head.is_ref():
            return True

    def current_branch(self):
        head = self.get_head()
        if head.branch:
            return self.simple_branch(head.name)
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


    def simple_branch(self,branch):
        m = re.match('refs/heads/(.+)',branch)
        if m: return m.group(1)
        return branch


    def remote_branch(self,branch,remote='origin'):
        if re.match('refs/remotes/[^/]+/',branch): return branch
        return 'refs/heads/%s/%s' % (remote,branch)


    def branch_exists(self,branch):
        canonical = self.canonical_branch(branch)
        branch_head_path = os.path.join(self.git_dir,canonical)
        if os.path.exists(branch_head_path):
            return True # Fast check
        refs = self.read_refs()
        if canonical in refs:
            return True
        
        
    def remote_branch_exists(self,branch,remote=None):
        remote_branch = self.find_remote_branch(branch,remote)
        return remote_branch != None


    def find_remote_branch(self,branch,remote=None):
        if remote:
            remote_path = self.remote_branch(branch,remote)
            branch_head_path = os.path.join(self.git_dir,remote_path)
            if os.path.exists(branch_head_path):
                return self.ID(remote_path)
            refs = self.read_refs()
            if remote_path in refs.keys():
                return self.ID(remote_path)
        else:
            ref_re = re.compile(r'refs/remotes/([^/]+)/%s' % (branch))
            refs = self.read_refs()
            for ref in refs.keys():
                if ref_re.match(ref):
                    return self.ID(self,ref)
            

    def read_refs(self):
        if self.refs:
            return self.refs

        self.refs = {}
        stdout = self.do_command(['git','show-ref'],capture=True)
        for line in stdout.split("\n"):
            try:
                sha1, ref = line.strip().split(' ')
                self.refs[ref] = sha1
            except ValueError: pass

        return self.refs
        

    def get_config(self,key,default=None):
        if not self.config:
            self.config = GitConfig()
            self.config.parse(os.path.join(self.git_dir,'config'))

        if key in self.config: return self.config[key] or default
        return default


    class ID(object):
        sha1_re = re.compile(r'([a-z0-9]{40})')
        branch_re = re.compile(r'(refs/heads/(\S+))')
        remote_branch_re = re.compile(r'(refs/remotes/([^/]+)/(\S+))')
        tag_re = re.compile(r'(refs/tags/(\S+))')

        def __init__(self,git,text):
            self.git = git
            self.name = None
            self.ref = None
            self.branch = False
            self.remote = None
            self.tag = False
            self.sha1 = None
            self.parse(text)

        def __repr__(self):
            if self.branch:
                if self.remote:
                    return '<Remote Branch: %s/%s>' % (self.remote,self.name)
                else:
                    return '<Branch: %s>' % (self.name)
            elif self.tag:
                return '<Tag: %s>' % (self.name)
            else:
                return '<ID: %s>' % (self.name)


        def __eq__(self,other):
            if not isinstance(other,Git.ID):
                return self.__eq__(Git.ID(self.git,str(other)))

            if self.git != other.git: return False
            if self.name != other.name: return False
            if self.branch != other.branch: return False
            if self.remote != other.remote: return False
            if self.tag != other.tag: return False
            return True
        
            
        def parse(self,raw):
            self.raw = raw.strip()
            self.name = self.raw
            
            m = self.sha1_re.search(self.raw)
            if m:
                self.sha1 = m.group(1)
                
            m = self.branch_re.search(self.raw)
            if m:
                self.ref = m.group(1)
                self.name = m.group(2)
                self.branch = True
                return

            m = self.remote_branch_re.search(self.raw)
            if m:
                self.ref = m.group(1)
                self.name = m.group(3)
                self.branch = True
                self.remote = m.group(2)
                return

            m = self.tag_re.search(self.raw)
            if m:
                self.ref = m.group(1)
                self.name = m.group(2)
                self.tag = True
                return

            

        def is_ref(self):
            return self.ref is not None
        

        def short(self):
            if is_ref: return self.name
            else: return self.name[0:8]
        

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


            
        
