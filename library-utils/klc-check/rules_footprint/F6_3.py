from typing import Any, Dict, List

from kicad_mod import KicadMod
from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """Pad requirements for SMD footprints"""

    REQUIRED_LAYERS = ("Cu", "Paste", "Mask")
    SIDES = ("F.", "B.")

    def __init__(self, component: KicadMod, args):
        super().__init__(component, args)

        self.stencil_pads_with_number: List[Dict[str, Any]] = []

    def checkPads(self, pads: List[Dict[str, Any]]) -> bool:

        self.stencil_pads_with_number = []
        missing_layer_errors = []
        extra_layer_errors = []

        for pad in pads:
            layers = pad["layers"]

            """
            A 'stencil' pad is used when a complex stencil shape is needed.
            - Only on F.Paste or B.Paste (or both)
            - Must not have a number (otherwise rats-nest is generated)
            """

            if all([lyr.endswith(".Paste") for lyr in layers]):
                if not pad["number"] == "":
                    self.stencil_pads_with_number.append(pad)
                continue

            # For SMD parts, following layers required:
            # F.Cu
            # F.Mask
            # F.Paste

            if not pad["type"] == "smd":
                continue

            err = False

            # Check that required layers are present
            for layer in self.REQUIRED_LAYERS:
                present = False
                for side in self.SIDES:
                    lyr = side + layer
                    if lyr in layers:
                        present = True

                # If there's a missing paste layer, try to figure out if
                # there's at least one stencil opening that's inside this pad's
                # area.
                #
                # TODO: Support non-rectangular and rotated pads.
                if (
                    not present
                    and layer == "Paste"
                    and pad["shape"] == "rect"
                    and pad["pos"]["orientation"] == 0
                ):
                    # Get the size of the pad
                    p_x = pad["pos"]["x"]
                    p_y = pad["pos"]["y"]
                    p_w = pad["size"]["x"]
                    p_h = pad["size"]["y"]
                    p_left = p_x - p_w / 2.0
                    p_right = p_x + p_w / 2.0
                    p_bottom = p_y - p_h / 2.0
                    p_top = p_y + p_h / 2.0
                    # Look for a stencil pad
                    for stencil_pad in pads:
                        # TODO: Support non-rectangular and rotated stencil
                        # openings.
                        if (
                            stencil_pad["shape"] != "rect"
                            or stencil_pad["pos"]["orientation"] != 0
                        ):
                            continue
                        # If stencil_pad is a real stencil pad
                        if all(
                            [lyr.endswith(".Paste") for lyr in stencil_pad["layers"]]
                        ):
                            # Get the size of the stencil pad
                            s_x = stencil_pad["pos"]["x"]
                            s_y = stencil_pad["pos"]["y"]
                            s_w = stencil_pad["size"]["x"]
                            s_h = stencil_pad["size"]["y"]
                            s_left = s_x - s_w / 2.0
                            s_right = s_x + s_w / 2.0
                            s_bottom = s_y - s_h / 2.0
                            s_top = s_y + s_h / 2.0
                            # If the stencil pad is entirely within the copper
                            # pad, mark the layer as present
                            if (
                                p_left <= s_left
                                and p_right >= s_right
                                and p_bottom <= s_bottom
                                and p_top >= s_top
                            ):
                                present = True

                if not present:
                    missing_layer_errors.append(
                        "Pad '{n}' missing layer '{lyr}'".format(
                            n=pad["number"], lyr=layer
                        )
                    )

            # Check for extra layers
            allowed = []
            for layer in self.REQUIRED_LAYERS:
                for side in self.SIDES:
                    allowed.append(side + layer)

            for layer in layers:
                if layer not in allowed:
                    extra_layer_errors.append(
                        "Pad '{n}' has extra layer '{lyr}'".format(
                            n=pad["number"], lyr=layer
                        )
                    )
        err = False

        if self.stencil_pads_with_number:
            err = True
            self.error("Stencil pad(s) found with non-empty number")
            for p in self.stencil_pads_with_number:
                self.errorExtra(
                    "Pad '{n}' @ ({x}, {y})".format(
                        n=p["number"], x=p["pos"]["x"], y=p["pos"]["y"]
                    )
                )

        if extra_layer_errors:
            err = True
            self.error("Pad(s) found with extra layers")
            for e in extra_layer_errors:
                self.errorExtra(e)

        if missing_layer_errors:
            self.warning("Pad(s) potentially missing layers")
            for w in missing_layer_errors:
                self.warningExtra(w)

        return err

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * stencil_pads_with_number
        """

        return self.checkPads(self.module.filterPads("smd"))

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        for pad in self.stencil_pads_with_number:
            self.info("Removing number '{x}' for stencil pad".format(x=pad["number"]))
            pad["number"] = ""

        self.recheck()
