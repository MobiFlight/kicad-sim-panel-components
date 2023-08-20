from typing import Dict

from kicad_sym import KicadSymbol, mil_to_mm
from rules_symbol.rule import KLCRule, positionFormater


class Rule(KLCRule):
    """Check part reference, name and footprint position and alignment"""

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.recommended_ref_pos: Dict[str, float] = {}
        self.recommended_ref_alignment: str = ""
        self.recommended_name_pos: Dict[str, float] = {}
        self.recommended_name_alignment: str = ""
        self.recommended_fp_pos: Dict[str, float] = {}
        self.recommended_fp_alignment: str = ""

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * recommended_ref_pos
            * recommended_ref_alignment
            * recommended_name_pos
            * recommended_name_alignment
            * recommended_fp_pos
            * recommended_fp_alignment
        """

        # check if component has just one rectangle, if not, skip checking
        ctr = self.component.get_center_rectangle(units=[0, 1])
        if not ctr:
            return False

        (maxx, top, minx, bottom) = ctr.get_boundingbox()

        # reference checking

        # If there is no pin in the top, the recommended position to ref is at top-center,
        # horizontally centered.
        if not self.component.filter_pins(direction="D"):
            self.recommended_ref_pos = {"posx": 0, "posy": (top + mil_to_mm(125))}
            self.recommended_ref_alignment = "center"

        # otherwise, the recommended is put it before the first pin x position, right-aligned
        else:
            x = min(
                [i.posx for i in self.component.filter_pins(direction="D")]
            ) - mil_to_mm(100)
            self.recommended_ref_pos = {"posx": x, "posy": (top + mil_to_mm(125))}
            self.recommended_ref_alignment = "right"

        # get the current reference infos and compare them to recommended ones
        ref = self.component.get_property("Reference")
        if ref:
            if not ref.compare_pos(
                self.recommended_ref_pos["posx"], self.recommended_ref_pos["posy"]
            ):
                self.warning(
                    "field: reference, {0}, recommended {1}".format(
                        positionFormater(ref),
                        positionFormater(self.recommended_ref_pos),
                    )
                )
            if ref.effects.h_justify != self.recommended_ref_alignment:
                self.warning(
                    "field: reference, justification {0}, recommended {1}".format(
                        ref.effects.h_justify, self.recommended_ref_alignment
                    )
                )
            # Does vertical alignment matter too?
            # What about orientation checking?

        # name checking

        # If there is no pin in the top, the recommended position to name is at top-center,
        # horizontally centered.
        if not self.component.filter_pins(direction="D"):
            self.recommended_name_pos = {"posx": 0, "posy": (top + mil_to_mm(50))}
            self.recommended_name_alignment = "center"

        # otherwise, the recommended is put it before the first pin x position, right-aligned
        else:
            x = min(
                [i.posx for i in self.component.filter_pins(direction="D")]
            ) - mil_to_mm(100)
            self.recommended_name_pos = {"posx": x, "posy": (top + mil_to_mm(50))}
            self.recommended_name_alignment = "right"

        # get the current name infos and compare them to recommended ones
        name = self.component.get_property("Value")
        if name:
            if not name.compare_pos(
                self.recommended_name_pos["posx"], self.recommended_name_pos["posy"]
            ):
                self.warning(
                    "field: name, {0}, recommended {1}".format(
                        positionFormater(name),
                        positionFormater(self.recommended_name_pos),
                    )
                )
            if name.effects.h_justify != self.recommended_name_alignment:
                self.warning(
                    "field: name, justification {0}, recommended {1}".format(
                        name.effects.h_justify, self.recommended_name_alignment
                    )
                )

        # footprint checking

        # If there is no pin in the bottom, the recommended position to footprint is at
        # bottom-center, horizontally centered.
        if not self.component.filter_pins(direction="U"):
            self.recommended_fp_pos = {"posx": 0, "posy": (bottom - mil_to_mm(50))}
            self.recommended_fp_alignment = "center"

        # otherwise, the recommended is put it after the last pin x position, left-aligned
        else:
            x = max(
                [i.posx for i in self.component.filter_pins(direction="U")]
            ) + mil_to_mm(50)
            self.recommended_fp_pos = {"posx": x, "posy": (bottom - mil_to_mm(50))}
            self.recommended_fp_alignment = "left"

        # get the current footprint infos and compare them to recommended ones
        fp = self.component.get_property("Footprint")
        if fp:
            if not fp.compare_pos(
                self.recommended_fp_pos["posx"], self.recommended_fp_pos["posy"]
            ):
                self.warning(
                    "field: footprint, {0}, recommended {1}".format(
                        positionFormater(fp), positionFormater(self.recommended_fp_pos)
                    )
                )
            if fp.effects.h_justify != self.recommended_fp_alignment:
                self.warning(
                    "field: footprint, justification {0}, recommended {1}".format(
                        fp.effects.h_justify, self.recommended_fp_alignment
                    )
                )

        # This entire rule only generates a WARNING (won't fail a component, only display a
        # message).
        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing...")
        fp = self.component.get_property("Footprint")
        fp.posx = self.recommended_fp_pos["posx"]
        fp.posy = self.recommended_fp_pos["posy"]
        fp.effects.h_justify = self.recommended_fp_alignment

        ref = self.component.get_property("Reference")
        ref.posx = self.recommended_ref_pos["posx"]
        ref.posy = self.recommended_ref_pos["posy"]
        ref.effects.h_justify = self.recommended_ref_alignment

        val = self.component.get_property("Value")
        val.posx = self.recommended_name_pos["posx"]
        val.posy = self.recommended_name_pos["posy"]
        val.effects.h_justify = self.recommended_name_alignment

        self.recheck()
