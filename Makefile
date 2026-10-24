.PHONY: setup smoke test clean rom fetch-firmware run test-api

setup:
	bash scripts/setup.sh

build/toolchain-smoke.o: firmware/toolchain-smoke.s
	mkdir -p build
	.tools/cc65/bin/ca65 --cpu 6502 -g -l build/toolchain-smoke.lst -o $@ $<

build/toolchain-smoke.bin: build/toolchain-smoke.o firmware/toolchain-smoke.cfg
	.tools/cc65/bin/ld65 -C firmware/toolchain-smoke.cfg -m build/toolchain-smoke.map -Ln build/toolchain-smoke.lbl -o $@ $<

build/diagnostic.o: firmware/diagnostic.s
	mkdir -p build
	.tools/cc65/bin/ca65 --cpu 6502 -g -l build/diagnostic.lst -o $@ $<

build/diagnostic.bin: build/diagnostic.o firmware/toolchain-smoke.cfg
	.tools/cc65/bin/ld65 -C firmware/toolchain-smoke.cfg -m build/diagnostic.map -Ln build/diagnostic.lbl -o $@ $<

build/via-irq.o: firmware/via-irq.s firmware/include/hardware.inc
	mkdir -p build
	.tools/cc65/bin/ca65 --cpu 6502 -I firmware/include -g -l build/via-irq.lst -o $@ $<

build/via-irq.bin: build/via-irq.o firmware/via-irq.cfg
	.tools/cc65/bin/ld65 -C firmware/via-irq.cfg -m build/via-irq.map -o $@ $<

build/abi-test.o: firmware/abi-test.s firmware/include/fw.inc firmware/include/hardware.inc
	mkdir -p build
	.tools/cc65/bin/ca65 --cpu 6502 -I firmware/include -g -l build/abi-test.lst -o $@ $<

build/abi-test.bin: build/abi-test.o firmware/payload.cfg
	.tools/cc65/bin/ld65 -C firmware/payload.cfg -m build/abi-test.map -o $@ $<

smoke: build/toolchain-smoke.bin build/diagnostic.bin build/via-irq.bin build/abi-test.bin rom
	.venv/bin/python -m unittest discover -s tests -v

test: smoke

clean:
	rm -rf build

fetch-firmware:
	.venv/bin/python scripts/fetch_firmware.py

rom: fetch-firmware
	.venv/bin/python scripts/build_rom.py

run: rom
	.venv/bin/python -m emulator

test-api: build/abi-test.bin rom
	.venv/bin/python -m unittest discover -s tests -p 'test_firmware_api.py' -v

.PHONY: test-loader
test-loader: rom
	.venv/bin/python -m unittest discover -s tests -p 'test_loader.py' -v

.PHONY: schematic-check
schematic-check:
	python3 scripts/check_schematic.py
