#!/usr/bin/env python3
"""
This file compares two .lib files and generates a list of deleted / added / updated components.
This is to be used to compare an updated library file with a previous version to determine which
components have been changed.
"""

import argparse
import difflib
import filecmp
import fnmatch
import os
import sys
from glob import glob


env_verbose_diff_limit = os.environ.get("VERBOSE_DIFF_LIMIT", "1048576")
VERBOSE_DIFF_LIMIT = int(env_verbose_diff_limit) \
    if env_verbose_diff_limit.isdigit() else 1024 * 1024  # 1MB

# Path to common directory
common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)

if common not in sys.path:
    sys.path.insert(0, common)

import check_symbol
from kicad_sym import KicadLibrary
from print_color import PrintColor
from rulebase import Verbosity
from sexpr import build_sexp, format_sexp


def ExitError(msg):
    print(msg)
    sys.exit(-1)


def print_colored_diff(printer: PrintColor, lines: list[str]):
    for line in lines:
        # Strip leading spaces because in some cases diff is indented.
        # This may lead to some false positives but it's a tradeoff.
        t = line.lstrip()
        if t.startswith("+"):
            printer.green(line)
        elif t.startswith("-"):
            printer.red(line)
        elif t.startswith("?"):
            printer.yellow(line)
        else:
            printer.regular(line)


parser = argparse.ArgumentParser(
    description="Compare two .kicad_sym files to determine which symbols have changed"
)
parser.add_argument(
    "--new", help="New (updated) .lib file(s), or folder of .kicad_sym files", nargs="+"
)
parser.add_argument(
    "--old",
    help="Old (original) .lib file(s), or folder of .kicad_sym files for comparison",
    nargs="+",
)
parser.add_argument(
    "-v", "--verbose", help="Enable extra verbose output", action="store_true"
)
parser.add_argument(
    "--check", help="Perform KLC check on updated/added components", action="store_true"
)
parser.add_argument(
    "--nocolor", help="Does not use colors to show the output", action="store_true"
)
parser.add_argument(
    "--design-breaking-changes",
    help=(
        "Checks if there have been changes made that would break existing designs using"
        " a particular symbol."
    ),
    action="store_true",
)
parser.add_argument(
    "--check-derived",
    help="Do not only check symbols but also derived symbols.",
    action="store_true",
)
parser.add_argument(
    "--shownochanges", help="Show libraries that have not changed", action="store_true"
)
parser.add_argument(
    "--exclude",
    help=(
        "Exclude a particular rule (or rules) to check against. Use comma separated"
        ' values to select multiple rules. e.g. "-e S3.1,EC02"'
    ),
)
parser.add_argument(
    "--footprint_directory",
    help=(
        "Path to footprint libraries (.pretty dirs). Specify with e.g."
        ' "~/kicad/footprints/"'
    ),
)

(args, extra) = parser.parse_known_args()
printer = PrintColor(use_color=not args.nocolor)

if not args.new:
    ExitError("New file(s) not supplied")
    # TODO print help

if not args.old:
    ExitError("Original file(s) not supplied")
    # TODO print help


def build_library_dict(filelist):
    """
    Take a list of files, expand globs if required. Build a dict in for form {'libname': filename}
    """
    libs = {}
    for lib in filelist:
        flibs = glob(lib)

        for lib_path in flibs:
            if os.path.isdir(lib_path):
                for root, dirnames, filenames in os.walk(lib_path):
                    for filename in fnmatch.filter(filenames, "*.kicad_sym"):
                        libs[os.path.basename(filename)] = os.path.abspath(
                            os.path.join(root, filename)
                        )

            elif lib_path.endswith(".kicad_sym") and os.path.exists(lib_path):
                libs[os.path.basename(lib_path)] = os.path.abspath(lib_path)
    return libs


# prepare variables
new_libs = build_library_dict(args.new)
old_libs = build_library_dict(args.old)
errors = 0
design_breaking_changes = 0

# create a SymbolCheck instance
# add footprints dir if possible
sym_check = check_symbol.SymbolCheck(
    None, args.exclude, Verbosity(2), args.footprint_directory,
    False if args.nocolor else True, silent=True
)

# iterate over all new libraries
for lib_name in new_libs:
    lib_path = new_libs[lib_name]
    new_lib = KicadLibrary.from_file(lib_path)

    # If library checksums match, we can skip entire library check
    if lib_name in old_libs:
        if filecmp.cmp(old_libs[lib_name], lib_path):
            if args.verbose and args.shownochanges:
                printer.yellow("No changes to library '{lib}'".format(lib=lib_name))
            continue

    # New library has been created!
    if lib_name not in old_libs:
        if args.verbose:
            printer.light_green("Created library '{lib}'".format(lib=lib_name))

        # Check all the components!
        for sym in new_lib.symbols:
            if args.check:
                (ec, wc) = sym_check.do_rulecheck(sym)
                if ec != 0:
                    errors += 1
        continue

    # Library has been updated - check each component to see if it has been changed
    old_lib_path = old_libs[lib_name]
    old_lib = KicadLibrary.from_file(old_lib_path)

    new_sym = {}
    old_sym = {}
    for sym in new_lib.symbols:
        if not args.check_derived and sym.extends:
            continue
        new_sym[sym.name] = sym

    for sym in old_lib.symbols:
        if not args.check_derived and sym.extends:
            continue
        old_sym[sym.name] = sym

    for symname in new_sym:
        # Component is 'new' (not in old library)
        derived_sym_info = ""
        if new_sym[symname].extends:
            derived_sym_info = " derived from {}".format(new_sym[symname].extends)

        if symname not in old_sym:
            if args.verbose:
                printer.light_green(f"New '{lib_name}:{symname}'{derived_sym_info}")

            if args.check:
                # only check new components
                (ec, wc) = sym_check.check_library(lib_path, component=symname)
                if ec != 0:
                    errors += 1

            continue

        if new_sym[symname].extends != old_sym[symname].extends and args.verbose:
            printer.white(
                "Changed derived state of '{lib}:{name}'".format(
                    lib=lib_name, name=symname
                )
            )

        if new_sym[symname] != old_sym[symname]:
            if args.verbose:
                printer.yellow(f"Changed '{lib_name}:{symname}'{derived_sym_info}")

                printer.start_fold_section("symbol_diff", "Show s-expr diff")

                new_sexpr = format_sexp(build_sexp(new_sym[symname].get_sexpr())).splitlines()
                old_sexpr = format_sexp(build_sexp(old_sym[symname].get_sexpr())).splitlines()
                difflines = [line.rstrip() for line in difflib.unified_diff(old_sexpr, new_sexpr)]

                print_colored_diff(printer, difflines)

                printer.end_fold_section("symbol_diff")

            if args.design_breaking_changes:
                pins_moved = 0
                nc_pins_moved = 0
                pins_missing = 0
                nc_pins_missing = 0
                for pin_old in old_sym[symname].pins:
                    pin_new = new_sym[symname].get_pin_by_number(pin_old.num)
                    if pin_new is None:
                        if pin_old.etype == "no_connect":
                            nc_pins_missing += 1
                        else:
                            pins_missing += 1
                        continue

                    if pin_old.posx != pin_new.posx or pin_old.posy != pin_new.posy:
                        if (
                            pin_old.etype == "no_connect"
                            and pin_new.etype == "no_connect"
                        ):
                            nc_pins_moved += 1
                        else:
                            pins_moved += 1

                if pins_moved > 0 or pins_missing > 0:
                    design_breaking_changes += 1
                    printer.light_purple(
                        "Pins have been moved, renumbered or removed in symbol"
                        f" '{lib_name}:{symname}'{derived_sym_info}"
                    )
                elif nc_pins_moved > 0 or nc_pins_missing > 0:
                    design_breaking_changes += 1
                    printer.purple(
                        "Normal pins ok but NC pins have been moved, renumbered or"
                        f" removed in symbol '{lib_name}:{symname}'{derived_sym_info}"
                    )

            if args.check:
                (ec, wc) = sym_check.do_rulecheck(new_sym[symname])
                if ec != 0:
                    errors += 1

    for symname in old_sym:
        # Component has been deleted from library
        if symname not in new_sym:
            derived_sym_info = ""
            if old_sym[symname].extends:
                derived_sym_info = " was an derived from {}".format(
                    old_sym[symname].extends
                )

            if args.verbose:
                printer.red(f"Removed '{lib_name}:{symname}'{derived_sym_info}")
            if args.design_breaking_changes:
                design_breaking_changes += 1

# Check if an entire lib has been deleted?
for lib_name in old_libs:
    if lib_name not in new_libs:
        if args.verbose:
            printer.red("Removed library '{lib}'".format(lib=lib_name))
        if args.design_breaking_changes:
            design_breaking_changes += 1

# Return the number of errors found ( zero if --check is not set )
sys.exit(errors + design_breaking_changes)
