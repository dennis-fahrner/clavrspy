import sys
import unittest
from test.TestRunner import TestRunner, Config

if __name__ == '__main__':
    Config.PRINT_LIVE = True
    Config.SINGLE_LINE_STACK = True

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test.test_cases')

    runner = TestRunner(verbosity=0)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)
