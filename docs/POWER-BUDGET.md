# Preliminary 5 V current budget

Estimated 2026-10-23 for the owned original MOS 6502/6522 parts at 1 MHz. This is a planning estimate, not a measurement or a guaranteed maximum. Unknown exact SRAM variant, glue/reset circuit, LCD/backlight, actual cable, port loads and chip condition prevent a closed worst-case calculation.

## Expected serial-only draw

| Item | Working estimate | Conservative allocation | Basis |
| --- | --- | --- | --- |
| MOS 6502 | 70 mA | 160 mA | MOS 1982 catalogue 6500-family electrical table: ICC 70 mA typical, 160 mA maximum |
| Two MOS 6522 VIAs | 150 mA combined (assume 75 mA each) | 400 mA combined | Working typical figure is an engineering allowance, not a MOS guaranteed typical. Catalogue specifies up to 1 W dissipation per VIA; 1 W / 5 V = 200 mA equivalent per-device allowance |
| HM62256 SRAM | 10 mA | 50 mA | Provisional allowance for unknown exact suffix/operating conditions; not a verified maximum for owned chip |
| W27C512-45Z | 15 mA | 30 mA | Working average allowance; Winbond specifies up to 30 mA read current |
| Purchased active oscillator | 17 mA | 25 mA | Supplied ECS-2100 reference, not independently identified actual module |
| Decoder, glue, reset | 15 mA | 30 mA | Provisional package/family allowance; LS138 alone specifies 6.3 mA typical, 10 mA maximum |
| FT232 interface in cable | 15 mA | 25 mA | Converter/interface allowance; actual cable design unspecified |
| Pull-ups / small status LED allowance | 5 mA | 10 mA | No substantial expansion or display loads included |
| **Total** | **297 mA** | **730 mA** | Arithmetic sum; the latter mixes limits and allowances and is not a certified worst-case bound |

Use **about 300 mA**, with a plausible **250–350 mA** range, as the initial serial-only expectation including the USB converter. Round the conservative planning allocation to **750 mA**. Original NMOS CPU/VIAs dominate; modern CMOS 6502/6522 current figures are not appropriate here. RAM/ROM duty cycles and actual port configurations affect averages.

The VIA allowance intentionally treats the catalogue dissipation ceiling conservatively; it is not a claim that each VIA normally draws 200 mA or that 1 W is a specified constant supply draw. Port loads and external-device power must be accounted for without double counting.

## Display and keyboard additions

- **LCD2004 plus backpack/backlight:** initially allow **60–170 mA expected**, **200 mA conservative** until the actual module is identified. Backlight dominates and varies by module. These are engineering allowances, not specifications for an identified LCD.
- **One bank digit and driver:** **10–30 mA expected**, **35 mA conservative**, assuming modest LED brightness/current. Seven illuminated segments are the sizing condition even if banks 0–3 usually light fewer. Final resistor/current choices and driver limits must agree.
- **Bare passive keyboard matrix:** no powered controller is assumed. Scan/pull-network current belongs in the VIA/interface budget; any adapter, indicators or powered keyboard electronics need an additional explicit allocation.
- **External expansion loads:** excluded; budget separately and do not promise full USB current on every header.

With both displays, working estimate becomes **roughly 400–500 mA** (approximately **320–550 mA** using the stated input ranges). Conservative allocation is **965 mA**, rounded to **about 1 A**, before unrestricted expansion loads. Backlight choice or lower segment currents can reduce this substantially.

## Power-path recommendation

For selecting hardware now, prefer a regulated **5 V supply rated 2 A** and a board power path/cable output explicitly rated **at least 1 A continuous**. The supply rating is available capacity, not current forced through the board. This provides a useful source margin while exact parts and measured loads are pending; it is a recommendation, not a newly accepted power architecture or automatic justification for 2 A through the serial cable.

The user's prior **500 mA total USB budget** may cover expected serial-only draw, but cannot be treated as a conservative full-board/display guarantee. A 1 A/2 A USB brick does not increase a serial cable's permitted output current. FTDI's own similar TTL-232R-5V cable has a 75 mA rating and is not suitable for this estimate; the user's actual FT232RL cable model is not identified. If that cable cannot carry the required board current, preserve its serial function and design a separate adequately rated USB power route with cable VCC isolation. Do not simply parallel supplies.

A standard PC USB 2.0 connection does not become a 1 A source by selecting a larger wire or changing a current-budget assumption. Host enumeration/power states remain relevant. If PC-powered operation is required within 500 mA, measure and constrain the complete configured load, including displays, and implement an appropriate input arrangement; otherwise use a suitable separately rated power source. The architecture choice remains with the user.

Measure voltage **at the board** under load: the purchased oscillator reference expects 4.75–5.25 V, and the six-foot serial/power cable can cause voltage drop. Size source, connectors and wiring for current as well as the required delivered voltage. Reset/startup, bulk-capacitor inrush and short-circuit protection are separate checks.

## Evidence and next verification

- [MOS/Commodore 1982 data catalogue](https://bitsavers.trailing-edge.com/components/mosTechnology/_dataBooks/1982_MOS_Technology_Data_Catalog.pdf), printed p. 2-16 (PDF p. 27): 6500-family ICC; printed p. 2-63 (PDF p. 74): MOS 6522 power dissipation. This is manufacturer literature, not a CMOS substitute. Downloaded text was checked for these entries.
- [Winbond W27C512](https://media.digikey.com/pdf/Data%20Sheets/Winbond%20PDFs/W27C512.pdf): 30 mA maximum read current.
- [TI LS138](https://www.ti.com/lit/ds/symlink/sn74ls138.pdf): decoder supply current; final glue families/counts still pending.
- [Supplied oscillator sheet](hardware/datasheets/ecs-2100-supplied.pdf): 17 mA typical /25 mA maximum in the 1–25 MHz range.
- [FTDI cable reference](https://ftdichip.com/products/ttl-232r-5v/) and [FT232R power guidance](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232R.pdf): cable-specific capability and USB power states.

Next: identify RAM/LCD variants and final glue/reset parts, then measure CPU+memory, add each VIA, add displays, and record idle/active current and board voltage. No hardware measurements or power-integrity validation have been performed.

User direction after review: **defer power-input options to actual PCB design**. Current estimates remain sizing inputs, not an immediate request to buy a different supply/cable or select power-switching circuitry. Final connector/source-selection/protection choices remain open until that work.

Additional proposed load: SPI SD card/module, not included in the estimates above. Exact module/card and peak current remain unselected; add a separate measured/datasheet allocation before final PCB power design.
