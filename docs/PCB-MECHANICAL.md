# PCB outline and LCD mounting

The LCD and motherboard retain a matching four-hole mounting pattern for stacked mounting. The original LCD-sized motherboard outline is now permitted to grow, especially below the LCD, to fit the socketed-DIP BOM and a lower control panel. Exact dimensions remain provisional until placement and actual LCD measurements are checked. No PCB layout has been created.

## Desktop terminal concept — latest direction

The user prefers a **mostly upright LCD leaning backward**, in a compact 1970s-terminal-inspired printed case. The case may have a wider bezel and an enlarged motherboard, particularly extending below the display. Put the toggles and buttons on a **front control panel below the LCD**. This resolves the earlier upright-versus-low-wedge question; exact lean angle and base depth remain open.

Use the existing controls in that lower panel: two bank toggles, hardware reset button and power switch. Preserve the established meanings and the hold-reset procedure for bank changes. The bank indicator can be considered beside the toggles; this placement is a proposal, not a new requirement. No new controls are introduced.

The case base supports the backward-leaning assembly and provides stability and rear cable space. The LCD and motherboard can remain parallel, with ICs facing the display and peripheral headers facing the rear. Maintain the four long retaining screws, inserts and custom standoffs; a larger board does not require the LCD holes to move. The shared holes may now sit above the motherboard's lower corners. Consider a printed support ledge or saddle for the lower extension so operating controls or plugging cables does not flex a cantilevered PCB.

**Working placement-study envelope: 110 × 90 mm**, with the LCD near the upper center and extra board area below. This is a starting estimate only, not a selected outline. Gross area would be 9,900 mm²; the measured 5,207 mm² of DIP socket courtyards would occupy about 53%, versus 89% in 98 × 60 mm. That is a more promising area budget, but does not establish a routable layout. Board-mounted versus panel-wired controls and their exact footprints remain to choose; the current schematic uses control headers.

Do not fix case dimensions, angle, cutouts, screw lengths or control positions until the component-placement and mechanical stack studies agree.

## Accepted case and board arrangement

The user will design a 3D-printed enclosure around the LCD, with custom standoffs, brass threaded inserts and four long machine screws. Those four screws retain the stacked boards and removable case back. Exact screw diameter/length, insert type/location, spacer heights and clamping details remain mechanical design choices.

Front-to-back stack:

1. Printed front shell / LCD viewing opening.
2. LCD module, with its visible face toward the front.
3. Clearance space for the LCD rear components/backpack and motherboard socketed DIP ICs.
4. Motherboard, with **top/component side facing the LCD** and **bottom side facing the case back**.
5. Bottom-mounted peripheral and serial/power pin headers, facing rearward, with room for mating DuPont connectors and leads.
6. Removable printed case back with connector-access cutouts.

Custom standoffs establish the board spacing at the matching four-hole pattern. The screw load should be supported at the mounting points by the case/spacer stack; display glass and components are not clamp surfaces. Screw entry from the rear into inserts in the front shell is a possible implementation, not yet a specified insert location.

PCB layout must place the CPU, VIAs, memory and socketed logic on the LCD-facing top side, and the three 1×12 buses, 1×8 mini bus and serial/power cable header on the rear-facing bottom side. The schematic specifies electrical pin assignments and header shape; actual top/bottom placement is a PCB-layout operation and is not implemented by the schematic alone.

## Layout and enclosure coordination

- Set the LCD-to-motherboard gap from the actual tallest opposing parts: socketed DIP packages, oscillator, capacitors, LCD backpack/trimmer and soldered header ends. Use a 3D/section review to check overlaps rather than deriving gap from bare board thickness.
- Reserve screw-head, insert and standoff envelopes around all four holes; confirm the chosen screws fit the actual LCD holes. The common module's nominal 2.5 mm holes remain a reference, not a selected screw size.
- Allocate motherboard-to-back clearance for both the bare header and a fully inserted DuPont housing, cable exit and assembly access. Locate cutouts from final bottom-side connector placement.
- Label pin 1, signals, +5 V and GND on the rear-facing silkscreen so connections can be made from outside. Bottom-view pin order is mirrored relative to the top view; retain electrical pad numbers rather than reversing signal assignments to match a drawing.
- Keep underside solder joints and top-side protruding tails of bottom-mounted through-hole headers clear of the LCD assembly. Plan assembly/soldering access and how the motherboard can be removed for ROM servicing.
- Place bank/reset/power controls below the LCD. Serial/power connection and mini bus are explicitly rear-accessible, alongside the three full-port buses. The bank digit location and other internal connector placement remain open.
- External case dimensions include walls and insert bosses; matching the two board outlines does not imply the whole enclosure is exactly 98 × 60 mm.

## Online reference geometry

The [Vishay LCD-020N004A/B datasheet](https://www.vishay.com/doc/?37312=), mechanical table on page 1 and dimension drawing on page 2, specifies:

| Feature | Reference dimension |
| --- | --- |
| PCB outline | 98.0 × 60.0 mm nominal |
| Four-hole center spacing | 93.0 × 55.0 mm |
| Hole-center setback | 2.5 mm from each corresponding edge |
| LCD mounting-hole diameter | 2.5 mm; drawing labels four plated holes |
| LCD mounting-pad diameter | 5.0 mm |
| LCD module depth | 13.6 mm maximum for this reference; does not establish backpack or stack clearance |

[Orient Display AMC2004A-I2C](https://www.orientdisplay.com/wp-content/uploads/2018/08/AMC2004AI2C-Full.pdf), page 10, also documents a 98 × 60 mm module with 93 × 55 mm hole spacing and four 2.5 mm holes. This is a mechanical comparison only, not selection of that module or its I2C controller.

For coordinates relative to the reference LCD board's upper-left corner, X rightward and Y downward (translate this pattern to the chosen motherboard position):

| Hole | X (mm) | Y (mm) |
| --- | --- | --- |
| Upper left | 2.5 | 2.5 |
| Upper right | 95.5 | 2.5 |
| Lower left | 2.5 | 57.5 |
| Lower right | 95.5 | 57.5 |

These coordinates are derived from the reference drawing; they are not measurements of the user's display. The 98 × 60 mm rectangle describes the reference LCD board; an enlarged motherboard uses its own outline while retaining the LCD-relative hole pattern. Do not treat these figures as a universal LCD2004 standard: the part name specifies character format, not one guaranteed mechanical design.

## Before freezing the board

- Confirm the exact purchased LCD outline, hole centers and diameters against its drawing or physical measurements.
- Choose mounting screws, spacer height and motherboard hole/pad/keepout details to match the actual assembly; the reference's 2.5 mm LCD holes do not establish clearance for larger screws.
- Check the LCD's rear components, I2C backpack, contrast trimmer, solder pins and connector/cable exit against the motherboard's DIP sockets and ICs. Include assembly tolerances and access to the ROM socket.
- Verify component placement and routing fit in this envelope; accepted dimensions are a target, not a demonstrated completed layout.
- Keep the separate LCD bring-up task to verify its actual 7-bit I2C address and backpack pin mapping. Mechanical similarity does not establish electrical compatibility.

The reference LCD hole plating is not an instruction to connect motherboard mounting holes to ground. Final motherboard plating, copper clearance and fastener details remain PCB decisions.

## Preliminary component fit

The socketed-DIP footprint assessment is crowded: ten IC courtyards total about 89% of the 98 × 60 mm gross area before passives, oscillator, routing and mounting clearance. See [PCB-FIT.md](PCB-FIT.md). Do not freeze the case dimensions until a placement trial establishes feasibility; an enlarged motherboard is now an allowed concept, with exact dimensions pending.

## Rear connection assignment

Accepted 2026-10-24: **serial connection and mini bus must be on the back**, alongside I/O 1–3. The serial interface remains the selected FT232RL cable/header, not a newly selected onboard USB connector. Plan serial/power J11 on the rear-facing motherboard side; its actual cable pin order and power-path circuitry remain open. J9 mini and J6–J8 full ports retain their selected single-row footprints and electrical pin numbering.

Provide rear-cover cutouts and mating/cable clearance for all five connection groups. Final spacing, orientation and cutout dimensions follow placement and actual connector/cable measurements. Internal LCD wiring stays inside the enclosure. This rear-placement requirement is not implemented physical placement until a PCB layout exists.
