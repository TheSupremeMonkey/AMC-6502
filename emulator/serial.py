"""8N1 serial peer consuming/driving VIA pin levels in emulated cycles."""
from collections import deque


class SerialPeer:
    bit_cycles = 104

    def __init__(self):
        self.time = 0
        self.frames = deque()
        self.output = bytearray()
        self.tx_level = 1
        self.samples = deque()
        self.value = 0
        self.framing_errors = 0

    def feed(self, data: bytes, gap=5000):
        start = max(self.time + 1000, self.frames[-1][0] + gap if self.frames else 0)
        for value in data:
            self.frames.append((start, value))
            start += gap

    @property
    def rx(self):
        while self.frames and self.time >= self.frames[0][0] + 10 * self.bit_cycles:
            self.frames.popleft()
        if not self.frames:
            return 1
        start, value = self.frames[0]
        bit = (self.time - start) // self.bit_cycles
        if bit < 0 or bit >= 9:
            return 1
        return 0 if bit == 0 else (value >> (bit - 1)) & 1

    def peek_rx(self):
        """Inspect the RX pin without removing expired input frames."""
        for start, value in self.frames:
            bit = (self.time - start) // self.bit_cycles
            if bit >= 10:
                continue
            if bit < 0 or bit >= 9:
                return 1
            return 0 if bit == 0 else (value >> (bit - 1)) & 1
        return 1

    def drive_tx(self, level):
        if self.tx_level and not level and not self.samples:
            self.value = 0
            self.samples.extend((self.time + self.bit_cycles * (3 + 2 * bit) // 2, bit) for bit in range(9))
        self.tx_level = level

    def tick(self, time):
        self.time = time
        while self.samples and self.samples[0][0] <= time:
            _, bit = self.samples.popleft()
            if bit < 8:
                self.value |= self.tx_level << bit
            elif self.tx_level:
                self.output.append(self.value)
            else:
                self.framing_errors += 1
