#!/usr/bin/env python3
"""Protocol byte invariants checked with the boardless co-sim stub from
coursework/docs/BOARDLESS_COSIM_METHODOLOGY.md s3.1.

We inject empty cv2 / serial modules into sys.modules *before* importing the
real camera_uart_sender, so the packer imports with no OpenCV, no camera and no
serial port. (serial needs a .Serial attribute because the module annotates
`ser: serial.Serial` at definition time.) This proves the 128x72 RGB888 wire
contract is independent of the new scaling code.

Run standalone (recommended, gives a clean stub):

    set PYTHONUTF8=1
    python tests/test_protocol_invariants.py
"""
import sys
import types
from pathlib import Path

# s3.1 empty stubs, installed before camera_uart_sender is imported.
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
_serial_stub = types.ModuleType("serial")
_serial_stub.Serial = type("Serial", (), {})
sys.modules.setdefault("serial", _serial_stub)

import numpy as np  # real numpy; build_frame_packet relies on it

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import camera_uart_sender as host

FRAME_HEADER = bytes((0x55, 0xAA, 0x80, 0x00, 0x48, 0x00, 0x18))


class FakeSerial:
    """Captures every byte written, like the methodology's compare stub."""

    def __init__(self) -> None:
        self.buffer = bytearray()

    def write(self, data) -> int:
        self.buffer.extend(data)
        return len(data)


def test_build_frame_packet_len_and_header():
    img = np.zeros((72, 128, 3), dtype=np.uint8)
    packet = host.build_frame_packet(img)
    assert len(packet) == 27943, len(packet)
    assert packet[:7] == FRAME_HEADER, packet[:7].hex(" ")


def test_send_control_command_bytes():
    ser = FakeSerial()
    host.send_control_command(ser, 0x01, 0x03)
    assert bytes(ser.buffer) == bytes.fromhex("a55a0103"), ser.buffer.hex(" ")


def test_send_requested_controls_sequence():
    ser = FakeSerial()
    host.send_requested_controls(ser, mode="overlay", threshold=40, overlay="on")
    # A5 5A 01 03 (mode=overlay=3) | A5 5A 02 28 (threshold=40) | A5 5A 03 01 (overlay on)
    expected = bytes.fromhex("a55a0103" "a55a0228" "a55a0301")
    assert bytes(ser.buffer) == expected, ser.buffer.hex(" ")


def test_packing_runs_without_real_opencv():
    """When run standalone the cv2 module is our empty stub, yet packing and
    control bytes still work -> the FPGA contract is decoupled from cv2."""
    cv2_module = sys.modules.get("cv2")
    stubbed = isinstance(cv2_module, types.ModuleType) and not hasattr(cv2_module, "resize")
    if stubbed:
        assert len(host.build_frame_packet(np.zeros((72, 128, 3), np.uint8))) == 27943
    else:
        # Real cv2 was already imported (e.g. running under pytest next to the
        # prepare_frame tests); byte invariants are still covered above.
        assert hasattr(host, "build_frame_packet")


def _run_all() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
