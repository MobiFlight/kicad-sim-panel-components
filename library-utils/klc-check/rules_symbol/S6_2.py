import re

from rulebase import isValidName
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Symbol fields and metadata filled out as required"""

    def checkReference(self) -> bool:
        fail = False
        ref = self.component.get_property("Reference")
        if not ref:
            self.error("Component is missing Reference field")
            # can not do other checks, return
            return True

        if (not self.component.is_graphic_symbol()) and (
            not self.component.is_power_symbol()
        ):
            if ref.effects.is_hidden:
                self.error("Reference field must be VISIBLE")
                fail = True
        else:
            if not ref.effects.is_hidden:
                self.error(
                    "Reference field must be INVISIBLE in graphic symbols or"
                    " power-symbols"
                )
                fail = True

        return fail

    def checkValue(self) -> bool:
        fail = False

        prop = self.component.get_property("Value")
        if not prop:
            self.error("Component is missing Value field")
            # can not do other checks, return
            return True
        name = prop.value

        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]

        if (not self.component.is_graphic_symbol()) and (
            not self.component.is_power_symbol()
        ):
            if not name == self.component.name:
                self.error(
                    "Value {val} does not match component name.".format(val=name)
                )
                fail = True
            # name field must be visible!
            if prop.effects.is_hidden:
                self.error("Value field must be VISIBLE")
                fail = True
        else:
            if (not ("~" + name) == self.component.name) and (
                not name == self.component.name
            ):
                self.error(
                    "Value {val} does not match component name.".format(val=name)
                )
                fail = True

        if not isValidName(
            self.component.name,
            self.component.is_graphic_symbol(),
            self.component.is_power_symbol(),
        ):
            self.error(
                "Symbol name '{val}' contains invalid characters as per KLC 1.7".format(
                    val=self.component.name
                )
            )
            fail = True

        return fail

    def checkFootprint(self) -> bool:
        # Footprint field must be invisible
        fail = False

        prop = self.component.get_property("Footprint")
        if not prop:
            self.error("Component is missing Footprint field")
            # can not do other checks, return
            return True

        if not prop.effects.is_hidden:
            self.error("Footprint field must be INVISIBLE")
            fail = True

        return fail

    def checkDatasheet(self) -> bool:
        # Datasheet field must be invisible
        fail = False

        ds = self.component.get_property("Datasheet")
        if not ds:
            self.error("Component is missing Datasheet field")
            # can not do other checks, return
            return True

        if not ds.effects.is_hidden:
            self.error("Datasheet field must be INVISIBLE")
            fail = True

        # more checks for non power or non graphics symbol
        if (not self.component.is_graphic_symbol()) and (
            not self.component.is_power_symbol()
        ):
            # Datasheet field must not be empty
            if ds.value == "":
                self.error("Datasheet field must not be EMPTY")
                fail = True
            if ds.value and len(ds.value) > 2:
                link = False
                links = ["http", "www", "ftp"]
                if any([ds.value.startswith(i) for i in links]):
                    link = True
                elif ds.value.endswith(".pdf") or ".htm" in ds.value:
                    link = True

                if not link:
                    self.warning(
                        "Datasheet entry '{ds}' does not look like a URL".format(
                            ds=ds.value
                        )
                    )
                    fail = True

        return fail

    def checkDescription(self) -> bool:
        dsc = self.component.get_property("ki_description")
        if not dsc:
            # can not do other checks, return
            if self.component.is_power_symbol():
                return True
            else:
                self.error("Missing Description field on 'Properties' tab")
                return True

        # Symbol name should not appear in the description
        desc = dsc.value
        if self.component.name.lower() in desc.lower():
            self.warning("Symbol name should not be included in description")

        return False

    def checkKeywords(self) -> bool:
        dsc = self.component.get_property("ki_keywords")
        if not dsc:
            # can not do other checks, return
            if self.component.is_power_symbol():
                return True
            else:
                self.error("Missing Keywords field on 'Properties' tab")
                return True
        else:
            # find special chars.
            # A dot followed by a non-word char is also considered a violation.
            # This allows 3.3V but prevents 'foobar. buzz'
            forbidden_matches = re.findall(r"\.\W|\.$|[,:;?!<>]", dsc.value)
            if forbidden_matches:
                self.error(
                    "Symbol keywords contain forbidden characters: {}".format(
                        forbidden_matches
                    )
                )
                return True

        return False

    def check(self) -> bool:
        # Check for extra fields. How? TODO
        extraFields = False

        return any(
            [
                self.checkReference(),
                self.checkValue(),
                self.checkFootprint(),
                self.checkDatasheet(),
                self.checkDescription(),
                self.checkKeywords(),
                extraFields,
            ]
        )

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """
        self.info("not supported")
        self.recheck()
