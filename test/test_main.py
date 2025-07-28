from unittest import TestSuite, makeSuite, TextTestRunner
from test.test_cases import *
from TestRunner import main as TestRunner, Config
import sys

if __name__ == '__main__':
    # Class to Test Suite
    # https://stackoverflow.com/questions/12011091/trying-to-implement-python-testsuite
    suite = TestSuite()
    # Connection and all
    suite.addTest(makeSuite(TestConnection))
    # Requests
    suite.addTest(makeSuite(TestRequest))
    suite.addTest(makeSuite(TestFaultyRequest))
    suite.addTest(makeSuite(TestTransaction))

    # Configure the TestRunner
    # prints the "...E..F." live as tests happen
    Config.PRINT_LIVE = True
    # Makes the stack output a single line
    Config.SINGLE_LINE_STACK = True

    TestRunner()
    # Execute the tests
    runner = TextTestRunner()
    result = runner.run(suite)

    if not result.wasSuccessful():
        sys.exit(1)
