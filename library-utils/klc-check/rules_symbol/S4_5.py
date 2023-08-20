from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Pins not connected on the footprint may be omitted from the symbol"""

    def checkMissingPins(self) -> bool:
        int_pins = []
        for pin in self.component.pins:
            try:
                int_pins.append(int(pin.number))
            except ValueError:
                pass

        if not int_pins:
            return False

        missing_pins = []
        for i in range(1, max(int_pins) + 1):
            if i not in int_pins:
                missing_pins.append(i)
        if missing_pins:
            self.warning(
                "Pin{s} {n} {v} missing.".format(
                    s="s" if len(missing_pins) > 1 else "",
                    n=", ".join(str(x) for x in missing_pins),
                    v="are" if len(missing_pins) > 1 else "is",
                )
            )
        return False

    def check(self) -> bool:
        # no need to check pins on a derived symbols
        if self.component.extends is not None:
            return False

        return self.checkMissingPins()

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fix not supported")
