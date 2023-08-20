from kicad_sym import KicadSymbol, Pin, mm_to_mil
from rulebase import KLCRuleBase, Verbosity


def pinString(pin: Pin, loc: bool = True, unit=None, convert=None) -> str:
    return "Pin {name} ({num}){loc}{unit}".format(
        name=pin.name,
        num=pin.number,
        loc=" @ ({x},{y})".format(x=mm_to_mil(pin.posx), y=mm_to_mil(pin.posy))
        if loc
        else "",
        unit=" in unit {n}".format(n=pin.unit) if unit else "",
    )


def positionFormater(element) -> str:
    if isinstance(element, dict):
        if not {"posx", "posy"}.issubset(element.keys()):
            raise Exception("missing keys 'posx' and 'posy' in" + str(element))
        return "@ ({0}, {1})".format(
            mm_to_mil(element["posx"]), mm_to_mil(element["posy"])
        )
    if hasattr(element, "posx") and hasattr(element, "posy"):
        return "@ ({0}, {1})".format(mm_to_mil(element.posx), mm_to_mil(element.posy))
    raise Exception("input type: ", type(element), "not supported, ", element)


class KLCRule(KLCRuleBase):
    """A base class to represent a KLC rule

    Create the methods check and fix to use with the kicad lib files.
    """

    verbosity: Verbosity = Verbosity.NONE

    def __init__(self, component: KicadSymbol):
        super().__init__()
        self.component: KicadSymbol = component
