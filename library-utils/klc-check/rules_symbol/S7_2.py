from kicad_sym import KicadSymbol
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Graphical symbols follow some special rules/KLC-exceptions"""

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.fixTooManyPins: bool = False
        self.fixNoFootprint: bool = False

    def check(self) -> bool:
        # no need to check this for a derived symbols
        if self.component.extends is not None:
            return False

        fail = False
        if self.component.is_graphic_symbol():
            # no pins in graphical symbol
            if self.component.pins:
                self.error("Graphical symbols have no pins")
                fail = True
                self.fixTooManyPins = True
            # footprint field must be empty
            fp_prop = self.component.get_property("Footprint")
            if fp_prop and fp_prop.value != "":
                self.error(
                    "Graphical symbols have no footprint association (footprint was set to '"
                    + fp_prop.value
                    + "')"
                )
                fail = True
                self.fixNoFootprint = True
            # FPFilters must be empty
            if self.component.get_fp_filters():
                self.error("Graphical symbols have no footprint filters")
                fail = True
                self.fixNoFootprint = True
            # Ref is set to '#SYM' and is invisible
            ref_prop = self.component.get_property("Reference")
            if not ref_prop:
                self.error("Graphical symbols have a Reference property")
            else:
                if ref_prop.value != "#SYM":
                    self.error("Graphical symbols have Reference set to '#SYM' ")
                    fail = True
                if not ref_prop.effects.is_hidden:
                    self.error("Graphical symbols have a hidden Reference")
                    fail = True
            # Value is invisible
            value_prop = self.component.get_property("Value")
            if not value_prop:
                self.error("Graphical symbols have a Value property")
            else:
                if not value_prop.effects.is_hidden:
                    self.error("Graphical symbols have a hidden Value")
                    fail = True
            if self.component.in_bom is True:
                self.error("Graphical symbols must be 'Excluded from schematic bill of materials'")
                fail = True
            if self.component.on_board is True:
                self.error("Graphical symbols must be 'Excluded from board'")
                fail = True

        return fail

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        if self.fixTooManyPins:
            self.info("FIX for too many pins in graphical symbol")
            self.component.pins = []
        if self.fixNoFootprint:
            self.info("FIX empty footprint association and FPFilters")
            self.component.get_property("Footprint").value = ""
            self.component.get_property("ki_fp_filters").value = ""
