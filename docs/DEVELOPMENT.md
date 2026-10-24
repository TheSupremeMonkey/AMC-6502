# Development environment

## Ubuntu prerequisites

Install general-purpose tools through Ubuntu packages:

```sh
sudo apt-get update
sudo apt-get install -y python3 python3-venv build-essential git
```

From the repository root:

```sh
make setup
make test
```

Setup creates `.venv/`, installs the hash-pinned Py65 1.2.0 wheel, and builds ca65/ld65 from cc65 V2.19 at commit `555282497c3ecf8b313d87d5973093af19c35bd5` in `.tools/cc65/`. The V2.19 tag reports `V2.18 - Git 5552824` from both tool version commands; the pinned Git commit identifies the source precisely. Nothing specialized is installed globally. Network access is required for initial setup. Rerunning setup reuses the local checkout and refuses changed source or an unexpected revision. `JOBS=4 make setup` changes build parallelism (default: 2).

The local Python interpreter is `.venv/bin/python`; activation is optional. Never install dependencies into system Python. General package versions follow Ubuntu; project dependencies are pinned in `requirements.txt` and `scripts/setup.sh`.

## Build and verification

- `make test` (or `make smoke`): assemble/link all ROM fixtures and the banked BASIC/Woz image, then run standard-library unittest checks.
- `make rom`: fetch/validate pinned firmware and build the 64 KB image.
- `make run`: build the image and start the terminal; see [FIRMWARE.md](FIRMWARE.md).
- `make clean`: delete `build/`; local tools and Python environment remain.
- `make clean && make test`: rebuild the ROM from scratch.

The build produces an 8 KB ROM, object, assembly listing, linker map, and label file under `build/`. The banked build also produces `build/amc6502.bin`, an exact 64 KB EEPROM image with four identical shared upper halves. Hardware has not been validated.

The smoke ROM initializes CPU state, computes `$40 + $02`, writes `$42` to RAM at `$0200`, and loops. The check boots through the reset vector using Py65's original NMOS 6502 core and runs a bounded 32 instructions. A separate check confirms the assembler rejects CMOS-only `STZ` in 6502 mode.

This is toolchain verification using upstream flat memory, not the AMC memory bus or a complete hardware diagnostic. The separate AMC diagnostic now exercises RAM/ROM protection; the banked image separately exercises banks, both VIA port/timer/IRQ models, and serial pins. Shift-register operation, timed output handshakes, and LCD remain pending. See [VIA.md](VIA.md) for timer/IRQ behavior and tests. NMOS decimal arithmetic, indirect-jump behavior, interrupts, and device timing require dedicated checks as the emulator develops. Undocumented instructions are outside the initial firmware target.

## Classic hardware target

Use ca65 `--cpu 6502` and source `.setcpu "6502"`; use `py65.devices.mpu6502.MPU`. Default firmware and emulation target classic chips, including original NMOS 6502 and classic 6522 VIA behavior. The board clock is fixed at 1 MHz. Modern CPU variants remain a separate experimental option for future explicit configurations. No alternate build/core configuration is implemented. Keep CMOS-only instructions out of baseline firmware and validate variant-specific behavior and whole-system timing before relying on them. Assembler acceptance alone does not prove electrical or timing compatibility.

## References

- [cc65 source and license](https://github.com/cc65/cc65/tree/V2.19)
- [ca65 documentation](https://cc65.github.io/doc/ca65.html)
- [Py65 source and license](https://github.com/mnaberez/py65)
- [Py65 1.2.0 package](https://pypi.org/project/py65/1.2.0/)


## First AMC machine diagnostic

`make test` also builds `firmware/diagnostic.s` into `build/diagnostic.bin`, with listing, map, and labels. `tests/test_machine.py` runs it through `emulator.machine.Machine` for a bounded instruction count. Firmware initializes CPU state, writes/checks RAM at `$0000`, `$0100`, and `$7FFF`, attempts a ROM write, then writes pass marker `$42` to `$0200` (or `$FF` on failure). It loops after completion; no emulator-specific output calls are used.

Tests also check memory-map boundaries, reset-vector boot, IRQ masking on reset, retained RAM, and instruction budgets. This is a spot diagnostic, not an exhaustive RAM test. These legacy diagnostic fixtures deliberately load one 8 KB bank; the main image now uses the accepted four-bank map and terminal described in [FIRMWARE.md](FIRMWARE.md).


## VIA timer/interrupt diagnostic

`make test` builds `build/via-irq.bin` from `firmware/via-irq.s` and its 16 KB linker configuration. Tests replicate it across four banks and verify masked pending interrupts, IRQ entry/acknowledgement from each VIA, repeated T1 events, and reset. This is a separate fixture; the BASIC/Woz image remains the default for `make run`. See [VIA.md](VIA.md).


## Bank 3 diagnostics personality

`make rom` now assembles `firmware/diagnostics.s` into the bank 3 payload. `make run`, then `:bank 4`, runs its RAM and VIA timer/IRQ checks. Enter `R` to rerun. `make test` includes pass/rerun, RAM restoration, and injected-failure coverage. See [DIAGNOSTICS.md](DIAGNOSTICS.md).


## Manual bank controls

Use `:bank 1` through `:bank 4` from any personality to simulate setting external toggles under reset. `:reset` retains the current bank. Software bank switching is retired: `$8020` is an unpopulated expansion address and `$E106` returns carry set. See [ROM switching](ROM-SWITCHING.md).


## Host debugger

`make run` starts the firmware terminal with debugger commands. Use `:help`, `:run`, `:stop`, `:regs`, `:mem`, `:step`, and `:break`. Ctrl-C pauses instead of exiting. `.venv/bin/python -m emulator --paused` starts at the reset vector without executing. See [DEBUGGER.md](DEBUGGER.md) for examples and exact breakpoint/IRQ semantics. No new dependencies or ROM changes are required.


## Shared service API tests

`make test-api` builds the assembled service fixture and banked ROM, then runs focused API integration tests. `make test` includes these checks in the full suite. Include `fw.inc` using `-I firmware/include` for new assembly clients. See [FIRMWARE-API.md](FIRMWARE-API.md) for addresses, register contracts, RAM ownership, and polling limits.

Serial upload: `make test-loader` runs focused firmware transfer tests. `.venv/bin/python scripts/send_hex.py --emulator examples/ram-test.hex` sends the sample to a fresh emulator through modeled serial pins. See [Serial loader](SERIAL-LOADER.md) for persistent terminal and POSIX serial use; no additional Python dependency is needed.

Optional hardware-document tooling: Ubuntu `poppler-utils` was installed to inspect supplied PDF datasheets (`pdftotext`, `pdftoppm`). It is a general-purpose system package, not a firmware build/test dependency. Image-only sheets require rendering for visual inspection.

Optional schematic rendering: Ubuntu `librsvg2-bin` was installed to render the editable reset SVG to PNG with `rsvg-convert`. It is not a ROM build/test dependency.

LCD: `:lcd mirror/dashboard/off` requests a mode, `:lcd` inspects rows. See [LCD.md](LCD.md). Optional KiCad tooling: install Ubuntu `kicad kicad-symbols kicad-footprints`, then run `make schematic-check` for native ERC, PDF and netlist exports. No PCB layout has been created.
