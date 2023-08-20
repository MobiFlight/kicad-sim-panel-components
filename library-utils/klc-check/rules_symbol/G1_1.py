import string

from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Only standard characters are used for naming libraries and components"""

    def check(self) -> bool:

        allowed = string.digits + string.ascii_letters + "_-.+,"

        name = self.component.name.lower()

        illegal = ""

        for i, c in enumerate(name):
            if c in allowed:
                continue

            # Some symbols have a special character at the start
            if i == 0:
                if c in ["~", "#"]:
                    continue

            # Illegal character found!
            illegal += c

        if illegal:
            self.error("Symbol name must contain only legal characters")
            self.errorExtra(
                "Name '{n}' contains illegal characters '{i}'".format(
                    n=self.component.name, i=illegal
                )
            )
            return True
        else:
            # No errors!
            return False

    def fix(self) -> None:
        self.recheck()
