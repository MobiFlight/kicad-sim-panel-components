# -*- coding: utf-8 -*-

# math and comments from Michal script
# https://github.com/michal777/KiCad_Lib_Check

from rules_footprint.rule import KLCRule, getStartPoint, getEndPoint, graphItemString
import math


class Rule(KLCRule):
    """Basic geometry checks"""

    # set thresholds for tested angle
    smallAngle = math.radians(2.0)
    verySmallAngle = math.radians(0.4)

    strangeLines = []
    nullLines = []
    hvLines = []

    def getStrangeLines(self, lines):

        for line in lines:
            start = getStartPoint(line)
            end = getEndPoint(line)

            if start == end:
                # a 0 length line
                self.nullLines.append(line)
                continue

            p1x = abs(end['x'] - start['x'])
            p1y = abs(end['y'] - start['y'])

            # really h or v ?
            if (p1x == 0) or (p1y == 0):
                continue

            # imaginary second point
            if p1x > p1y:     # horizontal
                p2x = p1x
                p2y = 0
            else:             # vertical
                p2x = 0
                p2y = p1y

            d1 = math.hypot(p1x, p1y)
            d2 = math.hypot(p2x, p2y)

            if d1 < 1e-6 or d2 < 1e-6:
                self.hvLines.append(line)

            A = math.acos((p1x*p2x + p1y*p2y) / (d1*d2))

            if A < self.verySmallAngle:
                self.hvLines.append(line)
            elif A < self.smallAngle:
                self.strangeLines.append(line)

        return

    def check(self):
        """
        Proceeds the checking of the rule.
        """

        layers_to_check = ['F.Fab', 'B.Fab', 'F.SilkS', 'B.SilkS', 'F.CrtYd', 'B.CrtYd']

        for layer in layers_to_check:

            self.strangeLines.clear()
            self.nullLines.clear()
            self.hvLines.clear()
            self.getStrangeLines(self.module.filterLines(layer))

            if len(self.nullLines) > 0:
                self.warning("Zero length lines")
                self.warningExtra("The following lines have 0 length")
                for bad in self.nullLines:
                    self.warningExtra(graphItemString(bad, layer=True, width=False))

            if len(self.hvLines) > 0:
                self.warning("Low angle")
                self.warningExtra("The following lines should be vertical or horizontal")
                for bad in self.hvLines:
                    self.warningExtra(graphItemString(bad, layer=True, width=False))

            if len(self.strangeLines) > 0:
                self.warning("Verticality / horizontality")
                self.warningExtra(
                    "The following lines might be slightly not horizontal or vertical")
                for bad in self.strangeLines:
                    self.warningExtra(graphItemString(bad, layer=True, width=False))

        return 0  # There is no KLC rule for this so this check only generates warnings

    def fix(self):
        """
        Proceeds the fixing of the rule, if possible.
        """
        return
