#!/usr/bin/env python3

import argparse
import os
import queue
import re
import sys
import time
import traceback
from functools import lru_cache
from glob import glob  # enable windows wildcards
from multiprocessing import JoinableQueue, Lock, Process, Queue
from typing import List, Optional, Tuple

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

from kicad_sym import KicadFileFormatError, KicadLibrary
from print_color import PrintColor
from rulebase import Verbosity, logError
from rules_symbol import get_all_symbol_rules
from rules_symbol.rule import KLCRule


class SymbolCheck:
    def __init__(
        self,
        selected_rules: Optional[List[str]] = None,
        excluded_rules: Optional[List[str]] = None,
        verbosity: Verbosity = Verbosity.NONE,
        footprints=None,
        use_color: bool = True,
        no_warnings: bool = False,
        silent: bool = False,
        log: bool = False,
    ):
        self.footprints = footprints
        self.printer = PrintColor(use_color=use_color)
        self.verbosity: Verbosity = verbosity
        self.metrics: List[str] = []
        self.no_warnings: bool = no_warnings
        self.log: bool = log
        self.silent: bool = silent
        self.error_count: int = 0
        self.warning_count: int = 0

        # build a list of rules to work with
        self.rules: List[KLCRule] = []

        for rule_name, rule in get_all_symbol_rules().items():
            if selected_rules is None or rule_name in selected_rules:
                if excluded_rules is not None and rule_name in excluded_rules:
                    pass
                else:
                    self.rules.append(rule.Rule)

    def do_unittest(self, symbol) -> Tuple[int, int]:
        error_count = 0
        m = re.match(r"(\w+)__(.+)__(.+)", symbol.name)
        if not m:
            self.printer.red("Test '{sym}' could not be parsed".format(sym=symbol.name))
            return (1, 0)
        unittest_result = m.group(1)
        unittest_rule = m.group(2)
        unittest_descrp = m.group(3)  # noqa: F841
        for rule in self.rules:
            rule.footprints_dir = self.footprints
            rule = rule(symbol)
            if unittest_rule == rule.name:
                rule.check()
                if unittest_result == "Fail" and rule.errorCount == 0:
                    self.printer.red("Test '{sym}' failed".format(sym=symbol.name))
                    error_count += 1
                    continue
                if unittest_result == "Warn" and rule.warningCount() == 0:
                    self.printer.red("Test '{sym}' failed".format(sym=symbol.name))
                    error_count += 1
                    continue
                if unittest_result == "Pass" and (
                    rule.warningCount() != 0 or rule.errorCount != 0
                ):
                    self.printer.red("Test '{sym}' failed".format(sym=symbol.name))
                    error_count += 1
                    continue
                self.printer.green("Test '{sym}' passed".format(sym=symbol.name))

            else:
                continue
        return (error_count, 0)

    def do_rulecheck(self, symbol) -> Tuple[int, int]:
        symbol_error_count = 0
        symbol_warning_count = 0
        first = True
        for rule in self.rules:
            rule.footprints_dir = self.footprints
            rule = rule(symbol)

            if self.verbosity.value > Verbosity.HIGH.value:
                self.printer.white("Checking rule " + rule.name)
            rule.check()

            if self.no_warnings and not rule.hasErrors():
                continue

            if rule.hasOutput():
                if first:
                    self.printer.green(
                        "Checking symbol '{lib}:{sym}':".format(
                            lib=symbol.libname, sym=symbol.name
                        )
                    )
                    first = False

                self.printer.yellow(
                    "Violating " + rule.name + " - " + rule.url, indentation=2
                )
                rule.processOutput(self.printer, self.verbosity, self.silent)

            if rule.hasErrors():
                if self.log:
                    logError(self.log, rule.name, symbol.libname, symbol.name)

            # increment the number of violations
            symbol_error_count += rule.errorCount
            symbol_warning_count += rule.warningCount()

        # No messages?
        if first:
            if not self.silent:
                self.printer.green(
                    "Checking symbol '{lib}:{sym}':".format(
                        lib=symbol.libname, sym=symbol.name
                    )
                )

        # done checking the symbol
        # count errors and update metrics
        self.metrics.append(
            "{l}.{p}.warnings {n}".format(
                l=symbol.libname, p=symbol.name, n=symbol_warning_count
            )
        )
        self.metrics.append(
            "{l}.{p}.errors {n}".format(
                l=symbol.libname, p=symbol.name, n=symbol_error_count
            )
        )
        return (symbol_error_count, symbol_warning_count)

    @lru_cache(maxsize=None)
    def _load_library(self, filename):
        return KicadLibrary.from_file(filename)

    def check_library(
        self, filename: str, component=None, pattern=None, is_unittest: bool = False
    ) -> Tuple[int, int]:
        error_count = 0
        warning_count = 0
        libname = ""
        if not os.path.exists(filename):
            self.printer.red("File does not exist: %s" % filename)
            return (1, 0)

        if not filename.endswith(".kicad_sym"):
            self.printer.red("File is not a .kicad_sym : %s" % filename)
            return (1, 0)

        try:
            library = self._load_library(filename)
        except KicadFileFormatError as e:
            self.printer.red("Could not parse library: %s. (%s)" % (filename, e))
            if self.verbosity:
                self.printer.red("Error: " + str(e))
                traceback.print_exc()
            return (1, 0)

        for symbol in library.symbols:
            if component:
                if component.lower() != symbol.name.lower():
                    continue

            if pattern:
                if not re.search(pattern, symbol.name, flags=re.IGNORECASE):
                    continue

            # check which kind of tests we want to run
            if is_unittest:
                (ec, wc) = self.do_unittest(symbol)
            else:
                (ec, wc) = self.do_rulecheck(symbol)

            error_count += ec
            warning_count += wc
            libname = symbol.libname

        # done checking the lib
        self.metrics.append("{lib}.total_errors {n}".format(lib=libname, n=error_count))
        self.metrics.append(
            "{lib}.total_warnings {n}".format(lib=libname, n=warning_count)
        )
        self.error_count += error_count
        self.warning_count += warning_count
        return (error_count, warning_count)


def worker(
    inp,
    outp,
    lock,
    selected_rules,
    excluded_rules,
    verbosity: Verbosity,
    footprints,
    args,
    i=0,
):
    # have one instance of SymbolCheck per worker
    c = SymbolCheck(
        selected_rules,
        excluded_rules,
        verbosity,
        footprints,
        not args.nocolor,
        no_warnings=args.nowarnings,
        silent=args.silent,
        log=args.log,
    )
    c.printer.buffered = True

    while True:
        try:
            fn = inp.get(block=False)
            # run the check on this file
            c.check_library(fn, args.component, args.pattern, args.unittest)
            # print the console output, all at once while we have the lock
            lock.acquire()
            c.printer.flush()
            lock.release()
            # signal that we are done with this item
            inp.task_done()
        except queue.Empty:
            break

    # output all the metrics at once
    for line in c.metrics:
        outp.put("{},{}".format(i, line))
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Checks KiCad library files (.kicad_sym) against KiCad Library Convention"
            " (KLC) rules. You can find the KLC at https://kicad.org/libraries/klc/"
        )
    )
    parser.add_argument("kicad_sym_files", nargs="+")
    parser.add_argument(
        "-c", "--component", help="check only a specific component", action="store"
    )
    parser.add_argument(
        "-p",
        "--pattern",
        help="Check multiple components by matching a regular expression",
        action="store",
    )
    parser.add_argument(
        "-r",
        "--rule",
        help=(
            "Select a particular rule (or rules) to check against (default = all"
            ' rules). Use comma separated values to select multiple rules. e.g. "-r'
            ' S3.1,EC02"'
        ),
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help=(
            "Exclude a particular rule (or rules) to check against. Use comma separated"
            ' values to select multiple rules. e.g. "-e S3.1,EC02"'
        ),
    )
    # currently there is no write support for a kicad symbol
    #    parser.add_argument('--fix', help='fix the violations if possible', action='store_true')
    parser.add_argument(
        "--nocolor", help="does not use colors to show the output", action="store_true"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help=(
            "Enable verbose output. -v shows brief information, -vv shows complete"
            " information"
        ),
        action="count",
    )
    parser.add_argument(
        "-s",
        "--silent",
        help="skip output for symbols passing all checks",
        action="store_true",
    )
    parser.add_argument(
        "-l", "--log", help="Path to JSON file to log error information"
    )
    parser.add_argument(
        "-w",
        "--nowarnings",
        help="Hide warnings (only show errors)",
        action="store_true",
    )
    parser.add_argument(
        "-m", "--metrics", help="generate a metrics.txt file", action="store_true"
    )
    parser.add_argument(
        "-u",
        "--unittest",
        help="unit test mode (to be used with test-symbols)",
        action="store_true",
    )
    parser.add_argument("-j", "--multiprocess", help="use parallel processing")
    parser.add_argument(
        "--footprints",
        help=(
            "Path to footprint libraries (.pretty dirs). Specify with e.g."
            ' "~/kicad/footprints/"'
        ),
    )
    args = parser.parse_args()

    #
    if args.rule:
        selected_rules = args.rule.split(",")
    else:
        selected_rules = None

    if args.exclude:
        excluded_rules = args.exclude.split(",")
    else:
        excluded_rules = None

    # Set verbosity globally
    verbosity = Verbosity.NONE
    if args.verbose:
        verbosity = Verbosity(args.verbose)
    KLCRule.verbosity = verbosity

    # check if a footprints dir was passed
    footprints = args.footprints

    # populate list of files
    files = []
    for f in args.kicad_sym_files:
        files += glob(f)

    if not files:
        print("File argument invalid: {f}".format(f=args.kicad_sym_files))
        sys.exit(1)

    # re work files list to include size
    for i in range(len(files)):
        files[i] = (files[i], os.path.getsize(files[i]))
    # Sort list by file size, largest on top
    # the idea is to further speed up multiprocessing by working on the bigger items first
    if not args.unittest:
        files.sort(key=lambda filename: filename[1], reverse=True)

    # Create queues for multiprocessing
    task_queue = JoinableQueue()
    out_queue = Queue()

    for (filename, size) in files:
        task_queue.put(filename)

    jobs = []
    job_output = {}

    # create the workers
    lock = Lock()
    for i in range(int(args.multiprocess) if args.multiprocess else 1):
        p = Process(
            target=worker,
            args=(
                task_queue,
                out_queue,
                lock,
                selected_rules,
                excluded_rules,
                verbosity,
                footprints,
                args,
                i,
            ),
        )
        jobs.append(p)
        p.start()
        job_output[str(i)] = []

    # wait for all workers to finish
    while jobs:
        for p in jobs:
            while True:
                try:
                    identifier, line = out_queue.get(block=False).split(",")
                    job_output[identifier].append(line)
                except queue.Empty:
                    break
            if not p.is_alive():
                jobs.remove(p)

    out_queue.put("STOP")

    time.sleep(1)

    # done checking all files
    error_count = 0
    if args.metrics or args.unittest:
        metrics_file = open("metrics.txt", "a+")

        for key in job_output:
            for line in job_output[key]:
                metrics_file.write(line + "\n")
                if ".total_errors" in line:
                    error_count += int(line.split()[-1])

        metrics_file.close()
    out_queue.close()
    sys.exit(0 if error_count == 0 else -1)
