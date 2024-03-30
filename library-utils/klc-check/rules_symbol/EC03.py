from rules_symbol.rule import KLCRule, pinString


class Rule(KLCRule):
    """Pin names should only contain ascii chars"""

    def checkPinsAscii(self):
        evil_pins = [pin for pin in self.component.pins if not pin.name.isascii()]

        if evil_pins:
            pin_list = ", ".join(pinString(x) for x in evil_pins)
            contain = "contain" if len(evil_pins) > 1 else "contains"
            self.warning(f"{pin_list} {contain} non ascii chars")

        # This is a informal rule, not explicitly codified in KLC.
        # Thus, we never return an error.
        return False

    def check(self):
        # no need to check pins of a derived symbol
        if self.component.extends is not None:
            return False

        return self.checkPinsAscii()

    def fix(self):
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fix not supported")
