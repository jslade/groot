
import os
import sys
import unittest
import yaml

import suite


class GrootTests(object):

    def __init__(self,argv):
        self.path_to_groot = argv[0]
        self.path_to_tests = argv[1]


    def run(self):
        self.create_test_suite()
        self.run_test_suite()


    def create_test_suite(self):
        print("Reading test case descriptions from %s" % (self.path_to_tests))
        description = yaml.load_all(open(self.path_to_tests))
              
        # description is a list of test cases:
        self.tests = suite.TestSuite()
        for case_desc in description:
            print("Loaded test case: %s" % (case_desc))
            case = self.tests.find_case(case_desc['name'],case_desc)
            self.tests.add_case(case)


    def run_test_suite(self):
        print("\nRunning tests:")
        unittest_suite = unittest.TestSuite(self.tests.get_ordered_test_cases())
        unittest.TextTestRunner(verbosity=2).run(unittest_suite)
    

if __name__ == '__main__':
    GrootTests(sys.argv[1:]).run()

    
    
