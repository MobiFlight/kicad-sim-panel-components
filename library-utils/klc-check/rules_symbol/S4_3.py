import sys
from typing import List

from kicad_sym import KicadSymbol, Pin
from rules_symbol.rule import KLCRule, pinString


class Rule(KLCRule):
    """Rules for pin stacking"""

    SPECIAL_POWER_PINS = ["power_in", "power_out", "output"]

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.different_names: List[str] = []
        self.different_types: List[str] = []
        self.visible_pin_not_lowest: List[str] = []
        self.NC_stacked: List[Pin] = []
        self.non_numeric: List[str] = []
        self.more_then_one_visible: bool = False

    def count_pin_etypes(self, pins: List[Pin], etyp: str) -> int:
        n = 0
        for pin in pins:
            if pin.etype == etyp:
                n += 1
        return n

    def get_smallest_pin_number(self, pins: List[Pin]) -> int:
        min_pin_number = sys.maxsize
        for p in pins:
            if p.number_int is not None:
                min_pin_number = min(p.number_int, min_pin_number)
        return min_pin_number

    def check(self) -> bool:
        # no need to check this for a derived symbols
        if self.component.extends is not None:
            return False

        possible_power_pin_stacks = []

        # iterate over pinstacks
        for (pos, pins) in self.component.get_pinstacks().items():
            # skip stacks with only one pin
            if len(pins) == 1:
                continue

            common_pin_name = pins[0].name
            visible_pin = None
            common_etype = pins[0].etype
            min_pin_number = self.get_smallest_pin_number(pins)

            for pin in pins:
                if pin.number_int is None and pos not in self.non_numeric:
                    self.warning(
                        "Found non-numeric pin in a pinstack: {0}".format(
                            pinString(pin)
                        )
                    )
                    self.non_numeric.append(pos)

                # Check1: If a single pin in a stack is of type NC, we consider this an error
                if pin.etype == "no_connect":
                    self.error(
                        "NC {pin} (x={x}, y={y}) is stacked on other pins".format(
                            pin=pinString(pin), x=pin.posx, y=pin.posy
                        )
                    )
                    self.NC_stacked.append(pin)

                # Check2: all pins should have the same name
                if pin.name != common_pin_name and pos not in self.different_names:
                    self.error("Pin names in the stack have different names")
                    self.different_names.append(pos)
                    for pin in pins:
                        self.errorExtra(pinString(pin))

                # Check3: exactly one pin should be visible
                if not pin.is_hidden:
                    if visible_pin is not None:
                        if not self.more_then_one_visible:
                            self.error(
                                "A pin stack must have exactly one (1) visible pin"
                            )
                            for pin in pins:
                                self.errorExtra(
                                    "{pin} is visible".format(pin=pinString(pin))
                                )
                        self.more_then_one_visible = True
                    else:
                        visible_pin = pin

                    # the visible pin should have the lowest pin_number
                    if (
                        pin.number_int is not None
                        and pin.number_int != min_pin_number
                        and pos not in self.visible_pin_not_lowest
                    ):
                        self.warning(
                            "The pin with the lowest number in a pinstack should be"
                            " visible"
                        )
                        self.warningExtra(
                            "Pin {0} is visible, the lowest number in this stack is {1}".format(
                                pinString(pin), min_pin_number
                            )
                        )
                        self.visible_pin_not_lowest.append(pos)

                # Check4: all pins should have the same electrical type.
                #         exceptions are power-pin-stacks
                if pin.etype != common_etype:
                    # this could be one of the special cases
                    # At least one of the two checked pins needs to be 'special' type.
                    # If not, this is an error.
                    if (
                        pin.etype in self.SPECIAL_POWER_PINS
                        or common_etype in self.SPECIAL_POWER_PINS
                    ):
                        possible_power_pin_stacks.append(pos)
                    else:
                        if pos not in self.different_types:
                            self.error(
                                "Pin names in the stack have different electrical types"
                            )
                            for pin in pins:
                                self.errorExtra(
                                    "{0} is of type {1}".format(
                                        pinString(pin), pin.etype
                                    )
                                )
                            self.different_types.append(pos)

        # check the possible power pin_stacks
        special_stack_err = False
        for pos in possible_power_pin_stacks:
            pins = self.component.get_pinstacks()[pos]
            min_pin_number = self.get_smallest_pin_number(pins)

            # 1. consists only of output and passive pins
            # 2. consists only of power-output and passive pins
            # 3. consists only of power-input and passive pins
            # 4. consists only of power-output/output pins

            # count types of pins
            n_power_in = self.count_pin_etypes(pins, "power_in")
            n_power_out = self.count_pin_etypes(pins, "power_out")
            n_output = self.count_pin_etypes(pins, "output")
            n_passive = self.count_pin_etypes(pins, "passive")
            n_others = len(pins) - n_power_in - n_power_out - n_passive - n_output
            n_total = len(pins)

            # check for cases 1..3
            if n_passive == n_total - 1 and (
                n_power_in == 1 or n_power_out == 1 or n_output == 1
            ):
                # find the passive pins, they must be invisible
                for pin in pins:
                    if pin.etype == "passive" and not pin.is_hidden:
                        self.error("Passive pins in a pinstack are hidden")
                        special_stack_err = True
                        for ipin in pins:
                            if ipin.etype == "passive" and not ipin.is_hidden:
                                self.errorExtra(
                                    "{0} is of type {1} and visible".format(
                                        pinString(ipin), ipin.etype
                                    )
                                )
                        break

                # Find the non-passive pin, it must be visible.
                # Also, it should have the lowest pin-number of all.
                for pin in pins:
                    if pin.etype != "passive":
                        # we found the non-passive pin
                        if pin.is_hidden:
                            self.error("Non passive pins in a pinstack are visible")
                            special_stack_err = True
                            self.errorExtra(
                                "{0} is of type {1} and invisible".format(
                                    pinString(pin), pin.etype
                                )
                            )

                        if (
                            pin.number_int is not None
                            and pin.number_int != min_pin_number
                            and pos not in self.visible_pin_not_lowest
                        ):
                            self.warning(
                                "The pin with the lowest number in a pinstack should be"
                                " visible"
                            )
                            self.warningExtra(
                                "Pin {0} is visible, the lowest number in this stack"
                                " is {1}".format(pinString(pin), min_pin_number)
                            )
                            self.visible_pin_not_lowest.append(pos)
                        break

            # check for case 4
            elif n_output == n_total or n_power_out == n_total:
                visible_pin = None
                # all but one pins should be invisible
                for pin in pins:
                    if not pin.is_hidden:
                        if visible_pin is None:
                            # this is the first time we found a visible pin in this stack
                            visible_pin = pin
                            if (
                                pin.number_int is not None
                                and pin.number_int != min_pin_number
                                and pos not in self.visible_pin_not_lowest
                            ):
                                self.warning(
                                    "The pin with the lowest number in a pinstack"
                                    " should be visible"
                                )
                                self.warningExtra(
                                    "Pin {0} is visible, the lowest number in this"
                                    " stack is {1}".format(
                                        pinString(pin), min_pin_number
                                    )
                                )
                                self.visible_pin_not_lowest.append(pos)
                        else:
                            # more than one visible pin found
                            special_stack_err = True
                            self.error("Only one pin in a pinstack is visible")
                            for vpin in (pin for pin in pins if not pin.is_hidden):
                                self.errorExtra(
                                    "Pin {0} is visible".format(pinString(vpin))
                                )

            else:
                # pinstack is none of the above cases.
                self.error(
                    "Illegal pin stack configuration next to {}".format(
                        pinString(pins[0])
                    )
                )
                self.errorExtra("Power input pins: {}".format(n_power_in))
                self.errorExtra("Power output pins: {}".format(n_power_out))
                self.errorExtra("Output pins: {}".format(n_output))
                self.errorExtra("Passive pins: {}".format(n_passive))
                self.errorExtra("Other type pins: {}".format(n_others))
                special_stack_err = True

        return bool(
            self.more_then_one_visible
            or self.different_types
            or self.NC_stacked
            or self.different_names
            or special_stack_err
        )

    def fix(self) -> None:
        self.info("FIX not supported (yet)! Please fix manually.")
