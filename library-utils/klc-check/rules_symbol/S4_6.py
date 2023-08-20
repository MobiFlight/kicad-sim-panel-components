import re
from typing import List

from kicad_sym import KicadSymbol, Pin
from rules_symbol.rule import KLCRule, pinString


class Rule(KLCRule):
    """Hidden pins"""

    # No-connect pins should be "N"
    NC_PINS = ["^nc$", "^dnc$", r"^n\.c\.$"]

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.invisible_errors: List[Pin] = []
        self.power_invisible_errors: List[Pin] = []
        self.type_errors: List[Pin] = []

    # check if a pin name fits within a list of possible pins (using regex testing)
    def test(self, pinName: str, nameList: List[str]) -> bool:
        for name in nameList:
            if re.search(name, pinName, flags=re.IGNORECASE) is not None:
                return True

        return False

    def checkPins(self, pins: List[Pin], is_power: bool) -> bool:
        self.invisible_errors = []
        self.power_invisible_errors = []
        self.type_errors = []

        for pin in pins:
            name = pin.name.lower()
            etype = pin.etype

            # Check NC pins
            if self.test(name, self.NC_PINS) or etype == "no_connect":
                # NC pins should be of type no_connect
                if not etype == "no_connect":  # Not set to NC
                    self.type_errors.append(pin)

                # NC pins should be invisible
                if not pin.is_hidden:
                    self.invisible_errors.append(pin)

            # For non-power-symbols: check if power-pins are invisible
            if not is_power and etype == "power_in" and pin.is_hidden:
                self.power_invisible_errors.append(pin)

        if self.type_errors:
            self.error("NC pins are not correct pin-type:")

            for pin in self.type_errors:
                self.errorExtra(
                    "{pin} should be of type NOT CONNECTED, but is of type {pintype}".format(
                        pin=pinString(pin), pintype=pin.etype
                    )
                )

        if self.invisible_errors:
            self.warning("NC pins are VISIBLE (should be INVISIBLE):")

            for pin in self.invisible_errors:
                self.warningExtra(
                    "{pin} should be INVISIBLE".format(pin=pinString(pin))
                )

        if self.power_invisible_errors:
            self.error("Power input pins must not be invisible unless used in power symbols.")

            for pin in self.power_invisible_errors:
                self.errorExtra(
                    "{pin} is of type power_in and invisible".format(pin=pinString(pin))
                )

        return self.invisible_errors or self.type_errors or self.power_invisible_errors

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * invisible_errors
            * power_invisible_errors
            * type_errors
        """

        # no need to check this for a derived symbols
        if self.component.extends is not None:
            return False

        fail = False

        if self.checkPins(self.component.pins, self.component.is_power):
            fail = True

        return fail

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing...")

        for pin in self.invisible_errors:
            if not pin.is_hidden:
                pin.is_hidden = True
                self.info("Setting pin {n} to INVISIBLE".format(n=pin.number))

        for pin in self.type_errors:
            if not pin.etype == "no_connect":
                pin.etype = "no_connect"
                self.info("Changing pin {n} type to NO_CONNECT".format(n=pin.number))

        self.recheck()
