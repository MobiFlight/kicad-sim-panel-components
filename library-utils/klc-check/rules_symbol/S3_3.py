import math
from typing import Optional

from kicad_sym import KicadSymbol, Polyline, mil_to_mm, mm_to_mil
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Symbol outline and fill requirements"""

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.center_rect_polyline: Optional[Polyline] = None

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * center_rect_polyline
        """

        # no checks for power-symbols, graphical symbols or derived symbols
        if (
            self.component.is_power_symbol()
            or self.component.is_graphic_symbol()
            or self.component.extends is not None
        ):
            return False

        # check if component has just one rectangle, if not, skip checking
        self.center_rect_polyline = self.component.get_center_rectangle(
            range(self.component.unit_count)
        )
        if self.center_rect_polyline is None:
            return False

        rectangle_need_fix = False
        if self.component.is_small_component_heuristics():
            if not math.isclose(self.center_rect_polyline.stroke_width, mil_to_mm(10)):
                self.warning(
                    "Component outline is thickness {0}mil, recommended is {1}mil for"
                    " standard symbol".format(
                        mm_to_mil(self.center_rect_polyline.stroke_width), 10
                    )
                )
                self.warningExtra(
                    "exceptions are allowed for small symbols like resistor,"
                    " transistor, ..."
                )
                rectangle_need_fix = False
        else:
            if not math.isclose(self.center_rect_polyline.stroke_width, mil_to_mm(10)):
                self.error(
                    "Component outline is thickness {0}mil, recommended is {1}mil".format(
                        mm_to_mil(self.center_rect_polyline.stroke_width), 10
                    )
                )
                rectangle_need_fix = True

        if self.center_rect_polyline.fill_type != "background":
            msg = (
                "Component background is filled with {0} color, recommended is filling"
                " with {1} color".format(
                    self.center_rect_polyline.fill_type, "background"
                )
            )
            if self.component.is_small_component_heuristics():
                self.warning(msg)
                self.warningExtra(
                    "exceptions are allowed for small symbols like resistor,"
                    " transistor, ..."
                )
            else:
                self.error(msg)
                rectangle_need_fix = True

        return rectangle_need_fix

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        return
