import re
from typing import List

from kicad_sym import KicadSymbol, Pin
from rules_symbol.rule import KLCRule, pinString


class Rule(KLCRule):
    """Pin electrical type should match pin function"""

    # Power Input Pins should be 'W'
    POWER_INPUTS = ["^[ad]*g(rou)*nd(a)*$", "^[ad]*v(aa|cc|dd|ss|bat|in)$"]

    # Power Output Pins should be 'w'
    POWER_OUTPUTS = ["^vout$"]

    PASSIVE_PINS = []

    # Input Pins should be "I"
    INPUT_PINS = ["^sdi$", "^cl(oc)*k(in)*$", "^~*cs~*$", "^[av]ref$"]

    # Output pins should be "O"
    OUTPUT_PINS = ["^sdo$", "^cl(oc)*kout$"]

    # Bidirectional pins should be "B"
    BIDIR_PINS = ["^sda$", "^s*dio$"]

    warning_tests = {
        "power_out": POWER_OUTPUTS,
        "passive": PASSIVE_PINS,
        "input": INPUT_PINS,
        "output": OUTPUT_PINS,
        "bidirectional": BIDIR_PINS,
    }

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.power_errors: List[Pin] = []
        self.suggestions: List[Pin] = []
        self.inversion_errors: List[Pin] = []

    # check if a pin name fits within a list of possible pins (using regex testing)
    def test(self, pinName: str, nameList: List[str]) -> bool:
        for name in nameList:
            if re.search(name, pinName, flags=re.IGNORECASE) is not None:
                return True
        return False

    # These pin types must be satisfied
    def checkPowerPins(self) -> bool:
        self.power_errors = []

        for stack in self.component.get_pinstacks().values():
            visible = [pin for pin in stack if not pin.is_hidden]
            invisible = [pin for pin in stack if pin.is_hidden]
            # Due to the implementation of S4.3 it is possible to assume that at maximum one pin is
            # visible.
            if visible:
                checkpins = [visible[0]]
            else:
                checkpins = invisible
            for pin in checkpins:
                name = pin.name.lower()
                etype = pin.etype

                if self.test(name.lower(), self.POWER_INPUTS) and (
                    not etype.lower() == "power_in"
                ):
                    if not self.power_errors:
                        self.error(
                            "Power pins should be of type POWER INPUT"
                        )
                    self.power_errors.append(pin)
                    self.errorExtra(
                        "{pin} is of type {t}".format(pin=pinString(pin), t=etype)
                    )

            if len(stack) > 1 and visible and visible[0].etype.lower() == "power_in":
                for pin in invisible:
                    if pin.etype.lower() != "passive":
                        if not self.power_errors:
                            self.error(
                                "Invisible powerpins in stacks should be of type"
                                " PASSIVE"
                            )

        return len(self.power_errors) > 0

    # These pin types are suggestions
    def checkSuggestions(self) -> bool:
        self.suggestions = []

        for pin in self.component.pins:
            name = pin.name.lower()
            etype = pin.etype

            for pin_type in self.warning_tests.keys():
                tests = self.warning_tests[pin_type]

                if self.test(name, tests):
                    if not pin_type == etype:
                        if not self.suggestions:
                            self.warning("Pin types should match pin function")
                        self.suggestions.append(pin)
                        self.warningExtra(
                            "{pin} is type {t1} : suggested {t2}".format(
                                pin=pinString(pin), t1=etype, t2=pin_type
                            )
                        )

                    break

        # No error generated for this rule
        return False

    def checkDoubleInversions(self) -> bool:
        self.inversion_errors = []
        for pin in self.component.pins:
            m = re.search(r"(\~{)(.+)}", pin.name)
            if m and pin.shape == "inverted":
                if not self.inversion_errors:
                    self.error(
                        "Pins should not be inverted twice (with inversion-symbol on"
                        " pin and overline on label)"
                    )
                self.inversion_errors.append(pin)
                self.errorExtra(
                    "{pin} : double inversion (overline + pin type:Inverting)".format(
                        pin=pinString(pin)
                    )
                )

        return len(self.inversion_errors) > 0

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * power_errors
            * suggestions
            * inversion_errors
        """

        # no need to check this for a derived symbols
        if self.component.extends is not None:
            return False

        return any(
            [
                self.checkPowerPins(),
                self.checkDoubleInversions(),
                self.checkSuggestions(),
            ]
        )

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing...")

        for pin in self.power_errors:

            pin["electrical_type"] = "W"  # Power Input

            self.info("Changing pin {n} type to POWER_INPUT".format(n=pin["num"]))

        for pin in self.inversion_errors:
            pin["pin_type"] = ""  # reset pin type (removes dot at the base of pin)
            self.info("Removing double inversion on pin {n}".format(n=pin["num"]))

        self.recheck()
