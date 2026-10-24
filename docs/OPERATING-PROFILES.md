# Operating profiles

Accepted planning direction: 2026-10-23. Profiles are not implemented yet; switch wiring and keyboard integration are deferred.

## One board, two uses

AMC-6502 should be easy to reconfigure between a standalone cyberdeck and an embedded controller, including quick changes for experiments. A common ROM image can support both profiles. Separate specialized controller ROM images remain an option.

| Profile | Console | Keyboard resources | LCD |
| --- | --- | --- | --- |
| Cyberdeck | Keyboard input and LCD output | Reserve two full VIA ports for keyboard support | Main text display; dashboard as appropriate |
| Controller | Serial input/output | Release both keyboard ports to the application | Independently available as an optional dashboard |

The two-port keyboard budget leaves one full 8-bit VIA expansion port available in cyberdeck mode, in addition to the partially allocated system-control port. Exact keyboard port assignments and the Atmos interface are not finalized. See [KEYBOARD.md](KEYBOARD.md).

## Selection at reset

Plan a mechanical Cyberdeck/Controller jumper or DIP setting, read by firmware during startup. Changing a setting takes effect on reset; firmware must not suddenly scan pins while a running controller application owns them.

The firmware should consume an abstract configuration value rather than embed the physical switch wiring throughout its drivers. A spare VIA input, an appropriate control input, or an external configuration register can supply it; no pin or register address is selected yet. A firmware-readable mechanical setting needs an input path, but does not inherently require sacrificing a full parallel-port bit if another suitable interface is used.

A possible later extension is **Auto / Cyberdeck / Controller**: Auto selects the active bank's preferred profile, while the explicit settings override it. Reserve this concept in planning; the three-position selector and bank preference metadata format are not finalized requirements. Existing `$FFC0–$FFDF` metadata contains descriptions only and is unchanged by this plan.

## Firmware responsibilities

At startup, firmware should:

1. Read the profile configuration and check that the active personality supports it.
2. Establish explicit peripheral/port ownership before enabling drivers.
3. Route shared console calls to serial or keyboard/LCD as appropriate.
4. Optionally show the selected profile in the banner/dashboard.

In cyberdeck mode, reserve the keyboard's two ports and initialize scanning. In controller mode, leave those ports as inputs initially and do not scan them, change their output latches/directions, or claim their associated resources afterward; the application controls configuration. The precise timer/control-line budget must be defined with the keyboard driver. LCD/I2C availability must remain independent of keyboard enablement.

Banks should declare supported profiles before profile-dependent drivers are enabled. Preferred-profile declarations are useful for the proposed Auto mode. Exact capability representation and behavior for an unsupported bank/profile combination remain open; do not silently enable a keyboard over controller-owned pins.

## Physical connection versus firmware ownership

Disabling scanning releases firmware ownership, not the electrical keyboard wiring. Reusing keyboard pins for another attached peripheral still needs a suitable disconnect or isolation arrangement. The mode jumper is a configuration input, not a switch that disconnects the entire keyboard matrix. Physical arrangements are deferred with keyboard implementation.

## Current implementation and next steps

Today all personalities use the serial console; neither profiles, LCD, nor keyboard scanning are implemented. The bank selector at `$8020` and software vector `$E106` continue to select/reset ROM personalities independently of this future profile setting.

Before implementation, choose the keyboard interface/port assignments, profile-input mechanism, resource budget, supported-profile representation, unsupported-combination behavior, and any electrical isolation. Then add emulator configuration and tests proving that controller mode leaves the reclaimed keyboard ports untouched by firmware.

Physical expansion reservation now provides I/O 1 (VIA1 PB plus its four control lines), I/O 2 (VIA2 PA+CA), and I/O 3 (VIA2 PB+CB), each with +5 V/GND. Exact keyboard choice of two of these ports is still open; providing the headers does not authorize scanning or assigning them by default. See [PINOUT.md](PINOUT.md).
