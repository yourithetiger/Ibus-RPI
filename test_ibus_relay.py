
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

# Add Ibus-service to path
sys.path.append(os.path.join(os.getcwd(), "Ibus-service"))

# Mock uinput before importing ibus
mock_uinput = MagicMock()
sys.modules['uinput'] = mock_uinput

from ibus import WemosRelay, xor_checksum, frame_valid

class TestIbusLogic(unittest.TestCase):
    def test_xor_checksum(self):
        # 3B 05 68 4E 01 00 19
        data = bytes.fromhex("3B 05 68 4E 01 00")
        self.assertEqual(xor_checksum(data), 0x19)

    def test_frame_valid(self):
        frame = bytes.fromhex("3B 05 68 4E 01 00 19")
        self.assertTrue(frame_valid(frame))

        bad_frame = bytes.fromhex("3B 05 68 4E 01 00 20")
        self.assertFalse(frame_valid(bad_frame))

class TestWemosRelayRobustness(unittest.TestCase):
    def setUp(self):
        self.mock_ser = MagicMock()
        with patch('serial.Serial', return_value=self.mock_ser):
            self.relay = WemosRelay("/dev/ttyTEST", 115200)
            self.relay.connect()

    def test_exchange_resets_buffers(self):
        self.relay.rxbuf = bytearray(b"stale data")

        t = [100.0]
        def mock_time():
            val = t[0]
            t[0] += 1.0
            return val

        with patch('time.time', side_effect=mock_time):
            self.mock_ser.read.return_value = b""
            self.relay._exchange("PING")
            self.mock_ser.reset_input_buffer.assert_called()
            self.assertEqual(self.relay.rxbuf, bytearray())

    def test_read_reply_partial_timeout_logging(self):
        self.relay.rxbuf = bytearray()

        # deadline = 100.0 + 0.1 = 100.1
        # while loop 1: 100.01 < 100.1 -> chunk = self.ser.read() -> PARTIAL
        # while loop 2: 100.2 < 100.1 -> False
        t = [100.0, 100.01, 100.2, 100.3, 100.4]
        it = iter(t)

        with patch('time.time', side_effect=lambda: next(it)):
            self.mock_ser.read.return_value = b"PARTIAL"

            with self.assertLogs(level='WARNING') as cm:
                res = self.relay._read_reply(timeout_s=0.1)
                self.assertIsNone(res)
                # print(cm.output)
                self.assertTrue(any("Wemos partial RX buffer timeout: b'PARTIAL'" in output for output in cm.output))

    def test_exchange_handles_stale_data_draining(self):
        self.mock_ser.read.side_effect = [b"STALE\n", b"", b"PONG\n", b"", b""]

        with patch('time.time', side_effect=lambda: 100.0):
             with self.assertLogs(level='INFO') as cm:
                res = self.relay._exchange("PING")
                self.assertEqual(res, "PONG")
                self.assertTrue(any("Wemos stale <- STALE" in output for output in cm.output))
                self.assertTrue(any("Wemos raw <- b'PONG\\n'" in output for output in cm.output))

if __name__ == '__main__':
    unittest.main()
