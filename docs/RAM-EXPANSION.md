# Optional extra RAM

Status: deferred option, 2026-10-24. The user accepts the eight-2-KB-slot decoder concept while explicitly keeping additional RAM optional. No second SRAM/6116, extra socket or RAM emulation is added now. The implemented [map](ADDRESS-DECODING.md) remains 32 KB RAM + 16 KB slot space + 16 KB banked ROM.

Six unpopulated 2 KB windows at `$8000–$AFFF` are available for later memory or I/O. VIA1 uses `$B000–$B7FF` and VIA2 uses `$B800–$BFFF`. Filling all six spare slots with RAM could provide **44 KB total RAM** under this decode; no such population is currently selected.

A 6116-sized device could occupy one slot. A larger spare SRAM could use multiple contiguous slots with appropriate select combining, leaving part of that chip unused. Select actual devices and derive chip-enable/read/write connections before fitting them; ensure no RAM response in either VIA window. J2 exposes selects and power only, not a full CPU expansion bus.

If BASIC should use a larger contiguous RAM region, first relocate the current LCD workspace at `$7F80–$7FFF` to the chosen new RAM top, then update BASIC's limit, loader protection, diagnostics and tests. Hardware expansion alone does not make the current BASIC allocator use the extra space.

The earlier discussion of 47 KB RAM with two 512-byte VIA windows and a second LS138 is **not the selected design**. Revisit finer decoding only as a separate accepted revision. See [MACHINE.md](MACHINE.md) for the implemented contract and [ADDRESS-DECODING.md](ADDRESS-DECODING.md) for current pin wiring.

## Inventory check before choosing upgrade sockets

User plan, 2026-10-24: check inventory tomorrow (2026-10-25) for 6116 SRAM. Depending on available parts, consider either fitted 6116 RAM or unpopulated DIP sockets for later upgrades. This is not a request to add sockets now or a scheduled reminder.

Record exact part markings, quantities and package dimensions before selecting footprints. One compatible 2 KB 6116 can occupy one spare LS138 slot; at most six such slots are available under the current map. Socket count/location, bypass positions, chip-select/read/write wiring and installed-memory policy need to be designed before reserving a final expansion area. Do not assume an empty socket's physical data-bus reads are guaranteed `$FF` just because the current emulator uses that value for unpopulated slots.

Keep baseline RAM at 32 KB and current BASIC/loader limits until hardware population and a coordinated software update are explicitly chosen. Unpopulated upgrade sockets, if later selected, still consume PCB space and require normal wiring and bypass provisions. Avoid committing all six sockets before the inventory and fit review.
