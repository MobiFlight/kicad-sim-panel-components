from typing import List

from kicad_mod import KicadMod
from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """For through-hole components, footprint anchor is set on pad 1"""

    def __init__(self, component: KicadMod, args):
        super().__init__(component, args)

        self.pin1_position: List[float] = []
        self.pin1_count: int = 0

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * pin1_position
            * pin1_count
        """

        # List of potential names for pad-1
        names = ["1", "A", "A1", "P1", "PAD1"]
        pads = []

        module = self.module

        num = ""

        # check if module is through-hole
        if module.attribute == "through_hole":

            for name in names:
                pads = module.getPadsByNumber(name)
                if pads:
                    num = name
                    break

            if not pads:
                self.warning("Pad 1 not found in footprint!")
                return False

            self.pin1_count = len(pads)

            for pad in pads:
                pos = pad["pos"]

                if not self.pin1_position:
                    self.pin1_position = [pos["x"], pos["y"]]

                # Pad is located at origin
                if pos["x"] == 0 and pos["y"] == 0:
                    return False

            # More than one pad-1? Only a warning...
            if len(pads) > 1:
                self.warning("Multiple Pins exist with number '{num}'".format(num=num))
                self.warningExtra("None are located on origin")

            else:
                self.error("Pad '{num}' not located at origin".format(num=num))
                self.errorExtra("Set origin to location of Pad '{num}'".format(num=num))

            return True

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        module = self.module
        if self.check() and self.pin1_position:
            self.info("Moved anchor position to Pin-1")
            module.setAnchor(self.pin1_position)
