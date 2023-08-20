import platform

from kicad_sym import KicadSymbol
from rulebase import checkLineEndings
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Library files must use Unix-style line endings (LF)"""

    lib_error = False

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.lib_error: bool = False

    def check(self) -> bool:
        # Only perform this check on linux systems (i.e. Travis)
        # Windows automatically checks out with CR+LF line endings
        if "linux" in platform.platform().lower():
            if not checkLineEndings(self.component.filename):
                self.lib_error = True
                self.error("Incorrect line endings (.kicad_sym)")
                self.errorExtra("Library files must use Unix-style line endings (LF)")

            if self.lib_error:
                return True

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.success("Line endings will be corrected on save")
