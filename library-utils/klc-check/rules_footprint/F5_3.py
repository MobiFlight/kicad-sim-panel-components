# math and comments from Michal script
# https://github.com/michal777/KiCad_Lib_Check

import os
import re
from typing import Any, Dict, List, Optional

from boundingbox import BoundingBox
from kicad_mod import KicadMod
from rules_footprint.klc_constants import KLC_CRTYD_GRID, KLC_CRTYD_WIDTH
from rules_footprint.rule import (
    KLCRule,
    getEndPoint,
    getStartPoint,
    graphItemString,
    mapToGrid,
    mmToNanoMeter,
)


class Rule(KLCRule):
    """Courtyard layer requirements"""

    def __init__(self, component: KicadMod, args):
        super().__init__(component, args)

        self.module_dir: str = ""

        self.bad_grid: List[Dict[str, Any]] = []
        self.bad_width: List[Dict[str, Any]] = []
        self.unconnected: List[Dict[str, Any]] = []

        self.fCourtyard: List[Dict[str, Any]] = []
        self.bCourtyard: List[Dict[str, Any]] = []

    # Get the superposed boundary of pads and fab layer
    def getFootprintBounds(self) -> BoundingBox:
        module = self.module

        padBounds = module.overpadsBounds()

        # Try getting bounds from these layers, in order
        layers = ["F.Fab", "B.Fab", "F.SilkS", "B.SilkS"]

        # Accept first valid layer
        for layer in layers:
            geo = module.geometricBoundingBox(layer)
            if geo.valid:
                print("using drawing from layer", layer)
                break

        # Add two bounding boxes together
        padBounds.addBoundingBox(geo)

        return padBounds

    # Return best-guess for courtyard offset
    def defaultOffset(self) -> float:
        module = self.module
        module_dir = os.path.split(os.path.dirname(os.path.realpath(module.filename)))[
            -1
        ]
        self.module_dir = "{0}".format(os.path.splitext(module_dir))

        # Default offset
        offset = 0.25

        bb = self.getFootprintBounds()

        # Smaller offset for miniature components
        if bb.width < 2 and bb.height < 2:
            offset = 0.15

        # BGA components required 1.0mm clearance
        if re.match("BGA-.*", module.name) or re.match(".*Housing.*BGA.*", module_dir):
            offset = 1

        # Connectors require 0.5mm clearance
        elif (
            re.match(".*Connector.*", module.name)
            or re.match(".*Connector.*", self.module_dir)
            or re.match(".*Socket.*", module.name)
            or re.match(".*Socket.*", self.module_dir)
            or re.match(".*Button.*", module.name)
            or re.match(".*Button.*", self.module_dir)
            or re.match(".*Switch.*", module.name)
            or re.match(".*Switch.*", self.module_dir)
        ):
            offset = 0.5

        return offset

    def defaultCourtyard(self) -> Optional[Dict[str, float]]:
        bb = self.getFootprintBounds()

        offset = self.defaultOffset()

        bb.expand(offset)

        print("Offset:", offset)

        if bb.valid:
            return {
                "x": mapToGrid(bb.xmin, KLC_CRTYD_GRID),
                "y": mapToGrid(bb.ymin, KLC_CRTYD_GRID),
                "width": mapToGrid(bb.width, KLC_CRTYD_GRID),
                "height": mapToGrid(bb.height, KLC_CRTYD_GRID),
            }

        # No valid bounding box found in component
        else:
            return None

    def isClosed(self, layer) -> List[Any]:
        def isSame(
            p1: Dict[str, float], p2: Dict[str, float], tolerance: float
        ) -> bool:
            s = (
                abs(p1["x"] - p2["x"]) <= tolerance
                and abs(p1["y"] - p2["y"]) <= tolerance
            )
            return s

        # no line is considered as closed
        if not layer:
            return []

        # calculate degree of vertices of the graph
        degree = [1]*2*len(layer)

        for i in range(len(layer)):
            pi = [getStartPoint(layer[i]), getEndPoint(layer[i])]
            # check for circles
            if isSame(pi[0], pi[1], 0):
                degree[i * 2] += 1
                degree[i * 2 + 1] += 1

            for j in range(i + 1, len(layer)):
                pj = [getStartPoint(layer[j]), getEndPoint(layer[j])]

                # check the line against the other one
                tolerance = 1e-9
                if "angle" in layer[i] or "angle" in layer[j]:
                    tolerance = 0.01
                for ii in range(2):
                    for jj in range(2):
                        if isSame(pi[ii], pj[jj], tolerance):
                            degree[i * 2 + ii] += 1
                            degree[j * 2 + jj] += 1

        bad = []
        for i in range(len(layer)):
            # line is unconnected if one of it's vertices has odd degree
            if degree[2*i] % 2 == 1 or degree[2*i + 1] % 2 == 1:
                bad.append(layer[i])

        return bad

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * bad_grid
            * bad_width
            * unconnected
            * fCourtyard
            * bCourtyard
        """

        module = self.module

        self.bad_grid = []
        self.bad_width = []
        self.unconnected = []

        self.fCourtyard = module.filterGraphs("F.CrtYd")
        self.bCourtyard = module.filterGraphs("B.CrtYd")

        # Check for existence of courtyard
        if not self.fCourtyard:
            if not self.bCourtyard:
                self.error("No courtyard found!")
                self.errorExtra("Add courtyard around footprint")
                return True

        self.courtyard = self.fCourtyard + self.bCourtyard

        # Check for closed courtyard outlines
        self.unconnected.extend(self.isClosed(self.fCourtyard))
        self.unconnected.extend(self.isClosed(self.bCourtyard))

        # Check for elements that are not on the grid
        GRID = mmToNanoMeter(KLC_CRTYD_GRID)
        for graph in self.courtyard:
            if graph["width"] != KLC_CRTYD_WIDTH:
                self.bad_width.append(graph)

            start = getStartPoint(graph)
            end = getEndPoint(graph)

            if not start or not end:
                self.bad_grid.append(graph)
                continue

            # make a list of all x and y coordinates of this graphical elements
            x1 = mmToNanoMeter(start["x"])
            y1 = mmToNanoMeter(start["y"])
            x2 = mmToNanoMeter(end["x"])
            y2 = mmToNanoMeter(end["y"])
            check = [x1, y1, x2, y2]

            # use a modulo division to check if those coordinates are on the grid
            # if at least one of the coordinates is not on the grid, add this
            # element to the bad_grid list
            grid_error = False
            for c in check:
                if not (c % GRID) == 0:
                    grid_error = True
                    break
            if grid_error:
                self.bad_grid.append(graph)

        # Check that courtyard is correct width
        if self.bad_width:
            self.error(
                "Courtyard width error (expected width = {w}mm)".format(
                    w=KLC_CRTYD_WIDTH
                )
            )
            for bad in self.bad_width:
                self.errorExtra(graphItemString(bad, layer=True, width=True))

        # Check that courtyard items are on correct grid
        if self.bad_grid:
            self.error(
                "Courtyard lines are not on {grid}mm grid".format(grid=KLC_CRTYD_GRID)
            )
            for bad in self.bad_grid:
                self.errorExtra(graphItemString(bad, layer=True, width=False))

        # Check that courtyard is closed
        if self.unconnected:
            self.error("Courtyard must be closed.")
            self.errorExtra("The following lines have unconnected endpoints")
            for bad in self.unconnected:
                self.errorExtra(graphItemString(bad, layer=True, width=False))

        return bool(self.bad_width or self.bad_grid or self.unconnected)

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """
        if self.bad_width:
            self.info("Fixing line width of courtyard items")
        for graph in self.bad_width:
            graph["width"] = KLC_CRTYD_WIDTH

        if self.bad_grid:
            self.info("Fixing grid alignment of courtyard items")
        for item in self.bad_grid:
            if "center" in item:  # Circle
                key = "center"
            else:  # Lines, Arcs
                key = "start"

            item[key]["x"] = mapToGrid(item[key]["x"], KLC_CRTYD_GRID)
            item[key]["y"] = mapToGrid(item[key]["y"], KLC_CRTYD_GRID)

            item["end"]["x"] = mapToGrid(item["end"]["x"], KLC_CRTYD_GRID)
            item["end"]["y"] = mapToGrid(item["end"]["y"], KLC_CRTYD_GRID)

        # create courtyard if does not exists
        if not self.fCourtyard and not self.bCourtyard:
            self.info("No courtyard detected - adding default courtyard")
            cy = self.defaultCourtyard()
            if not cy:
                self.info("Could not add courtyard - no footprint items found")
            else:
                self.module.addRectangle(
                    [cy["x"], cy["y"]],
                    [cy["x"] + cy["width"], cy["y"] + cy["height"]],
                    "F.CrtYd",
                    KLC_CRTYD_WIDTH,
                )
