# Optional keyboard planning

Status: candidate selection and firmware proposal, not a finalized pinout or implemented driver.

## Available keyboards

The user has an Oric Atmos keyboard, multiple Commodore 64 keyboards, and two TRS-80 Color Computer chicklet keyboards. The Atmos is the preferred candidate for its distinctive appearance and key feel; this is a preference, not a final hardware commitment.

## Optional ownership

Accepted direction: budget two full VIA ports for the keyboard, leaving one full expansion port beside the system-control port. Support Cyberdeck and Controller profiles, selected at reset; Controller releases keyboard ports to the application. Implementation and physical wiring are deferred. See [OPERATING-PROFILES.md](OPERATING-PROFILES.md) for the plan.

Keyboard scanning should be optional so controller applications can reclaim its PIO resources. LCD availability is independent: I2C uses the proposed VIA #1 Port A pins and need not be disabled when keyboard input is off.

Proposed firmware behavior: a bank requests its console/input profile; an external switch may override at reset. When the keyboard is disabled, firmware leaves its pins as inputs initially and does not scan or reconfigure them. The application owns subsequent configuration. The exact switch interface, bank metadata extension, and acquire/release API are not implemented or finalized. Reclaiming pins in firmware does not electrically disconnect an attached keyboard/adapter; expansion sharing also requires suitable disconnection/isolation in the physical design.

## Oric interface implications

The Atmos keyboard is a scanned matrix, not a ready-made ASCII serial keyboard. Its original interface includes a 4051 row multiplexer; original-machine column drive and row selection/sensing span more than one 8-bit port. Do not assume the complete keyboard plugs directly into the proposed VIA #1 Port B allocation.

Options to assess are a direct multi-port connection or a small keyboard adapter presenting fewer control lines. Keep the character-input API independent of the matrix and pin allocation. Verify the actual assembly, connector, matrix, and fitted electronics before choosing lines or promising a single-port interface. An emulator keyboard model can then reproduce that selected interface and key mapping.

References: [Oric/Atmos service manual](https://library.defence-force.org/books/content/service_manual_for_the_oric1_and_oric_atmos_microcomputers.pdf), [hardware investigation of the Oric keyboard interface](https://www.kernelcrash.com/blog/an-oric-wth-a-ps2-keyboard/2016/09/03/).
