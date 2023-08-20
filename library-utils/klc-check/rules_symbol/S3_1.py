import math

from kicad_sym import mm_to_mil
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Origin is centered on the middle of the symbol"""

    def check(self) -> bool:
        """
        Calculate the 'bounds' of the symbol based on rectangle (if only a
        single filled rectangle is present) or on pin positions.
        """

        # no need to check this for an
        if self.component.extends is not None:
            return False

        # Check units separately
        unit_count = self.component.unit_count

        for unit in range(1, unit_count + 1):
            # If there is only a single filled rectangle, we assume that it is the
            # main symbol outline.
            center_pl = self.component.get_center_rectangle([0, unit])
            if center_pl is not None:
                (x, y) = center_pl.get_center_of_boundingbox()
            else:
                pins = [pin for pin in self.component.pins if (pin.unit in [unit, 0])]

                # No pins? Ignore check.
                # This can be improved to include graphical items too...
                if not pins:
                    continue
                x_pos = [pin.posx for pin in pins]
                y_pos = [pin.posy for pin in pins]
                x_min = min(x_pos)
                x_max = max(x_pos)
                y_min = min(y_pos)
                y_max = max(y_pos)

                # Center point average
                x = (x_min + x_max) / 2
                y = (y_min + y_max) / 2

            # convert to mil
            x = mm_to_mil(x)
            y = mm_to_mil(y)
            # Right on the middle!
            if x == 0 and y == 0:
                continue
            elif math.fabs(x) <= 50 and math.fabs(y) <= 50:
                self.warning("Symbol unit {unit} slightly off-center".format(unit=unit))
                self.warningExtra("  Center calculated @ ({x}, {y})".format(x=x, y=y))
            else:
                self.error(
                    "Symbol unit {unit} not centered on origin".format(unit=unit)
                )
                self.errorExtra("Center calculated @ ({x}, {y})".format(x=x, y=y))

        return False

    def fix(self) -> None:
        return
