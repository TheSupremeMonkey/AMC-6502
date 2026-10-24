# Preliminary fit assessment: 98 × 60 mm

Assessment: the full current socketed-DIP BOM is too crowded for confidence in a 98 × 60 mm motherboard with all ICs on the LCD-facing top side. The user subsequently allowed a larger motherboard/bezel; 110 × 90 mm is now the working placement-study envelope. This historical 98 × 60 mm measurement explains that revision. DIP construction remains required.

## Measured footprint envelopes

Measured from the installed standard KiCad footprint library using `pcbnew.FootprintLoad`, taking the bounding rectangle of each footprint's F.CrtYd geometry. Source components/footprints are the exported `build/schematic/AMC-6502.xml` netlist. Dimensions include courtyard stroke and are rounded here. This is a conservative envelope/area estimate, not physical placement or routed-board verification; exact purchased socket dimensions may differ.

| Item | Quantity | Courtyard per item (mm) | Combined area (mm², approximate) |
| --- | --- | --- | --- |
| DIP40 socket: CPU + two VIAs | 3 | 18.35 × 51.48 | 2,834 |
| Wide DIP28 socket: RAM + ROM | 2 | 18.35 × 36.25 | 1,330 |
| DIP14 socket: LS21, LS00, HC14 | 3 | 10.71 × 18.46 | 593 |
| DIP16 socket: LS138 + optional HC4511 | 2 | 10.71 × 20.99 | 450 |
| Active oscillator | 1 | 13.25 × 13.25 | 176 |
| Main 1×12 header | 3 | 3.59 × 31.53 | 340 |
| Mini 1×8 header | 1 | 3.59 × 21.37 | 77 |

Gross board area: **5,880 mm²**.

- All ten socketed DIP ICs: **5,207 mm²**, about **89%** of gross area.
- Nine socketed ICs excluding optional bank-display driver: **4,982 mm²**, about **85%**.
- ICs plus all other non-header components in the current draft: **6,406 mm²**, about **109%**. This assumes those parts occupy separate top-side envelopes.
- Every current footprint including headers: **7,363 mm²**. This is a count of all component envelopes, not a valid one-side occupancy percentage when connectors mount underneath.

No allowance in these percentages is subtracted for four screw/standoff keepouts, board-edge margins, routing channels or the LCD backpack's opposing component envelope. Several current headers/passives are optional or draft review provisions; the total is a snapshot of the schematic, not a finalized purchasing BOM.

## Interpretation and options

Rear-mounted headers avoid putting their housings on the top, but their plated through-hole pads and solder tails still constrain the IC-side layout. Some small passives could potentially move underneath if their pads, mating cables and back-cover clearance permit it; the current area calculation does not prove that such a two-sided placement fits. More copper layers improve routing freedom but do not reduce socket size.

The current full BOM should not be called a comfortable fit in 98 × 60 mm. A trial placement with actual socket envelopes, all four mounting keepouts and bottom connectors is the next decision gate. The user has chosen to explore a larger motherboard and bezel while retaining the LCD hole pattern. Offloading the optional bank-display circuitry helps but leaves the core socketed ICs occupying about 85% of gross area.

No component placement, routing, enclosure CAD or mechanical interference check was completed by this assessment. Keep the chosen DIP chips, single-row DuPont headers and case stack; trial-place the larger working envelope before fixing the outline.

## Revised enclosure concept

The user permits exploring a larger motherboard and bezel, particularly an extension below the LCD. The display is mostly upright and leans backward; toggles/buttons go below it. The shared LCD mounting-hole pattern and four-screw case assembly remain the direction. The **110 × 90 mm working** placement envelope provides 9,900 mm², reducing IC-courtyard occupancy to approximately 53% and IC-plus-non-header occupancy to approximately 65%. These are area estimates, not validated placement/routing. No exact new outline is selected. See [PCB-MECHANICAL.md](PCB-MECHANICAL.md).

Decoder revision note (2026-10-24): IC/socket counts are unchanged; internal J2 grew from 1×3 to 1×8 to expose six spare 2 KB select signals and rails. Recomputed total of all footprint envelopes is approximately 7,363 mm², while IC-only and non-header figures above remain unchanged. Rear connector/routing clearance still requires actual placement.
