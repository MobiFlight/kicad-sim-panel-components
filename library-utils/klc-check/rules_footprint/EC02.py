# -*- coding: utf-8 -*-

from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """Pad shape checks"""

    def check(self):
        # Check that smd pads are not rectangle
        bad_pads = []
        for pad in self.module.pads:
            if pad['type'] == 'smd' and pad['shape'] == 'rect':
                bad_pads.append(str(pad['number']))

        if bad_pads:
            self.warning("Rectangular SMD pad")
            self.warningExtra(f"Pads {', '.join(bad_pads)} are square. "
                              "If possible, change to round-rect.")

    def fix(self):
        """
        Proceeds the fixing of the rule, if possible.
        """
        return
