#!/usr/bin/env python3
import os
import time
import glob
import logging
import serial
import uinput
from serial.tools import list_ports

LOG_LEVEL = logging.INFO

WEMOS_FIXED = "/dev/wemos_relay"
RESLER_FIXED = "/dev/ibus_resler"

WEMOS_BAUD = 115200
IBUS_BAUD = 9600

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

def list_serial_candidates():
    ports = []
    for p in list_ports.comports(include_links=True):
        ports.append({
            "device": p.device,
            "description": p.description,
            "hwid": p.hwid,
            "vid": p.vid,
            "pid": p.pid,
            "manufacturer": getattr(p, "manufacturer", None),
            "product": getattr(p, "product", None),
            "serial_number": getattr(p, "serial_number", None),
            "location": getattr(p, "location", None),
            "interface": getattr(p, "interface", None),
        })
    return ports

def port_exists(path: str) -> bool:
    return os.path.exists(path)

def detect_wemos_port():
    if port_exists(WEMOS_FIXED):
        logging.info("Using fixed Wemos port: %s", WEMOS_FIXED)
        return WEMOS_FIXED

    candidates = list_serial_candidates()

    for p in candidates:
        vid = p["vid"]
        pid = p["pid"]
        desc = (p["description"] or "").lower()
        prod = (p["product"] or "").lower()

        if (vid == 0x1A86 and pid == 0x7523) or "ch340" in desc or "ch341" in desc or "usb2.0-ser" in prod:
            logging.info("Auto-detected Wemos candidate: %s (%s)", p["device"], p["description"])
            return p["device"]

    for path in sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")):
        logging.info("Fallback Wemos candidate: %s", path)
        return path

    raise RuntimeError("No Wemos serial port found")

def detect_resler_port(wemos_port: str):
    if port_exists(RESLER_FIXED):
        logging.info("Using fixed Resler port: %s", RESLER_FIXED)
        return RESLER_FIXED

    candidates = list_serial_candidates()

    preferred = []
    fallback = []

    for p in candidates:
        dev = p["device"]
        if dev == wemos_port:
            continue
        if os.path.realpath(dev) == os.path.realpath(wemos_port):
            continue

        desc = (p["description"] or "").lower()
        prod = (p["product"] or "").lower()
        manu = (p["manufacturer"] or "").lower()
        hwid = (p["hwid"] or "").lower()

        score = 0
        if "resler" in desc or "resler" in prod or "resler" in manu:
            score += 100
        if "ftdi" in desc or "ftdi" in hwid:
            score += 20
        if "usb serial" in desc or "uart" in desc:
            score += 5

        if score > 0:
            preferred.append((score, dev, p))
        else:
            fallback.append((dev, p))

    if preferred:
        preferred.sort(reverse=True)
        dev = preferred[0][1]
        p = preferred[0][2]
        logging.info("Auto-detected preferred Resler candidate: %s (%s)", dev, p["description"])
        return dev

    for dev, p in fallback:
        logging.info("Fallback Resler candidate: %s (%s)", dev, p["description"])
        return dev

    raise RuntimeError("No Resler serial port found")

class WemosRelay:
    VALID_REPLIES = {"PONG", "OK", "PI", "OEM"}

    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.ser = None
        self.current = "OEM"

    def connect(self):
        try:
            self.ser = serial.Serial(
                self.port,
                self.baud,
                timeout=0.4,
                write_timeout=0.4
            )
            time.sleep(2.0)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            t_end = time.time() + 1.5
            while time.time() < t_end:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line:
                    logging.info("Wemos boot junk: %r", line)

            logging.info("Wemos connected on %s", self.port)
        except Exception as e:
            logging.warning("No Wemos connection on %s: %s", self.port, e)
            self.ser = None

    def _exchange(self, cmd: str, tries: int = 3):
        if not self.ser:
            return None

        for _ in range(tries):
            try:
                self.ser.reset_input_buffer()
                self.ser.write((cmd + "\n").encode())
                self.ser.flush()

                for _ in range(4):
                    rep = self.ser.readline().decode(errors="ignore").strip()
                    if not rep:
                        continue
                    logging.info("Wemos %s -> %s", cmd, rep)
                    return rep
            except Exception as e:
                logging.warning("Wemos exchange failed: %s", e)
                self.ser = None
                return None

        return None

    def ping(self):
        rep = self._exchange("PING")
        return rep == "PONG"

    def set_pi(self):
        rep = self._exchange("SRC PI")
        if rep in {"PI", "OK"}:
            self.current = "PI"
            return True
        return False

    def set_oem(self):
        rep = self._exchange("SRC OEM")
        if rep in {"OEM", "OK"}:
            self.current = "OEM"
            return True
        return False

    def keepalive(self):
        if not self.ser:
            return
        ok = self.ping()
        if not ok:
            logging.warning("Wemos invalid ping reply, reconnecting")
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
            time.sleep(0.5)
            self.connect()
class BMWBackend:
    def __init__(self):
        self.wemos_port = detect_wemos_port()
        self.resler_port = detect_resler_port(self.wemos_port)

        logging.info("Selected Wemos port: %s", self.wemos_port)
        logging.info("Selected Resler port: %s", self.resler_port)

        self.ibus = serial.Serial(
            port=self.resler_port,
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
        self.wemos = WemosRelay(self.wemos_port, WEMOS_BAUD)
        self.wemos.connect()
        self.last_wemos_keepalive = 0.0

    def send_ibus(self, frame: bytes):
        self.ibus.write(frame)
        self.ibus.flush()
        logging.info("TX %s", frame.hex(' ').upper())

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
                self.send_ibus(rebuild_checksum(ack))
                playing = bytes.fromhex("18 0A 68 39 02 09 00 21 00 01 01 00")
                self.send_ibus(rebuild_checksum(playing))
                logging.info("CD1 selected -> PI relay")
                return True
            elif 0x02 <= disc <= 0x06:
                self.wemos.set_oem()
                logging.info("CD%d selected -> OEM relay", disc)
                return False

        if self.cdc_disc == 0x01:
            if sub == 0x03:
                ack = bytes.fromhex("18 0A 68 39 07 09 00 21 00 01 01 00")
                self.send_ibus(rebuild_checksum(ack))
                playing = bytes.fromhex("18 0A 68 39 02 09 00 21 00 01 01 00")
                self.send_ibus(rebuild_checksum(playing))
                return True

            if sub == 0x00:
                status = bytes.fromhex("18 0A 68 39 02 09 00 21 00 01 01 00")
                self.send_ibus(rebuild_checksum(status))
                return True

        return False

    def rewrite_cdc_status(self, frame: bytes, src, dst, data):
        if not (src == 0x18 and dst == 0x68 and len(data) >= 8 and data[0] == 0x39):
            return frame

        status = bytearray(frame)
        magazine_index = 7
        status[magazine_index] |= MAG_SLOT_1
        return rebuild_checksum(bytes(status))

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
