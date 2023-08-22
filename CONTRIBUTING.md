## Symbol Naming Strategy

If the component has an LCSC part number available, include a field in the symbol that uses the Name `LCSC Part #` and indicate corresponding part number in the corresponding value.

### Fully Specified Symbols

Fully specified symbols should be named after the NPM (manufacturer part number) and include the full part number (for atomic components) or a partial part number (for fully specified symbols, e.g. has multiple variants and are _not_ atomic).

### Component Variants

If a component has multiple variants that use the same symbol, create the common symbol first, using a naming convention that generalizes the part number, then create dervied symbols that are named after the full part number.

Often, generalizing the part number can be achieved by simply including a subset of the name (starting with the first character). For example, derived parts TL6275AA2PQNY and TL6275BA2PQNY both share the same parent part, named TL6275, from which they are derived. This shorted name used for parent symbol, will often match the "series" naming convention used by the manufacturer.

Alternatively, lower cases "x" characters can be used in as placeholders in the parent symbol if an appropriate substring isn't readily available. e.g. A parent symbol could be named ABC-1X55 if has the derived parts of ABC-1055, ABC-1155, ABC-1255, etc.

### Datasheets

Datasheet references in symbols should point to the manufacturer's URL, if available.

In some instances, parts are purchased from a vendor that provides little information regarding the original manufacturer and will provide their own version of the component datasheet. In these instances, the datasheet file should be added to the `/datasheets` folder in this repo and reference the datasheet in the symbol using the `{KICAD_SIMPANEL_DIR}/` prefix.

## Footprint Requirements

See the [KiCad Library Convention (KLC)](https://klc.kicad.org/), noting the KLC Compliance Check Modifications listed below.

## Submitting Changes

Changes to this library can be requested by creating a pull request.

Prior to creating a pull request, please execute the modified KLC Compliance Checks (included in this repository) in your local environment. Additional details on how to execute these checks are described below.

When creating a pull request, GitHub will excecute the modified KLC Compliance Checks. If any checks produce a error of warning, the GitHub action will indicate failure.

## KLC Compliance Checks

Python scripts are included in this repository to check symbols and footprints for complaince with a modified version the KiCad Library Converion (KLC).

A few checks are modified or disabled, typically because they conflict with a strategy implemented by the components in this repo. A full listing of the KLC rule exclusions and their reasoning is listed below.

### KLC Compliance Check Modifications

| Rule | Subsection | Type (Modified/Excluded) | Rationale                                                                                                                                                                                                                 |
| ---- | ---------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F9.3 | 7          | Modified                 | Model paths must start with `${KICAD_SIMPANEL_DIR}/` in lieu of `${KICAD7_3DMODEL_DIR}/` since they are intended for local use                                                                                            |
| F9.3 | 8          | Modified                 | 3D model file type can be in either `.wrl` or `.step`. Unlike the standard KLC, which requires `.wrl`, the `.step` format can be used exclusively as the `AP214 STEP` format includes both geometry and color infomation. |
| S6.2 | 4          | Modified                 | Since derived symbols inherit fields unless overridden, it is acceptable to populate a common datasheet in the parent symbol and leave derived symbols empty                                                              |

## Executing KLC Compliance Checks

### Prerequisites

- python3
- VS Code (optional)

### Using VS Code

- Open the project folder
- Open the Command Pallete (`Ctrl`+`Shift`+`P` or `F1`)
- Select `Tasks: Run Tasks`
- Select `KLC - Check All`

### Using Python

In your terminal:

- Change directory to the root of your local instance of this repo.
- To execute the symbol check, run:

```shell
python .\library-utils\klc-check\check_symbol.py .\SimPanel.kicad_sym -vv
```

- To execute the footprint check, run:

```shell
python .\library-utils\klc-check\check_footprint.py .\SimPanel.pretty\\* -vv
```

