from typing import Any, Dict

from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """Minimum hole drill size"""

    def checkPad(self, pad: Dict[str, Any]) -> bool:

        if "drill" not in pad:
            self.error("Pad {p} is missing 'drill' parameter".format(p=pad["number"]))
            return True

        drill = pad["drill"]

        if "size" not in drill:
            self.error(
                "Drill specification is missing 'size' parameter for pad {p}".format(
                    p=pad["number"]
                )
            )
            return True

        size = min(drill["size"]["x"], drill["size"]["y"])

        err = False

        if size < 0.20:
            self.error(
                "Pad {n} min. drill size ({d}mm) is below minimum (0.20mm)".format(
                    n=pad["number"], d=size
                )
            )
            err = True

        return err

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        """
        module = self.module

        return any([self.checkPad(pad) for pad in module.filterPads("thru_hole")])

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fix - not supported for this rule")
