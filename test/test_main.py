from test.TestRunner import main as TestRunner, Config

if __name__ == '__main__':
    Config.PRINT_LIVE = True
    Config.SINGLE_LINE_STACK = True

    # Custom TestRunner automatically injects itself
    TestRunner(module='test.test_cases')
