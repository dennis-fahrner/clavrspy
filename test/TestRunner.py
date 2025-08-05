"""
https://gist.github.com/viniciusd/73e6eccd39dea5e714b1464e3c47e067
A TestRunner for use with the Python unit testing framework. It
generates a tabular report to show the result at a glance.

The simplest way to use this is to invoke its main method. E.g.

    import unittest
    import TestRunner

    ... define your tests ...

    if __name__ == '__main__':
        TestRunner.main()

    # run the test
    runner.run(my_test_suite)


This TestRunner is based on HTMLTestRunner <http://tungwaiyip.info/software/HTMLTestRunner.html>
It is likely that I will rewrite this module form scracth soon.
By the way, HTMLTestRunner's license does not cover forking, given that I removed HTMLTestRunner's main characteristic(the HTML), I decided also removing the license. If I did not interpret the license properly, please, let me know.
HTMLTestRunner's author is Wai Yip Tung and I am grateful for his contribution.
"""

import datetime

try:
    from StringIO import StringIO # type: ignore
except ImportError:
    from io import StringIO
import io
import time
import types
import sys
import re
import humanize
import unittest


class Config:
    PRINT_LIVE: bool = True
    SINGLE_LINE_STACK: bool = True


# ------------------------------------------------------------------------
# The redirectors below are used to capture output during testing. Output
# sent to sys.stdout and sys.stderr are automatically captured. However
# in some cases sys.stdout is already cached before HTMLTestRunner is
# invoked (e.g. calling logging.basicConfig). In order to capture those
# output, use the redirectors for the cached stream.
#
# e.g.
#   >>> logging.basicConfig(stream=HTMLTestRunner.stdout_redirector)
#   >>>

class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """

    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()


stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


class Table(object):

    def __init__(self, padding='', allow_newlines=False):
        self.__columnSize__ = []
        self.__rows__ = []
        self.__titles__ = None
        self.padding = padding
        self.allow_newlines = allow_newlines

    def __length__(self, x):  # type: ignore
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return len(ansi_escape.sub('', x))
        # return len(re.sub(r"\033\[[0-9];[0-9];[0-9]{1,2}m", "", x))

    def addRow(self, row):
        rows = [[''] for l in range(len(row))]
        maxrows = 1
        for i, x in enumerate(row):
            for j, y in enumerate(x.split("\n")):
                if len(y) == 0 and self.allow_newlines == False:
                    continue
                try:
                    self.__columnSize__[i] = max(self.__columnSize__[i], self.__length__(y))
                except IndexError:
                    self.__columnSize__.append(self.__length__(y))
                rows[i].append(y)
                maxrows = max(j, maxrows)
        for i in range(len(rows)):
            rows[i] += (maxrows - (len(rows[i]) - 1)) * ['']
        for i in range(maxrows):
            self.__rows__.append([rows[j][i + 1] for j in range(len(row))])

    def addTitles(self, titles):
        for i, x in enumerate(titles):
            try:
                self.__columnSize__[i] = max(self.__columnSize__[i], self.__length__(x))
            except IndexError:
                self.__columnSize__.append(self.__length__(x))
        self.__titles__ = titles

    def __repr__(self):
       # Collect all rows including titles
        all_rows = []
        if self.__titles__:
            all_rows.append(self.__titles__)
        all_rows.extend(self.__rows__)

        # Compute column count
        col_count = max(len(r) for r in all_rows) if all_rows else 0

        # Pad all rows to col_count
        for i in range(len(all_rows)):
            if len(all_rows[i]) < col_count:
                all_rows[i] += [''] * (col_count - len(all_rows[i]))

        # Compute max widths per column using visible lengths
        col_widths = [0] * col_count
        for r in all_rows:
            for i, cell in enumerate(r):
                length = self.__length__(cell)
                if length > col_widths[i]:
                    col_widths[i] = length

        # Build horizontal line
        hline_base = self.padding + "{left}"  # left char (e.g. "┌")
        middle_parts = []
        for index, w in enumerate(col_widths):
            if index == len(col_widths) - 1:
                build_char = "{right}"  # right bound placeholder
            else:
                build_char = "{mid}"    # middle junction placeholder
            middle_parts.append("─" * (w + 2) + build_char)
        hline_base += "".join(middle_parts)

        # Now fill in the placeholders
        hline_top = hline_base.format(left="┌", mid="┬", right="┐")
        hline_mid = hline_base.format(left="├", mid="┼", right="┤")
        hline_bot = hline_base.format(left="└", mid="┴", right="┘")

        # Build title line
        if self.__titles__:
            titles_padded = []
            for i, t in enumerate(self.__titles__):
                titles_padded.append(t.center(col_widths[i]))
            title_line = self.padding + "│ " + " │ ".join(titles_padded) + " │"
            output = hline_top + "\n" + title_line + "\n" + hline_mid + "\n"
        else:
            output = hline_top + "\n"

        # Build data rows
        for r in self.__rows__:
            if len(r) < col_count:
                r += [''] * (col_count - len(r))
            padded_cells = []
            for i, c in enumerate(r):
                visible_len = self.__length__(c)
                padded_cells.append(c + ' ' * (col_widths[i] - visible_len))
            output += self.padding + "│ " + " │ ".join(padded_cells) + " │\n"

        output += hline_bot + "\n"
        return output


class bcolors(object):
    FORMAT = {
        'Regular': '0',
        'Bold': '1',
        'Underline': '4',
        'High Intensity': '0',  # +60 on color
        'BoldHighIntensity': '1',  # +60 on color
    }
    START = "\033["
    COLOR = {
        'black': "0;30m",
        'red': "0;31m",
        'green': "0;32m",
        'yellow': "0;33m",
        'blue': "0;34m",
        'purple': "0;35m",
        'cyan': "0;36m",
        'white': "0;37m",
        'end': "0m",
    }

    def __getattr__(self, name):
        def handlerFunction(*args, **kwargs):
            return self.START + self.FORMAT['Regular'] + ";" + self.COLOR[name.lower()]

        return handlerFunction(name=name)
    # ----------------------------------------------------------------------


# Template

class Template_mixin(object):
    bc = bcolors()

    STATUS = {
        0: bc.GREEN + 'pass' + bc.END,
        1: bc.PURPLE + 'fail' + bc.END,
        2: bc.RED + 'error' + bc.END,
    }

    # ------------------------------------------------------------------------
    # Report
    #

    REPORT_TEST_WITH_OUTPUT_TMPL = r"""
   %(desc)s

        %(status)s

        %(script)s

"""  # variables: (tid, Class, style, desc, status)

    REPORT_TEST_NO_OUTPUT_TMPL = r"""
    %(desc)s
    %(status)s
"""  # variables: (tid, Class, style, desc, status)

    REPORT_TEST_OUTPUT_TMPL = r"""
%(output)s
"""  # variables: (id, output)


# -------------------- The end of the Template class -------------------


TestResult = unittest.TestResult


class _TestResult(TestResult):
    # note: _TestResult is a pure representation of results.
    # It lacks the output and reporting ability compares to unittest._TextTestResult.

    def __init__(self, verbosity=1):
        TestResult.__init__(self)
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.verbosity = verbosity

        # result is a list of result in 4 tuple
        # (
        #   result code (0: success; 1: fail; 2: error),
        #   TestCase object,
        #   Test output (byte string),
        #   stack trace,
        # )
        self.result = []
        #
        self.outputBuffer = StringIO()

    def startTest(self, test):
        TestResult.startTest(self, test)
        # just one buffer for both stdout and stderr
        self.outputBuffer = StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        """
        Disconnect output redirection and return buffer.
        Safe to call multiple times.
        """
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()

    def stopTest(self, test):
        # Usually one of addSuccess, addError or addFailure would have been called.
        # But there are some path in unittest that would bypass this.
        # We must disconnect stdout in stopTest(), which is guaranteed to be called.
        self.complete_output()

    def addSubTest(self, test, subtest, err):
        # Subtest:
        #  Needs index / enumerate labeled i, if i==0 that means its the last test
        #  The parameters are displayed in brackets

        def dummy_id(self):
            params = dict(subtest.params.items()) # pyright: ignore[reportAttributeAccessIssue]
            index = params.pop("i", 1)
            if index == 0:
                start = "└"
            else:
                start = "├"
            return f" {start}─ [{','.join([f'{v}' for k,v in params.items()])}]"

        # Replace the id function, which is what is used to display it in the table view
        subtest.id = types.MethodType(dummy_id, subtest)

        # Add a SubTest
        if Config.SINGLE_LINE_STACK:
            if err:
                clean_msg = str(err[1]).replace("\n", " ")
                new_err = err[1].__class__(str(clean_msg)) # type: ignore
                err = (err[0], new_err, None)

        if err is None:
            self.addSuccess(subtest)
        elif issubclass(err[0], AssertionError): # type: ignore
            self.addFailure(subtest, err) # type: ignore
        else:
            self.addError(subtest, err) # type: ignore

    def addSuccess(self, test):
        self.success_count += 1
        TestResult.addSuccess(self, test)
        output = self.complete_output()
        self.result.append((0, test, output, ''))
        if self.verbosity > 1:
            sys.stderr.write('ok ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            if Config.PRINT_LIVE:
                sys.stderr.write('.')
                sys.stderr.flush()

    def addError(self, test, err):
        self.error_count += 1

        # Remove the traceback object to have single line error
        if Config.SINGLE_LINE_STACK:
            clean_msg = str(err[1]).replace("\n", " ")
            new_err = err[1].__class__(clean_msg) # type: ignore
            err = (err[0], new_err, None)

        TestResult.addError(self, test, err) # type: ignore
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((2, test, output, _exc_str))
        if self.verbosity > 1:
            sys.stderr.write('E  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            if Config.PRINT_LIVE:
                sys.stderr.write('E')
                sys.stderr.flush()

    def addFailure(self, test, err):
        self.failure_count += 1

        # Remove traceback to have single line failure
        if Config.SINGLE_LINE_STACK:
            # Replaces old exception with new instance with updated error message that is a single line
            new_err = err[1].__class__(str(err[1]).replace("\n", "")) # type: ignore
            err = (err[0], new_err, None)

        TestResult.addFailure(self, test, err) # type: ignore
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((1, test, output, _exc_str))
        if self.verbosity > 1:
            sys.stderr.write('F  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            if Config.PRINT_LIVE:
                sys.stderr.write('F')
                sys.stderr.flush()


class TestRunner(Template_mixin):
    """
    """

    def __init__(self, stream=sys.stdout, verbosity=1, title=None, description=None):
        self.stream = stream
        self.verbosity = verbosity
        if title is None:
            self.title = 'Unit Test Report'
        else:
            self.title = title
        if description is None:
            self.description = ''
        else:
            self.description = description

        self.startTime = datetime.datetime.now()
        self.bc = bcolors()

    def run(self, test):
        "Run the given test case or test suite."
        result = _TestResult(self.verbosity)
        test(result)
        self.stopTime = datetime.datetime.now()
        self.generateReport(test, result)
        return result

    def sortResult(self, result_list):
        rmap = {}
        classes = []
        seen_parents = set()

        for n, test, output, error in result_list:
            is_subtest = hasattr(test, "test_case")
            parent_test = getattr(test, "test_case", test)
            test_class = parent_test.__class__

            # Note procedually generated methods
            if "%generated" in (test._testMethodDoc or ""):
                test._testMethodName = "*" + test._testMethodName

            if test_class not in rmap:
                rmap[test_class] = []
                classes.append(test_class)
            
            # Ensure parent test is added once (either as standalone or before subtests)
            if is_subtest:
                if parent_test not in seen_parents:
                    parent_result = next(
                    ((pn, pt, po, pe) for pn, pt, po, pe in result_list if pt == parent_test),
                    (n, parent_test, "", "")  # fallback in case not found
                    )
                    rmap[test_class].append(parent_result)
                    seen_parents.add(parent_test)
                rmap[test_class].append((n, test, output, error))
            else:
                if test not in seen_parents:
                    rmap[test_class].append((n, test, output, error))
                    seen_parents.add(test)

        return [(cls, rmap[cls]) for cls in classes]

    def getReportAttributes(self, result):
        """
        Return report attributes as a list of (name, value).
        Override this to add custom attributes.
        """
        startTime = str(self.startTime)[:19]
        duration = str(self.stopTime - self.startTime)
        status = []
        padding = 4 * ' '
        status.append(padding + self.bc.GREEN + 'Pass   ' + self.bc.END + ' : %s\n' % result.success_count)
        status.append(padding + self.bc.PURPLE + 'Failure' + self.bc.END + ' : %s\n' % result.failure_count)
        status.append(padding + self.bc.RED + 'Error  ' + self.bc.END + ' : %s\n' % result.error_count)

        if status:
            status = '\n' + ''.join(status)
        else:
            status = 'none'
        return [
            ('Start Time', startTime),
            ('Duration', duration),
            ('Status', status),
        ]

    def generateReport(self, test, result):
        time.sleep(1)
        report_attrs = self.getReportAttributes(result)
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        output = "\n" + self.title + "\n" + \
                 heading + \
                 report
        try:
            self.stream.write(output.encode('utf8')) # type: ignore
            self.stream.flush()
        except TypeError:
            self.stream = io.TextIOWrapper(self.stream.buffer, encoding='utf-8')
            self.stream.write(output)
            self.stream.flush()

    def _generate_heading(self, report_attrs):
        a_lines = []
        # Add the time it took for the tests
        for name, value in report_attrs:
            line = self.bc.CYAN + name + ": " + self.bc.END + value + "\n"
        a_lines.append(line) # type: ignore

        # Generate description
        class DefaultDict(dict):
            def __missing__(self, key):
                return '{' + key + '}'

        time_elapsed = (self.stopTime - self.startTime)
        self.description = self.description.format_map({'humanized_time': humanize.naturaldelta(time_elapsed), 'time': time_elapsed})
        
        self.description = self.description.lstrip(" \n")
        if "\n" in self.description:
            description_lines = self.description.split("\n")
        else:
            description_lines = [self.description]
        self.description = '\n  ' + '\n  '.join(description_lines)
        
        heading = ''.join(a_lines) + \
                  self.bc.CYAN + "Description:" + self.bc.END + self.description + "\n"
        return heading

    def _generate_report(self, result):
        rows = []
        sortedResult = self.sortResult(result.result)
        padding = 4 * ' '
        table = Table(padding=padding)
        table.addTitles(["Test group/Test case", "Count", "Pass ", "Fail ", "Error"])
        tests = ''

        for cid, (testClass, classResults) in enumerate(sortedResult):  # Iterate over the test cases
            classTable = Table(padding=2 * padding)
            classTable.addTitles(["Test Name", "Stack", "Status"])
            # subtotal for a class
            np = nf = ne = 0
            for n, _t, _o, _e in classResults:
                if n == 0:
                    np += 1
                elif n == 1:
                    nf += 1
                else:
                    ne += 1

            # format class description
            if testClass.__module__ == "__main__":
                name = testClass.__name__
            else:
                name = "%s" % testClass.__name__

            # Color classname header blue
            tests += "\n" + padding + self.bc.CYAN + name + self.bc.END + "\n"
            
            # style = ne > 0 and 'errorClass' or nf > 0 and 'failClass' or 'passClass',
            table.addRow([name, str(np + nf + ne), str(np), str(nf), str(ne)])
            for tid, (n, test, output, error) in enumerate(classResults):  # Iterate over the unit tests
                classTable.addRow(self._generate_report_test(cid, tid, n, test, output, error))
            
            # Add Description right under that thang
            doc = testClass.__doc__ or ""
            if doc:
                doc = doc.strip(" \n")
                if "\n" in doc:
                    doc_lines = doc.split("\n")
                else:
                    doc_lines = [doc]
                doc_lines = [doc_line.strip(" \n") for doc_line in doc_lines]
                doc = ('\n' + padding * 2).join(doc_lines)
                tests += padding * 2 + doc + '\n'

            tests += str(classTable)

        table.addRow(
            ["Total", str(result.success_count + result.failure_count + result.error_count), str(result.success_count),
             str(result.failure_count), str(result.error_count)])
        report = self.bc.CYAN + "Summary: " + self.bc.END + "\n" + str(table) + tests
        return report

    def _generate_report_test(self, cid, tid, n, test, output, error):
        has_output = bool(output or error)
        tid = (n == 0 and 'p' or 'f') + 't%s.%s' % (cid + 1, tid + 1)
        name = test.id().split('.')[-1]

        doc = test.shortDescription() or ""
        if "%ignore" in doc:
            doc = ""

        desc = doc and ('%s: %s' % (name, doc)) or name
        tmpl = has_output and self.REPORT_TEST_WITH_OUTPUT_TMPL or self.REPORT_TEST_NO_OUTPUT_TMPL
        if isinstance(output, str):
            try:
                uo = output.decode('latin-1') # type: ignore
            except AttributeError:
                uo = output
        else:
            uo = output
        if isinstance(error, str):
            try:
                ue = error.decode('latin-1') # type: ignore
            except AttributeError:
                ue = error
        else:
            ue = error

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            output=uo + ue,
        )
        row = [desc, script, self.STATUS[n]]
        return row

# Note: Reuse unittest.TestProgram to launch test. In the future we may
# build our own launcher to support more specific command line
# parameters like test title, CSS, etc.
class TestProgram(unittest.TestProgram):
    """
    A variation of the unittest.TestProgram. Please refer to the base
    class for command line parameters.
    """

    def runTests(self):
        if self.testRunner is None:
            self.testRunner = TestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)

main = TestProgram
