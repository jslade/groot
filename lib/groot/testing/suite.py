
import types
import unittest
import yaml


class TestSuite(object):
    
    def __init__(self):
        self.cases = {}

    def add_case(self,test_case):
        """ Added a TestCase instance to the list of cases in the suite.
            Makes sure the dependencies get hooked up as well"""
        for prereq_name in test_case.prereq_names():
            prereq = self.find_case(prereq_name)
            test_case.add_prereq(prereq)

        self.cases[test_case.name] = test_case
        
        
    def find_case(self,name,desc=None):
        if not name in self.cases:
            self.cases[name] = TestCase(name,desc)

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


class TestCase(unittest.TestCase):
    """ Test case is constructed from a dict (usually loaded from YAML) """

    def __init__(self,name,description=None):
        unittest.TestCase.__init__(self)

        self._testMethodDoc = name # Display name when running the tests
        
        self.name = name
        self.description = description or {}

        self.follows = []


    def set_description(self,description):
        self.description = description
        

    def prereq_names(self):
        if 'follows' in self.description:
            return self.as_list(self.description['follows'])

        return []


    def add_prereq(self,prereq):
        self.follows.append(prereq)

    

    def as_list(self,val):
        if type(val) == types.ListType: return val
        return [val]




    def runTest(self):
        pass

    
