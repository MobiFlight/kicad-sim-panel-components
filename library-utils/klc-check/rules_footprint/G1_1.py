import re

from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """Only standard characters are used for naming libraries and components"""

    # Set of allowed chars. Some characters need to be escaped.
    ALLOWED_CHARS = r"a-zA-Z0-9_\-\.,\+"
    PATTERN = re.compile("^[" + ALLOWED_CHARS + "]+$")
    FORBIDDEN = re.compile("([^" + ALLOWED_CHARS + "])+")

    def check(self) -> bool:
        name = str(self.module.name).lower()
        if not self.PATTERN.match(name):
            self.error("Footprint name must contain only legal characters")
            illegal = re.findall(self.FORBIDDEN, name)
            self.errorExtra(
                "Illegal character(s) '{c}' found".format(c="', '".join(illegal))
            )
            return False
        return True

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        # Re-check line endings
        self.check()
