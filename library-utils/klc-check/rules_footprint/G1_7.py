import platform

from rulebase import checkLineEndings
from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """Library files must use Unix-style line endings (LF)"""

    def check(self) -> bool:

        # Only perform this check on linux systems (i.e. Travis)
        # Windows automatically checks out with CR+LF line endings
        if "linux" in platform.platform().lower() and not checkLineEndings(
            self.module.filename
        ):
            self.error("Incorrect line endings")
            self.errorExtra("Library files must use Unix-style line endings (LF)")
            return True

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.success("Line endings will be corrected on save")
