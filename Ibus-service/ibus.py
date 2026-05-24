#!/usr/bin/env python3
import time
import logging
import serial
import uinput

IBUS_PORT = "/dev/ttyUSB0"     # Resler
IBUS_BAUD = 9600

WEMOS_PORT = "/dev/ttyUSB1"    # adapte si besoin
WEMOS_BAUD = 115200

LOG_LEVEL = logging.INFO

TV_ON_RADIO = bytes.fromhex("3B 05 68 4E 01 00 19")
TV_OFF_RADIO = bytes.fromhex("3B 05 68 4E 00 00 18")
TV_ON_MONITOR = bytes.fromhex("ED 05 F0 4F 11 12 54")
TV_OFF_MONITOR = bytes.fromhex("ED 05 F0 4F 12 11 54")

MAG_SLOT_1 = 0x20

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(message)s"
)

kbd = uinput.Device([
    uinput.KEY_LEFT,
    uinput.KEY_RIGHT,
    uinput.KEY_UP,
    uinput.KEY_DOWN,
    uinput.KEY_ENTER,
    uinput.KEY_ESC,
    uinput.KEY_HOME,
    uinput.KEY_TAB,
])

def tap(key):
    kbd.emit_click(key)

def xor_checksum(data: bytes) -> int:
    x = 0
    for b in data:
        x ^= b
    return x

def frame_valid(frame: bytes) -> bool:
    if len(frame) < 4:
        return False
    return xor_checksum(frame[:-1]) == frame[-1]

def rebuild_checksum(frame: bytes) -> bytes:
    return frame[:-1] + bytes([xor_checksum(frame[:-1])])

class WemosRelay:
    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.ser = None
        self.current = "OEM"

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.3, write_timeout=0.3)
            time.sleep(1.5)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            logging.info("Wemos connected on %s", self.port)
        except Exception as e:
            logging.warning("No Wemos connection: %s", e)
            self.ser = None

    def cmd(self, s: str):
        if not self.ser:
            return None
        try:
            self.ser.write((s + "\n").encode())
            self.ser.flush()
            rep = self.ser.readline().decode(errors="ignore").strip()
            logging.info("Wemos %s -> %s", s, rep)
            return rep
        except Exception as e:
            logging.warning("Wemos cmd failed: %s", e)
            self.ser = None
            return None

    def set_pi(self):
        if self.current != "PI":
            self.cmd("SRC PI")
            self.current = "PI"

    def set_oem(self):
        if self.current != "OEM":
            self.cmd("SRC OEM")
            self.current = "OEM"

    def keepalive(self):
        if not self.ser:
            return
        if self.current == "PI":
            self.cmd("SRC PI")
        else:
            self.cmd("PING")

class BMWBackend:
    def __init__(self):
        self.ibus = serial.Serial(
            port=IBUS_PORT,
            baudrate=IBUS_BAUD,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.02,
            write_timeout=0.02
        )
        self.buf = bytearray()
        self.tv_mode = False
        self.cdc_disc = 2
        self.wemos = WemosRelay(WEMOS_PORT, WEMOS_BAUD)
        self.wemos.connect()
        self.last_wemos_keepalive = 0.0

    def send_ibus(self, frame: bytes):
        self.ibus.write(frame)
        self.ibus.flush()
        logging.info("TX %s", frame.hex(" ").upper())

    def tv_on(self):
        self.send_ibus(TV_ON_RADIO)
        time.sleep(0.03)
        self.send_ibus(TV_ON_MONITOR)
        self.tv_mode = True
        logging.info("TV mode ON")

    def tv_off(self):
        self.send_ibus(TV_OFF_MONITOR)
        time.sleep(0.03)
        self.send_ibus(TV_OFF_RADIO)
        self.tv_mode = False
        logging.info("TV mode OFF")

    def toggle_tv(self):
        if self.tv_mode:
            self.tv_off()
        else:
            self.tv_on()

    def maybe_handle_hudiy_input(self, src, dst, data):
        if not self.tv_mode:
            return

        if src == 0xF0 and dst == 0x3B and data == bytes([0x48, 0x05]):
            tap(uinput.KEY_ENTER)
        elif src == 0xF0 and dst == 0x3B and data == bytes([0x48, 0x45]):
            tap(uinput.KEY_HOME)
        elif src == 0xF0 and dst == 0xFF and data == bytes([0x48, 0x34]):
            tap(uinput.KEY_ESC)
        elif src == 0xF0 and dst == 0x68 and data == bytes([0x48, 0x20]):
            tap(uinput.KEY_ENTER)
        elif src == 0xF0 and dst == 0x68 and data == bytes([0x48, 0x10]):
            tap(uinput.KEY_UP)
        elif src == 0xF0 and dst == 0x68 and data == bytes([0x48, 0x00]):
            tap(uinput.KEY_DOWN)
        elif src == 0xF0 and dst == 0x3B and len(data) == 2 and data[0] == 0x49:
            if data[1] & 0x80:
                tap(uinput.KEY_RIGHT)
            else:
                tap(uinput.KEY_LEFT)

    def handle_clock(self, src, dst, data):
        if src == 0xF0 and dst == 0xFF and data == bytes([0x48, 0x07]):
            self.toggle_tv()
            return True
        return False

    def handle_cdc_request(self, frame: bytes, src, dst, data):
        if not (src == 0x68 and dst == 0x18 and len(data) >= 2 and data[0] == 0x38):
            return False

        sub = data[1]

        if sub == 0x06 and len(data) >= 3:
            disc = data[2]
            self.cdc_disc = disc
            if disc == 0x01:
                self.wemos.set_pi()
                ack = bytes.fromhex("18 0A 68 39 07 09 00 21 00 01 01 00")
                ack = rebuild_checksum(ack)
                self.send_ibus(ack)
                playing = bytes.fromhex("18 0A 68 39 02 09 00 21 00 01 01 00")
                playing = rebuild_checksum(playing)
                self.send_ibus(playing)
                logging.info("CD1 selected -> PI relay")
                return True
            elif 0x02 <= disc <= 0x06:
                self.wemos.set_oem()
                logging.info("CD%d selected -> OEM relay", disc)
                return False

        if self.cdc_disc == 0x01:
            if sub == 0x03:
                ack = bytes.fromhex("18 0A 68 39 07 09 00 21 00 01 01 00")
                ack = rebuild_checksum(ack)
                self.send_ibus(ack)
                playing = bytes.fromhex("18 0A 68 39 02 09 00 21 00 01 01 00")
                playing = rebuild_checksum(playing)
                self.send_ibus(playing)
                return True

            if sub == 0x00:
                status = bytes.fromhex("18 0A 68 39 02 09 00 21 00 01 01 00")
                status = rebuild_checksum(status)
                self.send_ibus(status)
                return True

        return False

    def rewrite_cdc_status(self, frame: bytes, src, dst, data):
        if not (src == 0x18 and dst == 0x68 and len(data) >= 8 and data[0] == 0x39):
            return frame

        status = bytearray(frame)
        data_start = 3
        magazine_index = data_start + 1 + 3
        status[magazine_index] |= MAG_SLOT_1
        status = bytearray(rebuild_checksum(bytes(status)))
        logging.info("CDC 0x39 rewritten with CD1 present")
        return bytes(status)

    def handle_frame(self, frame: bytes):
        if not frame_valid(frame):
            return

        src = frame[0]
        dst = frame[2]
        data = frame[3:-1]

        if self.handle_clock(src, dst, data):
            return

        self.maybe_handle_hudiy_input(src, dst, data)

        blocked = self.handle_cdc_request(frame, src, dst, data)
        if blocked:
            return

        out = self.rewrite_cdc_status(frame, src, dst, data)
        if out != frame:
            self.send_ibus(out)

    def read_loop(self):
        while True:
            b = self.ibus.read(1)
            now = time.time()

            if now - self.last_wemos_keepalive > 3.0:
                self.wemos.keepalive()
                self.last_wemos_keepalive = now

            if not b:
                continue

            self.buf += b

            if len(self.buf) >= 2:
                length = self.buf[1]
                frame_len = length + 2

                if len(self.buf) == frame_len:
                    frame = bytes(self.buf)
                    self.buf.clear()
                    logging.info("RX %s", frame.hex(" ").upper())
                    self.handle_frame(frame)
                elif len(self.buf) > frame_len:
                    self.buf.clear()

def main():
    backend = BMWBackend()
    backend.read_loop()

if __name__ == "__main__":
    main()
