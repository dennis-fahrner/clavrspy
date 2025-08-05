import sys
import unittest
from test.TestRunner import TestRunner, Config
from LocalDB.Local import get_clavrs_version

if __name__ == '__main__':
    # If Subtest fails, the main test is not shown
    # Check the action logs, the .... line appears somewhere in the middle of the thing??
    Config.PRINT_LIVE = True
    Config.SINGLE_LINE_STACK = True

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test.test_cases')

    runner = TestRunner(verbosity=0, title=f"Unit Test Report <{get_clavrs_version()}>")
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)
