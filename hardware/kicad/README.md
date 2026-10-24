# AMC-6502 native KiCad draft

Open `AMC-6502.kicad_pro` in KiCad 9. All ICs use DIP/socket footprints. No PCB layout is included. See [the schematic guide](../../docs/SCHEMATIC.md) for circuit details, open decisions and validation limits.

Run `make schematic-check` from the repository root to export PDF/netlist and run ERC. Project-local symbols are in `AMC.kicad_sym`; adapted standard symbols retain the license and schematic exception in `KICAD-LIBRARY-LICENSE.txt`.

Next layout study: 110 × 90 mm working envelope, retain LCD-relative holes, ICs facing LCD and all external buses/serial toward the rear. Lower front-panel controls and printed-case stack are in [PCB-MECHANICAL.md](../../docs/PCB-MECHANICAL.md). This is not a frozen outline or completed placement.
