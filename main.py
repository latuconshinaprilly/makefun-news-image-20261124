#!/usr/bin/env python3
"""Carrier for THE DAYBREAK SIGNAL (NI24, Akun 18).

Stdlib-only: verifies entry.png beside this file against the gate
(1024x1024, <= 1 MiB) and writes its bytes exactly to stdout.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PNG = os.path.join(HERE, "entry.png")
MAX_BYTES = 1024 * 1024


def main():
    with open(PNG, "rb") as fh:
        data = fh.read()
    if len(data) > MAX_BYTES:
        sys.exit("entry.png exceeds 1 MiB gate")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit("entry.png is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (1024, 1024):
        sys.exit("entry.png is not 1024x1024")
    sys.stdout.buffer.write(data)


if __name__ == "__main__":
    main()
