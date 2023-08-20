from kicad_sym import mil_to_mm, mm_to_mil
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Pin name position offset"""

    def check(self) -> bool:
        # no need to check this for a derived symbols
        if self.component.extends is not None:
            return False

        offset = mm_to_mil(self.component.pin_names_offset)
        if self.component.hide_pin_names:
            # If the pin names aren't drawn, the offset doesn't matter.
            return False
        elif offset == 0:
            # An offset of 0 means the text is placed outside the symbol,
            # rather than inside.  As the rules about offset only apply when
            # the text is inside the symbol, this case is perfectly OK.
            return False
        elif offset > 50:
            self.error("Pin offset outside allowed range")
            self.errorExtra(f"Pin offset ({offset}) must not be above 50mils")
            return True
        elif offset < 20:
            self.warning("Pin offset outside allowed range")
            self.warningExtra(f"Pin offset ({offset}) should not be below 20mils")
            return True
        elif offset > 20:
            self.warning("Pin offset not preferred value")
            self.warningExtra(
                f"Pin offset ({offset}) should be 20mils unless"
                " required by symbol geometry"
            )

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing, assuming typical symbol geometry...")
        self.component.pin_names_offset = mil_to_mm(20)

        self.recheck()
