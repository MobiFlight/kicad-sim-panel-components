from typing import List

from kicad_sym import KicadSymbol, Pin, Property, mil_to_mm, mm_to_mil
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Text fields should use a common text size of 50mils"""

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.violating_pins: List[Pin] = []
        self.violating_properties: List[Property] = []

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * violating_pins
            * violating_properties
        """

        self.violating_properties = []
        for prop in self.component.properties:
            text_size = mm_to_mil(prop.effects.sizex)
            if text_size != 50:
                self.violating_properties.append(prop)
                message = "{0} at posx {1} posy {2}".format(
                    prop.name, mm_to_mil(prop.posx), mm_to_mil(prop.posy)
                )
                self.error(" - Field {0} size {1}".format(message, text_size))

        self.violating_pins = []

        """
        Pin number MUST be 50mils
        Pin name must be between 20mils and 50mils
        Pin name should be 50mils
        """

        for pin in self.component.pins:
            name_text_size = mm_to_mil(pin.name_effect.sizex)
            num_text_size = mm_to_mil(pin.number_effect.sizex)

            if (
                (name_text_size < 20)
                or (name_text_size > 50)
                or (num_text_size < 20)
                or (num_text_size > 50)
            ):
                self.violating_pins.append(pin)
                self.error(
                    " - Pin {0} ({1}), text size {2}, number size {3}".format(
                        pin.name, pin.number, name_text_size, num_text_size
                    )
                )
            else:
                if name_text_size != 50:
                    self.warning(
                        "Pin {0} ({1}) name text size should be 50mils (or 20...50mils"
                        " if required by the symbol geometry)".format(
                            pin.name, pin.number
                        )
                    )
                if num_text_size != 50:
                    self.warning(
                        "Pin {0} ({1}) number text size should be 50mils (or"
                        " 20...50mils if required by the symbol geometry)".format(
                            pin.name, pin.number
                        )
                    )

        if self.violating_properties or self.violating_pins:
            return True

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """
        if self.violating_properties:
            self.info("Fixing field text size")
        for prop in self.violating_properties:
            prop.effects.sizex = mil_to_mm(50)
            prop.effects.sizey = mil_to_mm(50)

        if self.violating_pins:
            self.info("Fixing pin text size")
        for pin in self.violating_pins:
            pin.name_effect.sizex = mil_to_mm(50)
            pin.name_effect.sizey = mil_to_mm(50)
            pin.number_effect.sizex = mil_to_mm(50)
            pin.number_effect.sizey = mil_to_mm(50)
        self.recheck()
