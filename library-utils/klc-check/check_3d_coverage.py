#!/usr/bin/env python3


import argparse
import os
import sys
from glob import glob  # enable windows wildcards

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

from kicad_mod import KicadMod
from print_color import PrintColor


class Config:
    def __init__(self):

        # Set default argument values
        self.verbose = False
        self.print_color = True
        self.summary = False
        self.library = []
        self.root = os.path.join("..", "..")
        self.parse_arguments()
        self.library_root = os.path.join(self.root, "kicad-footprints")
        self.model_root = os.path.join(self.root, "kicad-packages3D")

    def model_dir_path(self, library_name):
        return os.path.join(self.model_root, library_name + ".3dshapes")

    def footprint_dir_path(self, library_name):
        return os.path.join(self.library_root, library_name + ".pretty")

    def valid_library_names(self):
        if self.library:
            spec = self.library[0] + ".pretty"
        else:
            spec = "*.pretty"
        try:
            libs = sorted(
                [
                    os.path.splitext(os.path.basename(f))[0]
                    for f in glob(os.path.join(self.library_root, spec))
                    if os.path.isdir(f)
                ]
            )
        except FileNotFoundError:
            logger.fatal(
                "EXIT: problem reading from footprint root: {mr:s}".format(
                    mr=self.library_root
                )
            )
            sys.exit(1)
        if self.library:
            if not libs:
                logger.fatal(
                    "EXIT: footprint library not found: {fl:s}".format(
                        fl=self.library[0]
                    )
                )
                sys.exit(1)
        return libs

    def valid_models(self, library_name):
        if os.path.exists(self.model_dir_path(library_name)):
            try:
                return sorted(
                    [
                        model
                        for model in os.listdir(self.model_dir_path(library_name))
                        if model.endswith(("wrl", "step", "stp"))
                    ]
                )
            except FileNotFoundError:
                logger.error(
                    "- problem reading from 3D model directory: {d:s}".format(
                        d=self.model_dir_path(library_name)
                    )
                )
                return None
        else:
            logger.error(
                "- 3D model directory does not exist: {d:s}".format(
                    d=self.model_dir_path(library_name)
                )
            )
            return None

    def valid_footprints(self, library_name):
        dir_name = self.footprint_dir_path(library_name)
        try:
            return sorted(
                [
                    f
                    for f in os.listdir(dir_name)
                    if os.path.isfile(os.path.join(dir_name, f))
                    and f.endswith(".kicad_mod")
                ]
            )
        except FileNotFoundError:
            logger.fatal(
                "EXIT: problem reading from footprint directory: {d:s}".format(
                    d=dir_name
                )
            )
            sys.exit(1)

    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description=(
                "Checks that KiCad footprint files (.kicad_mod) reference 3D model"
                " files that exist in the KiCad library."
            )
        )
        parser.add_argument(
            "library",
            help=(
                "name of footprint library to check (e.g. Housings_SOIC) (default is"
                " all libraries)"
            ),
            type=str,
            nargs="*",
        )
        parser.add_argument(
            "-r",
            "--root",
            help="path to root KiCad folder (default is ../../)",
            type=str,
        )
        parser.add_argument(
            "-v", "--verbose", help="enable verbose output", action="store_true"
        )
        parser.add_argument(
            "--nocolor", help="do not use color text in output", action="store_true"
        )
        parser.add_argument("--summary", help="print summary only", action="store_true")
        args = parser.parse_args()
        if args.verbose:
            self.verbose = True
        if args.nocolor:
            self.print_color = False
        if args.library:
            self.library.append(str(args.library[0]))
        if args.root:
            self.root = str(args.root)
        if args.summary:
            self.summary = True


class Logger:
    def __init__(self, printer, verbose=False, summary=False):
        self.printer = printer
        self.verbose = verbose
        self.summary = summary
        self.warning_count = 0
        self.error_count = 0

    def status(self, s):
        self.printer.regular(s)

    def info(self, s):
        if self.verbose:
            self.printer.green(s)

    def warning(self, s):
        self.warning_count += 1
        if not self.summary:
            self.printer.yellow(s)

    def error(self, s):
        self.error_count += 1
        if not self.summary:
            self.printer.red(s)

    def fatal(self, s):
        self.printer.red(s)

    def reset(self):
        self.error_count = 0
        self.warning_count = 0


class LibraryChecker:
    def __init__(self):
        self.num_footprints = 0
        self.no_3dshape_folder = 0
        self.no_model_specified = 0
        self.model_not_found = 0
        self.model_found = 0
        self.invalid_model_path = 0
        self.unused_wrl = 0

    def parse_footprint(self, filename):

        # logger.info('Footprint: {f:s}'.format(f=os.path.basename(filename)))
        try:
            footprint = KicadMod(filename)
        except FileNotFoundError:
            logger.fatal(
                "EXIT: problem reading footprint file {fn:s}".format(fn=filename)
            )
            sys.exit(1)
        try:
            long_reference = footprint.models[0]["file"]
        except IndexError:
            if footprint.attribute == "virtual":
                # count as model found
                self.model_found += 1
            else:
                logger.warning(
                    "- No model file specified in {fp:s}".format(
                        fp=os.path.basename(filename)
                    )
                )
                self.no_model_specified += 1
            return None

        try:
            # Accept both forward and backward slash characters in path
            long_reference = "/".join(long_reference.split("\\"))
            return os.path.basename(long_reference)
        # TODO: determine, which specific problem could happen above ("ValueError" is just a guess)
        except ValueError:
            logger.warning("- Invalid model reference {f:s}".format(f=long_reference))
            self.invalid_model_path += 1
            return None

    def find_name_in_list(self, _list, name, case_sensitive=True):
        if case_sensitive:
            return name in _list
        else:
            name_lower = name.lower()
            for n in _list:
                if name_lower == n.lower():
                    return True
            return False

    def check_footprint_library(self, library_name):
        logger.reset()
        logger.status(
            "\r\nChecking {p:s} (contains {n:d} footprints)".format(
                p=library_name, n=len(config.valid_footprints(library_name))
            )
        )

        footprint_names = config.valid_footprints(library_name)
        models = config.valid_models(library_name)

        if not os.path.exists(config.model_dir_path(library_name)):
            self.no_3dshape_folder += 1

        if models:
            unused = models[:]

        for footprint in footprint_names:
            self.num_footprints += 1
            model_ref = self.parse_footprint(
                os.path.join(config.footprint_dir_path(library_name), footprint)
            )
            if model_ref:
                if models:
                    if self.find_name_in_list(models, model_ref, True):
                        self.model_found += 1
                        logger.info("Found 3D model {model:s}".format(model=model_ref))
                        if model_ref in unused:
                            unused.remove(model_ref)
                    else:
                        self.model_not_found += 1
                        if self.find_name_in_list(models, model_ref, False):
                            logger.warning(
                                "- 3D model not found {model:s} in {fp:s} (wrong case)".format(
                                    model=model_ref, fp=footprint
                                )
                            )
                        else:
                            logger.warning(
                                "- 3D model not found {model:s} in {fp:s}".format(
                                    model=model_ref, fp=footprint
                                )
                            )
                else:
                    self.model_not_found += 1

        footprint_warnings = logger.warning_count
        unused_models = []

        if models:
            unused_models = [model for model in unused if model.endswith(".wrl")]
            self.unused_wrl += len(unused_models)
            for model in unused_models:
                logger.warning(
                    "- Unused .wrl model {lib:s}.3dshapes/{m:s}".format(
                        lib=library_name, m=model
                    )
                )

        if logger.warning_count > 0:
            logger.status("- {n:d} footprint warnings".format(n=footprint_warnings))

        if logger.error_count > 0:
            logger.status("- {n:d} footprint errors".format(n=logger.error_count))

        if unused_models:
            logger.status("- {n:d} unused model warnings".format(n=len(unused_models)))

    def check_libraries(self):

        lib_names = config.valid_library_names()
        for library in lib_names:
            self.check_footprint_library(library)

        logger.status("")
        logger.status("-" * 80)
        logger.status("Summary")
        logger.status("")
        logger.status("Libraries scanned       {}".format(len(lib_names)))
        logger.status("Footprints              {}".format(self.num_footprints))
        logger.status("No model file specified {}".format(self.no_model_specified))
        logger.status("3D Model not found      {}".format(self.model_not_found))
        logger.status("No 3D Model folder      {}".format(self.no_3dshape_folder))
        logger.status("3D Model found          {}".format(self.model_found))
        logger.status("Unused wrl file         {}".format(self.unused_wrl))


# main program

if __name__ == "__main__":
    config = Config()

    printer = PrintColor(use_color=config.print_color)
    logger = Logger(printer, config.verbose, config.summary)

    logger.info("Library root: {r:s}".format(r=config.library_root))
    logger.info("Model root:  {r:s}".format(r=config.model_root))

    checker = LibraryChecker()
    checker.check_libraries()
