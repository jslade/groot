#
# Groot testing suite:
# groot tests have to operate on multiple real git repositories
# they need both local (clones) and remote repositories
# test cases need to have a known starting state, like certain
#    commits, branches, modified files, etc
# test cases need to run one or more groot / git commands
# after running, test cases have to be able to check for expected outcomes,
#    like new commits, branches, etc
# commit IDs aren't fixed, so requires an alternate method for
#    identifying commits via symbolic names
#

import subprocess
import types
import unittest
import yaml

import groot.git
import groot.repo


class GrootTestSuite(object):
    
    def __init__(self):
        self.cases = {}

    def add_case(self,test_case):
        """ Add a GrootTestCase instance to the list of cases in the suite.
            Makes sure the dependencies get hooked up as well"""
        for prereq_name in test_case.prereq_names():
            prereq = self.find_case(prereq_name)
            test_case.add_prereq(prereq)

        self.cases[test_case.name] = test_case
        
        
    def find_case(self,name,desc=None):
        if not name in self.cases:
            self.cases[name] = GrootTestCase(name,desc)

        if desc: self.cases[name].description = desc
            
        return self.cases[name]


    def get_ordered_test_cases(self):
        unordered = self.cases.keys()
        ordered = []

        while len(unordered):
            progress=False
            
            for name in unordered:
                case = self.cases[name]

                all_prereqs_done = True
                for prereq in case.follows:
                    if prereq.name in unordered:
                        all_prereqs_done = False
                        break

                if all_prereqs_done:
                    ordered.append(case)
                    unordered.remove(name)
                    progress=True
                    
            if not progress:
                raise "Stuck in loop building ordered list of test cases. Ordered list=%s, unordered=%s" % \
                      ([c.name for c in ordered],unordered)

        return ordered


class GrootTestCase(unittest.TestCase):
    """ Test case is constructed from a dict (usually loaded from YAML).
        This is a unittest.TestCase, so it implements runTest() to actually perform
        the tests. But it also has functionality for ordering itself relative to other
        tests in the suite so that it's prerequisites are met """

    def __init__(self,name,description=None):
        unittest.TestCase.__init__(self)

        self._testMethodDoc = name # Display name when running the tests
        
        self.name = name
        self.description = description or {}

        self.follows = []


    def set_description(self,description):
        self.description = description
        

    def prereq_names(self):
        """ Returns the list of test case names that must precede this test case.
            Taken from the 'follows' part of the description """
        if 'follows' in self.description:
            return self.as_list(self.description['follows'])
        return []


    def add_prereq(self,prereq):
        """ Add another TestCase instance as a prerequisite of this one. This is a
            TestCase instance, created from the list returned by prereq_names() """
        self.follows.append(prereq)

    
    def as_list(self,val):
        """ Helper method to turn a value into a list if it is not already a list """
        if type(val) == types.ListType: return val
        return [val]


    def runTest(self):
        self.validate_input_state()
        self.execute_commands()
        self.validate_output_state()


    def validate_input_state(self):
        pass


    def execute_commands(self):
        pass


    def validate_output_state(self):
        pass

    

class TestRepo(object):
    """ Represents a git repo used to execute tests. The main things it provides:
        * the ability to run git commands
        * a pseudo tagging / naming facility to give symbolic names to commits/refs

        """

    def __init__(self,path,bare=False,init=True):
        self.path = path
        self.bare = bare

        self.git = groot.git.Git(path,bare)

        if init:
            self.git_init()
            

    def git_init(self):
        # Clear out the old repo (if any) and make it fresh
        if os.path.exists(self.path):
            subprocess.call(["rm","-rf",self.path])
        os.makedirs(self.path)
        
        init_cmd = ['git','init']
        if self.bare: init_cmd.append('--bare')
        self.do_cmd(init_cmd)
    

    def do_cmd(self,cmd,**kwargs):
        self.git.do_cmd(cmd,**kwargs)

        
