# KiCad Sim-Panel Library

Welcome to the KiCad Sim-Panel Library repository! This collection is dedicated to providing KiCad symbols, footprints, and 3D models tailored to the unique requirements of Sim-Panel PCBs. These resources will simplify the process of designing and building your custom Sim-Panel PCBs.

We aim to achieve compliance with the [KiCad Library Convention (KLC)](https://klc.kicad.org/) with all our components, with the exception of:
 - F9.3, since 3D Model paths are allowed to: 
   - start with `${KICAD_SIMPANEL_DIR}/` in lieu of `${KICAD7_3DMODEL_DIR}/` since they are intended for local use
   - be in a STEP format (either WRL or STEP are acceptable)

## What's Inside

### KiCad Symbols

This repository features a wide array of KiCad symbols representing electrical components commonly used in Sim-Panel PCB construction. Symbols are schematic depictions of electronic components and are essential for circuit design. They allow you to create circuit diagrams that serve as a blueprint for assembling the physical PCB. Each symbol is tailored to the specifications of real-world components, enabling you to quickly choose the appropriate components for your project.

### KiCad Footprints

Footprints are vital for the PCB design process. They are patterns of pads, holes, or lands on the PCB where an electrical component will be soldered. Our library offers an extensive collection of footprints compatible with various electronic components typically used in Sim-Panel PCBs. Each footprint is meticulously designed to match the physical dimensions and pin configurations of the corresponding components.

### 3D Models

3D models provide a visual representation of electronic components on a PCB. They are invaluable for verifying component placement, assessing clearance and fit, and creating realistic visualizations of the final assembled PCB. In this repository, we furnish detailed 3D models for the components corresponding to the provided symbols and footprints.

## How to Use

### Configure Environment Variables
1. Clone this repository to your local machine.
2. In KiCad, go to "Preferences" and select "Configure Paths"
3. Add a new environment variable with the name `KICAD_SIMPANEL_DIR` and the path to this cloned repository on your local machine.

![image](https://github.com/ssewell/kicad-sim-panel-components/assets/2242776/5b1cd322-5240-435d-997c-46c8f860d4ab)

### Configure Symbols
1. In KiCad, go to "Preferences" and select "Manage Symbol Libraries..."
2. Add a new table entry with the Nickname `SimPanel` and the Library Path `${KICAD_SIMPANEL_DIR}/SimPanel.kicad_sym`

![image](https://github.com/ssewell/kicad-sim-panel-components/assets/2242776/fd8bc72e-2a8e-4e66-960a-6bbab8f1458d)

### Configure Footprints
1. In KiCad, go to "Preferences" and select "Manage Footprint Libraries..."
2. Add a new table entry with the Nickname `SimPanel` and the Library Path `${KICAD_SIMPANEL_DIR}/SimPanel.pretty`
![image](https://github.com/ssewell/kicad-sim-panel-components/assets/2242776/39850925-3402-4985-887c-303fcb2e6237)

Once added, you can access these resources from within KiCad as you design your Sim-Panel PCBs.

## Contribution

We encourage contributions from the community to enhance and expand this library. If you've created symbols, footprints, or 3D models that could be beneficial for Sim-Panel PCBs, please open a pull request or contact us to discuss adding them to the repository.

## License

This repository is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/).