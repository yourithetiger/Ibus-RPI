import re
import uuid
import shutil

SCHEMATIC_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_sch"
BACKUP_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_sch.bak_task3"

# Restore clean backup from task 3
shutil.copy(BACKUP_PATH, SCHEMATIC_PATH)

def uid():
    return str(uuid.uuid4())

def transform(S_x, S_y, p_x, p_y, rot):
    if rot == 0:
        return round(S_x + p_x, 4), round(S_y - p_y, 4)
    elif rot == 90:
        return round(S_x - p_y, 4), round(S_y - p_x, 4)
    elif rot == 180:
        return round(S_x - p_x, 4), round(S_y + p_y, 4)
    elif rot == 270:
        return round(S_x + p_y, 4), round(S_y + p_x, 4)
    raise ValueError(f"Unsupported rot {rot}")

def get_sys_sym(lib, sym_name, new_lib_name=None):
    with open(f"/usr/share/kicad/symbols/{lib}.kicad_sym") as f:
        text = f.read()
    target = f'(symbol "{sym_name}"'
    idx = text.find(target)
    if idx == -1:
        raise ValueError(f"{sym_name} not found in {lib}")
    depth = 0
    end = -1
    for i in range(idx, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    sym_text = text[idx:end]
    if new_lib_name:
        sym_text = sym_text.replace(f'(symbol "{sym_name}"', f'(symbol "{new_lib_name}:{sym_name}"', 1)
    return sym_text

# 1. Custom library symbols
ts5a3159_sym = """\
\t\t(symbol "pi4-HAT:TS5A3159"
\t\t\t(pin_names (offset 1.016))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "U" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "TS5A3159" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27))) (hide yes))
\t\t\t(property "Datasheet" "http://www.ti.com/lit/ds/symlink/ts5a3159.pdf" (at 0 0 0) (effects (font (size 1.27 1.27))) (hide yes))
\t\t\t(property "Description" "1-Ohm SPDT Analog Switch, SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27))) (hide yes))
\t\t\t(symbol "TS5A3159_0_1"
\t\t\t\t(rectangle (start -6.35 6.35) (end 6.35 -6.35) (stroke (width 0.254) (type default)) (fill (type background)))
\t\t\t)
\t\t\t(symbol "TS5A3159_1_1"
\t\t\t\t(pin passive line (at 8.89 2.54 180) (length 2.54) (name "NO" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin power_in line (at 0 -8.89 90) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin passive line (at 8.89 -2.54 180) (length 2.54) (name "NC" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin passive line (at -8.89 0 0) (length 2.54) (name "COM" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin power_in line (at 0 8.89 270) (length 2.54) (name "V+" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin input line (at -8.89 -3.81 0) (length 2.54) (name "IN" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)"""

tlv3012_sym = """\
\t\t(symbol "pi4-HAT:TLV3012"
\t\t\t(pin_names (offset 1.016))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "U" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "TLV3012" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27))) (hide yes))
\t\t\t(property "Datasheet" "http://www.ti.com/lit/ds/symlink/tlv3012.pdf" (at 0 0 0) (effects (font (size 1.27 1.27))) (hide yes))
\t\t\t(property "Description" "Nanopower Precision Comparator with 1.242V Reference, SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27))) (hide yes))
\t\t\t(symbol "TLV3012_0_1"
\t\t\t\t(rectangle (start -7.62 6.35) (end 7.62 -6.35) (stroke (width 0.254) (type default)) (fill (type background)))
\t\t\t)
\t\t\t(symbol "TLV3012_1_1"
\t\t\t\t(pin output line (at 10.16 0 180) (length 2.54) (name "OUT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin power_in line (at 0 -8.89 90) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin output line (at -10.16 -3.81 0) (length 2.54) (name "REF" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin input line (at -10.16 0 0) (length 2.54) (name "IN-" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin input line (at -10.16 3.81 0) (length 2.54) (name "IN+" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin power_in line (at 0 8.89 270) (length 2.54) (name "V+" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)"""

with open(SCHEMATIC_PATH) as f:
    content = f.read()

# Make sure paper is A3
content = content.replace('(paper "A4")', '(paper "A3")')

# Collect symbols to add to lib_symbols
new_symbols = []
if "pi4-HAT:TS5A3159" not in content:
    new_symbols.append(ts5a3159_sym)
if "pi4-HAT:TLV3012" not in content:
    new_symbols.append(tlv3012_sym)

standard_syms = [
    ("Connector_Generic", "Conn_01x02"),
    ("Connector_Generic", "Conn_01x04"),
    ("Connector", "Conn_Coaxial"),
    ("Switch", "SW_DIP_x03"),
    ("Transistor_FET", "Q_PMOS_GSD"),
    ("Device", "D_Zener_Small")
]

for lib, sym in standard_syms:
    fullname = f"{lib}:{sym}"
    if f'(symbol "{fullname}"' not in content:
        s_text = get_sys_sym(lib, sym, lib)
        s_indented = "\n".join("\t\t" + line for line in s_text.splitlines())
        new_symbols.append(s_indented)

# Insert into lib_symbols
if new_symbols:
    lib_idx = content.find("(lib_symbols")
    depth = 0
    end_lib = -1
    for i in range(lib_idx, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                end_lib = i
                break
    content = content[:end_lib] + "\n" + "\n".join(new_symbols) + "\n\t" + content[end_lib:]
    print(f"Added {len(new_symbols)} symbols to lib_symbols.")

instances = []
wires = []
labels = []
junctions = []
no_connects = []

def add_inst(lib_id, ref, val, fp, x, y, rot=0, pin_count=2, desc=""):
    pins_str = "\n".join([f'\t\t(pin "{i+1}" (uuid "{uid()}"))' for i in range(pin_count)])
    inst = f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rot})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "{ref}" (at {x} {y - 4} 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "{val}" (at {x} {y - 5.5} 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "{fp}" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Datasheet" "~" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Description" "{desc}" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
{pins_str}
\t\t(instances
\t\t\t(project "pi4-HAT"
\t\t\t\t(path "/e63e39d7-6ac0-4ffd-8aa3-1841a4541b55"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""
    instances.append(inst)

def add_wire(x1, y1, x2, y2):
    w = f"""\t(wire
\t\t(pts (xy {x1} {y1}) (xy {x2} {y2}))
\t\t(stroke (width 0) (type solid))
\t\t(uuid "{uid()}")
\t)"""
    wires.append(w)

def add_label(text, x, y, rot=0):
    l = f"""\t(label "{text}"
\t\t(at {x} {y} {rot})
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)"""
    labels.append(l)

def add_nc(x, y):
    nc = f"""\t(no_connect
\t\t(at {x} {y})
\t\t(uuid "{uid()}")
\t)"""
    no_connects.append(nc)

def add_pwr_flag(x, y):
    inst = f"""\t(symbol
\t\t(lib_id "power:PWR_FLAG")
\t\t(at {x} {y} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "#FLG07" (at {x} {y} 0) (effects (font (size 1.27 1.27))) (hide yes))
\t\t(property "Value" "PWR_FLAG" (at {x} {y} 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Datasheet" "~" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Description" "" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(pin "1" (uuid "{uid()}"))
\t\t(instances
\t\t\t(project "pi4-HAT"
\t\t\t\t(path "/e63e39d7-6ac0-4ffd-8aa3-1841a4541b55"
\t\t\t\t\t(reference "#FLG07")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""
    instances.append(inst)


# =========================================================================
# BLOCK A: Autonomous Low-Voltage Cutoff for DVR (X: 320..415, Y: 85..155)
# =========================================================================
# R28 (680k) rot=90: local pins (0, 2.54), (0, -2.54)
# pin 1: transform(325.12, 91.44, 0, 2.54, 90) = (322.58, 91.44) -> VRAW
# pin 2: transform(325.12, 91.44, 0, -2.54, 90) = (327.66, 91.44) -> DVR_VCC_5V
add_inst("Device:R_Small", "R28", "680k", "Resistor_SMD:R_0603_1608Metric", 325.12, 91.44, rot=90, pin_count=2)
p1 = transform(325.12, 91.44, 0, 2.54, 90)
p2 = transform(325.12, 91.44, 0, -2.54, 90)
add_label("VRAW", p1[0], p1[1], rot=180)
add_label("DVR_VCC_5V", p2[0], p2[1], rot=0)

# D12 (BZX84C4V7 Zener) rot=90: local pins K: (-2.54, 0), A: (2.54, 0)
# K: transform(335.28, 91.44, -2.54, 0, 90) = (335.28, 93.98) -> DVR_VCC_5V
# A: transform(335.28, 91.44, 2.54, 0, 90) = (335.28, 88.9) -> GND
add_inst("Device:D_Zener_Small", "D12", "BZX84C4V7", "Package_TO_SOT_SMD:SOT-23", 335.28, 91.44, rot=90, pin_count=2)
pk = transform(335.28, 91.44, -2.54, 0, 90)
pa = transform(335.28, 91.44, 2.54, 0, 90)
add_label("DVR_VCC_5V", pk[0], pk[1], rot=270)
add_label("GND", pa[0], pa[1], rot=90)

# C25 (100nF) rot=0: local pins (0, 2.54), (0, -2.54)
# pin 1: (345.44, 91.44 - 2.54) = (345.44, 88.9) -> DVR_VCC_5V
# pin 2: (345.44, 91.44 + 2.54) = (345.44, 93.98) -> GND
add_inst("Device:C_Small", "C25", "100nF", "Capacitor_SMD:C_0603_1608Metric", 345.44, 91.44, rot=0, pin_count=2)
p1 = transform(345.44, 91.44, 0, 2.54, 0)
p2 = transform(345.44, 91.44, 0, -2.54, 0)
add_label("DVR_VCC_5V", p1[0], p1[1], rot=90)
add_label("GND", p2[0], p2[1], rot=270)
# Add PWR_FLAG on DVR_VCC_5V
add_pwr_flag(p1[0], p1[1])

# Comparator U6 (TLV3012) at (355.6, 121.92) rot=0
# Pin 1 (OUT): (10.16, 0) -> (365.76, 121.92)
# Pin 2 (GND): (0, -8.89) -> (355.6, 130.81)
# Pin 3 (REF): (-10.16, -3.81) -> (345.44, 125.73)
# Pin 4 (IN-): (-10.16, 0) -> (345.44, 121.92)
# Pin 5 (IN+): (-10.16, 3.81) -> (345.44, 118.11)
# Pin 6 (V+):  (0, 8.89) -> (355.6, 113.03)
add_inst("pi4-HAT:TLV3012", "U6", "TLV3012", "Package_TO_SOT_SMD:SOT-23-6", 355.6, 121.92, rot=0, pin_count=6)
p_out = transform(355.6, 121.92, 10.16, 0, 0)
p_gnd = transform(355.6, 121.92, 0, -8.89, 0)
p_ref = transform(355.6, 121.92, -10.16, -3.81, 0)
p_inm = transform(355.6, 121.92, -10.16, 0, 0)
p_inp = transform(355.6, 121.92, -10.16, 3.81, 0)
p_vcc = transform(355.6, 121.92, 0, 8.89, 0)

add_label("DVR_COMP_OUT", p_out[0], p_out[1], rot=0)
add_label("GND", p_gnd[0], p_gnd[1], rot=270)
add_label("DVR_SENSE", p_inp[0], p_inp[1], rot=180)
add_label("DVR_VCC_5V", p_vcc[0], p_vcc[1], rot=90)
# Connect Pin 3 (REF) to Pin 4 (IN-)
add_wire(p_ref[0], p_ref[1], p_ref[0] - 2.54, p_ref[1])
add_wire(p_ref[0] - 2.54, p_ref[1], p_inm[0] - 2.54, p_inm[1])
add_wire(p_inm[0] - 2.54, p_inm[1], p_inm[0], p_inm[1])

# Divider: R29 (1.00M 1%), R30 (1.00M), R34 (10M)
add_inst("Device:R_Small", "R29", "1.00M_1%", "Resistor_SMD:R_0603_1608Metric", 325.12, 114.3, rot=90, pin_count=2)
p1 = transform(325.12, 114.3, 0, 2.54, 90)
p2 = transform(325.12, 114.3, 0, -2.54, 90)
add_label("VRAW", p1[0], p1[1], rot=180)
add_label("DVR_SENSE", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R30", "1.00M", "Resistor_SMD:R_0603_1608Metric", 325.12, 127.0, rot=90, pin_count=2)
p1 = transform(325.12, 127.0, 0, 2.54, 90)
p2 = transform(325.12, 127.0, 0, -2.54, 90)
add_label("DVR_SENSE", p1[0], p1[1], rot=180)
add_label("GND", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R34", "10M", "Resistor_SMD:R_0603_1608Metric", 355.6, 142.24, rot=90, pin_count=2)
p1 = transform(355.6, 142.24, 0, 2.54, 90)
p2 = transform(355.6, 142.24, 0, -2.54, 90)
add_label("DVR_SENSE", p1[0], p1[1], rot=180)
add_label("DVR_COMP_OUT", p2[0], p2[1], rot=0)

# DIP Switch SW_DVR_CFG at (325.12, 149.86) rot=0
# Left pins:
# Pin 1: local (-7.62, 2.54) -> (317.5, 147.32)
# Pin 2: local (-7.62, 0)    -> (317.5, 149.86)
# Pin 3: local (-7.62, -2.54) -> (317.5, 152.4)
# Right pins:
# Pin 6: local (7.62, 2.54)  -> (332.74, 147.32)
# Pin 5: local (7.62, 0)     -> (332.74, 149.86)
# Pin 4: local (7.62, -2.54) -> (332.74, 152.4)
add_inst("Switch:SW_DIP_x03", "SW_DVR_CFG", "DIP-3", "Button_Switch_SMD:SW_DIP_SPSTx03_Slide_6.7x8.9mm_W8.61mm_P2.54mm_LowProfile", 325.12, 149.86, rot=0, pin_count=6)
p_sw1 = transform(325.12, 149.86, -7.62, 2.54, 0)
p_sw2 = transform(325.12, 149.86, -7.62, 0, 0)
p_sw3 = transform(325.12, 149.86, -7.62, -2.54, 0)
add_wire(p_sw1[0], p_sw1[1], p_sw3[0], p_sw3[1])
add_label("DVR_SENSE", p_sw2[0], p_sw2[1], rot=180)

p_sw6 = transform(325.12, 149.86, 7.62, 2.54, 0)
p_sw5 = transform(325.12, 149.86, 7.62, 0, 0)
p_sw4 = transform(325.12, 149.86, 7.62, -2.54, 0)

# Resistors R31 (118k), R32 (115k), R33 (113k) to GND
add_inst("Device:R_Small", "R31", "118k_1%", "Resistor_SMD:R_0603_1608Metric", 342.9, p_sw6[1], rot=90, pin_count=2)
p1 = transform(342.9, p_sw6[1], 0, 2.54, 90)
p2 = transform(342.9, p_sw6[1], 0, -2.54, 90)
add_wire(p_sw6[0], p_sw6[1], p1[0], p1[1])
add_label("GND", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R32", "115k_1%", "Resistor_SMD:R_0603_1608Metric", 342.9, p_sw5[1], rot=90, pin_count=2)
p1 = transform(342.9, p_sw5[1], 0, 2.54, 90)
p2 = transform(342.9, p_sw5[1], 0, -2.54, 90)
add_wire(p_sw5[0], p_sw5[1], p1[0], p1[1])
add_label("GND", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R33", "113k_1%", "Resistor_SMD:R_0603_1608Metric", 342.9, p_sw4[1], rot=90, pin_count=2)
p1 = transform(342.9, p_sw4[1], 0, 2.54, 90)
p2 = transform(342.9, p_sw4[1], 0, -2.54, 90)
add_wire(p_sw4[0], p_sw4[1], p1[0], p1[1])
add_label("GND", p2[0], p2[1], rot=0)

# MOSFET Driver Q3 (2N7002) at (381.0, 121.92) rot=0
# G: local (-5.08, 0)    -> (375.92, 121.92)
# S: local (2.54, -5.08) -> (383.54, 127.0)
# D: local (2.54, 5.08)  -> (383.54, 116.84)
add_inst("Transistor_FET:Q_NMOS_GSD", "Q3", "2N7002", "Package_TO_SOT_SMD:SOT-23", 381.0, 121.92, rot=0, pin_count=3)
q3_g = transform(381.0, 121.92, -5.08, 0, 0)
q3_s = transform(381.0, 121.92, 2.54, -5.08, 0)
q3_d = transform(381.0, 121.92, 2.54, 5.08, 0)
add_label("DVR_COMP_OUT", q3_g[0], q3_g[1], rot=180)
add_label("GND", q3_s[0], q3_s[1], rot=270)
add_label("DVR_GATE_PULL", q3_d[0], q3_d[1], rot=90)

# R35 (100k) & R36 (100k)
add_inst("Device:R_Small", "R35", "100k", "Resistor_SMD:R_0603_1608Metric", 393.7, 104.14, rot=90, pin_count=2)
p1 = transform(393.7, 104.14, 0, 2.54, 90)
p2 = transform(393.7, 104.14, 0, -2.54, 90)
add_label("VRAW", p1[0], p1[1], rot=180)
add_label("DVR_PMOS_GATE", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R36", "100k", "Resistor_SMD:R_0603_1608Metric", 393.7, 116.84, rot=90, pin_count=2)
p1 = transform(393.7, 116.84, 0, 2.54, 90)
p2 = transform(393.7, 116.84, 0, -2.54, 90)
add_label("DVR_PMOS_GATE", p1[0], p1[1], rot=180)
add_label("DVR_GATE_PULL", p2[0], p2[1], rot=0)

# P-MOSFET Q4 (DMP32D4S) at (406.4, 104.14) rot=0
# G: local (-5.08, 0)    -> (401.32, 104.14)
# S: local (2.54, -5.08) -> (408.94, 109.22)
# D: local (2.54, 5.08)  -> (408.94, 99.06)
add_inst("Transistor_FET:Q_PMOS_GSD", "Q4", "DMP32D4S", "Package_TO_SOT_SMD:SOT-23", 406.4, 104.14, rot=0, pin_count=3)
q4_g = transform(406.4, 104.14, -5.08, 0, 0)
q4_s = transform(406.4, 104.14, 2.54, -5.08, 0)
q4_d = transform(406.4, 104.14, 2.54, 5.08, 0)
add_label("DVR_PMOS_GATE", q4_g[0], q4_g[1], rot=180)
add_label("VRAW", q4_s[0], q4_s[1], rot=270)
add_label("DVR_12V_OUT", q4_d[0], q4_d[1], rot=90)

# Screw terminal J_DVR (Conn_01x02) at (419.1, 99.06) rot=0
# Pin 1: local (-5.08, 0)     -> (414.02, 99.06) -> DVR_12V_OUT
# Pin 2: local (-5.08, -2.54) -> (414.02, 101.6) -> GND
add_inst("Connector_Generic:Conn_01x02", "J_DVR", "TE_MKDS_2P", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", 419.1, 99.06, rot=0, pin_count=2)
jd_p1 = transform(419.1, 99.06, -5.08, 0, 0)
jd_p2 = transform(419.1, 99.06, -5.08, -2.54, 0)
add_label("DVR_12V_OUT", jd_p1[0], jd_p1[1], rot=180)
add_label("GND", jd_p2[0], jd_p2[1], rot=180)

# Pi Monitoring Divider R37 (10k), R38 (20k) -> GPIO26
add_inst("Device:R_Small", "R37", "10k", "Resistor_SMD:R_0603_1608Metric", 375.92, 137.16, rot=90, pin_count=2)
p1 = transform(375.92, 137.16, 0, 2.54, 90)
p2 = transform(375.92, 137.16, 0, -2.54, 90)
add_label("DVR_COMP_OUT", p1[0], p1[1], rot=180)
add_label("GPIO26", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R38", "20k", "Resistor_SMD:R_0603_1608Metric", 391.16, 137.16, rot=90, pin_count=2)
p1 = transform(391.16, 137.16, 0, 2.54, 90)
p2 = transform(391.16, 137.16, 0, -2.54, 90)
add_label("GPIO26", p1[0], p1[1], rot=180)
add_label("GND", p2[0], p2[1], rot=0)


# =========================================================================
# BLOCK B: Reverse 12V Detect & TV Pin 17 Diode-OR (X: 120..195, Y: 250..275)
# =========================================================================
# J_REV (Conn_01x02) at (129.54, 256.54) rot=0
# Pin 1: (-5.08, 0)     -> (124.46, 256.54)
# Pin 2: (-5.08, -2.54) -> (124.46, 259.08)
add_inst("Connector_Generic:Conn_01x02", "J_REV", "MKDS_REV_12V", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", 129.54, 256.54, rot=0, pin_count=2)
p1 = transform(129.54, 256.54, -5.08, 0, 0)
p2 = transform(129.54, 256.54, -5.08, -2.54, 0)
add_label("REV_12V_IN", p1[0], p1[1], rot=180)
add_label("GND", p2[0], p2[1], rot=180)

# Divider R22 (10k), R23 (3.3k) & D8 (3.3V Zener) -> GPIO13{slash}PWM1
add_inst("Device:R_Small", "R22", "10k", "Resistor_SMD:R_0603_1608Metric", 142.24, 256.54, rot=90, pin_count=2)
p1 = transform(142.24, 256.54, 0, 2.54, 90)
p2 = transform(142.24, 256.54, 0, -2.54, 90)
add_label("REV_12V_IN", p1[0], p1[1], rot=180)
add_label("REV_SENSE_3V3", p2[0], p2[1], rot=0)
add_label("GPIO13{slash}PWM1", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R23", "3.3k", "Resistor_SMD:R_0603_1608Metric", 154.94, 256.54, rot=0, pin_count=2)
# rot=0 -> p1 (0, 2.54) -> (154.94, 254.0), p2 (0, -2.54) -> (154.94, 259.08)
p1 = transform(154.94, 256.54, 0, 2.54, 0)
p2 = transform(154.94, 256.54, 0, -2.54, 0)
add_label("REV_SENSE_3V3", p1[0], p1[1], rot=90)
add_label("GND", p2[0], p2[1], rot=270)

add_inst("Device:D_Zener_Small", "D8", "BZX84C3V3", "Package_TO_SOT_SMD:SOT-23", 165.1, 256.54, rot=90, pin_count=2)
# rot=90 -> K (-2.54, 0) -> (165.1, 259.08), A (2.54, 0) -> (165.1, 254.0)
# Wait! In rot=90, pk = (165.1, 256.54 - (-2.54) is inverted):
# transform(165.1, 256.54, -2.54, 0, 90) = (165.1, 259.08)
# transform(165.1, 256.54, 2.54, 0, 90) = (165.1, 254.0)
# So pk is at 259.08 and pa is at 254.0!
pk = transform(165.1, 256.54, -2.54, 0, 90)
pa = transform(165.1, 256.54, 2.54, 0, 90)
add_label("REV_SENSE_3V3", pk[0], pk[1], rot=270)
add_label("GND", pa[0], pa[1], rot=90)

# Diode-OR D9 (BAT54C) for TV Pin 17 ground trigger
# Pin 1 (Anode 1): (-7.62, 0) -> (170.18, 256.54)
# Pin 2 (Anode 2): (7.62, 0)  -> (185.42, 256.54)
# Pin 3 (Cathode): (0, -5.08) -> (177.8, 261.62)
add_inst("Diode:BAT54C", "D9", "BAT54C", "Package_TO_SOT_SMD:SOT-23", 177.8, 256.54, rot=0, pin_count=3)
p1 = transform(177.8, 256.54, -7.62, 0, 0)
p2 = transform(177.8, 256.54, 7.62, 0, 0)
p3 = transform(177.8, 256.54, 0, -5.08, 0)
add_label("REV_SENSE_3V3", p1[0], p1[1], rot=180)
add_label("GPIO25", p2[0], p2[1], rot=0)
add_label("TV_TRIG_GATE", p3[0], p3[1], rot=270)

# Pull-down R25 (100k) rot=0
add_inst("Device:R_Small", "R25", "100k", "Resistor_SMD:R_0603_1608Metric", 177.8, 269.24, rot=0, pin_count=2)
p1 = transform(177.8, 269.24, 0, 2.54, 0)
p2 = transform(177.8, 269.24, 0, -2.54, 0)
add_label("TV_TRIG_GATE", p1[0], p1[1], rot=90)
add_label("GND", p2[0], p2[1], rot=270)

# Transistor Q2 (2N7002) at (195.58, 256.54) rot=0
add_inst("Transistor_FET:Q_NMOS_GSD", "Q2", "2N7002", "Package_TO_SOT_SMD:SOT-23", 195.58, 256.54, rot=0, pin_count=3)
q2_g = transform(195.58, 256.54, -5.08, 0, 0)
q2_s = transform(195.58, 256.54, 2.54, -5.08, 0)
q2_d = transform(195.58, 256.54, 2.54, 5.08, 0)
add_label("TV_TRIG_GATE", q2_g[0], q2_g[1], rot=180)
add_label("GND", q2_s[0], q2_s[1], rot=270)
add_label("CAM_TRIG_GND", q2_d[0], q2_d[1], rot=90)

# J_TV_TRIG (Conn_01x02) at (208.28, 251.46) rot=0
# Pin 1: (-5.08, 0)     -> (203.2, 251.46) -> CAM_TRIG_GND
# Pin 2: (-5.08, -2.54) -> (203.2, 254.0)  -> GND
add_inst("Connector_Generic:Conn_01x02", "J_TV_TRIG", "TV_PIN17_TRIG", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", 208.28, 251.46, rot=0, pin_count=2)
p1 = transform(208.28, 251.46, -5.08, 0, 0)
p2 = transform(208.28, 251.46, -5.08, -2.54, 0)
add_label("CAM_TRIG_GND", p1[0], p1[1], rot=180)
add_label("GND", p2[0], p2[1], rot=180)


# =========================================================================
# BLOCK C: TS5A3159 Video Switch & Connectors (X: 215..300, Y: 250..275)
# =========================================================================
# Diode-OR D11 (BAT54C) for VID_SEL
add_inst("Diode:BAT54C", "D11", "BAT54C", "Package_TO_SOT_SMD:SOT-23", 226.06, 256.54, rot=0, pin_count=3)
p1 = transform(226.06, 256.54, -7.62, 0, 0)
p2 = transform(226.06, 256.54, 7.62, 0, 0)
p3 = transform(226.06, 256.54, 0, -5.08, 0)
add_label("REV_SENSE_3V3", p1[0], p1[1], rot=180)
add_label("GPIO24", p2[0], p2[1], rot=0)
add_label("VID_SEL", p3[0], p3[1], rot=270)

# Pull-down R24 (100k)
add_inst("Device:R_Small", "R24", "100k", "Resistor_SMD:R_0603_1608Metric", 226.06, 269.24, rot=0, pin_count=2)
p1 = transform(226.06, 269.24, 0, 2.54, 0)
p2 = transform(226.06, 269.24, 0, -2.54, 0)
add_label("VID_SEL", p1[0], p1[1], rot=90)
add_label("GND", p2[0], p2[1], rot=270)

# Video Switch U5 (TS5A3159) at (254.0, 256.54) rot=0
# Pin 1 (NO):  (8.89, 2.54)  -> (262.89, 254.0)
# Pin 2 (GND): (0, -8.89)    -> (254.0, 265.43)
# Pin 3 (NC):  (8.89, -2.54) -> (262.89, 259.08)
# Pin 4 (COM): (-8.89, 0)    -> (245.11, 256.54)
# Pin 5 (V+):  (0, 8.89)     -> (254.0, 247.65)
# Pin 6 (IN):  (-8.89, -3.81)-> (245.11, 260.35)
add_inst("pi4-HAT:TS5A3159", "U5", "TS5A3159", "Package_TO_SOT_SMD:SOT-23-6", 254.0, 256.54, rot=0, pin_count=6)
p_no  = transform(254.0, 256.54, 8.89, 2.54, 0)
p_gnd = transform(254.0, 256.54, 0, -8.89, 0)
p_nc  = transform(254.0, 256.54, 8.89, -2.54, 0)
p_com = transform(254.0, 256.54, -8.89, 0, 0)
p_vcc = transform(254.0, 256.54, 0, 8.89, 0)
p_in  = transform(254.0, 256.54, -8.89, -3.81, 0)

add_label("CAM_VID", p_no[0], p_no[1], rot=0)
add_label("GND", p_gnd[0], p_gnd[1], rot=270)
add_label("PI_VID", p_nc[0], p_nc[1], rot=0)
add_label("TV_VID_OUT", p_com[0], p_com[1], rot=180)
add_label("+5V", p_vcc[0], p_vcc[1], rot=90)
add_label("VID_SEL", p_in[0], p_in[1], rot=180)

# Decoupling C23 (100nF), C24 (10uF)
add_inst("Device:C_Small", "C23", "100nF", "Capacitor_SMD:C_0603_1608Metric", 243.84, 245.11, rot=0, pin_count=2)
p1 = transform(243.84, 245.11, 0, 2.54, 0)
p2 = transform(243.84, 245.11, 0, -2.54, 0)
add_label("+5V", p1[0], p1[1], rot=90)
add_label("GND", p2[0], p2[1], rot=270)

add_inst("Device:C_Small", "C24", "10uF", "Capacitor_SMD:C_0805_2012Metric", 264.16, 245.11, rot=0, pin_count=2)
p1 = transform(264.16, 245.11, 0, 2.54, 0)
p2 = transform(264.16, 245.11, 0, -2.54, 0)
add_label("+5V", p1[0], p1[1], rot=90)
add_label("GND", p2[0], p2[1], rot=270)

# J_PI_VID (Conn_01x04) at (284.48, 256.54) rot=0
# Pin 1: (-5.08, 2.54)  -> (279.4, 254.0) -> NC
# Pin 2: (-5.08, 0)     -> (279.4, 256.54) -> NC
# Pin 3: (-5.08, -2.54) -> (279.4, 259.08) -> GND
# Pin 4: (-5.08, -5.08) -> (279.4, 261.62) -> PI_VID
add_inst("Connector_Generic:Conn_01x04", "J_PI_VID", "TRRS_3.5mm_PI", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", 284.48, 256.54, rot=0, pin_count=4)
p1 = transform(284.48, 256.54, -5.08, 2.54, 0)
p2 = transform(284.48, 256.54, -5.08, 0, 0)
p3 = transform(284.48, 256.54, -5.08, -2.54, 0)
p4 = transform(284.48, 256.54, -5.08, -5.08, 0)
add_nc(p1[0], p1[1])
add_nc(p2[0], p2[1])
add_label("GND", p3[0], p3[1], rot=180)
add_label("PI_VID", p4[0], p4[1], rot=180)

# J_RCA_CAM (Conn_Coaxial) at (284.48, 269.24) rot=0
# Pin 1 (In):  (-5.08, 0)    -> (279.4, 269.24)
# Pin 2 (Ext): (0, -5.08)    -> (284.48, 274.32)
add_inst("Connector:Conn_Coaxial", "J_RCA_CAM", "RCA_CAM_IN", "Connector_Coaxial:SMA_Amphenol_132203-12_Horizontal", 284.48, 269.24, rot=0, pin_count=2)
p1 = transform(284.48, 269.24, -5.08, 0, 0)
p2 = transform(284.48, 269.24, 0, -5.08, 0)
add_label("CAM_VID", p1[0], p1[1], rot=180)
add_label("GND", p2[0], p2[1], rot=270)

# J_RCA_TV (Conn_Coaxial) at (236.22, 269.24) rot=180
# Pin 1 (In):  local (-5.08, 0) -> rot=180: (236.22 + 5.08, 269.24) = (241.3, 269.24)
# Pin 2 (Ext): local (0, -5.08) -> rot=180: (236.22, 269.24 + (-5.08)) = (236.22, 264.16)
add_inst("Connector:Conn_Coaxial", "J_RCA_TV", "RCA_TV_OUT", "Connector_Coaxial:SMA_Amphenol_132203-12_Horizontal", 236.22, 269.24, rot=180, pin_count=2)
p1 = transform(236.22, 269.24, -5.08, 0, 180)
p2 = transform(236.22, 269.24, 0, -5.08, 180)
add_label("TV_VID_OUT", p1[0], p1[1], rot=0)
add_label("GND", p2[0], p2[1], rot=90)


# =========================================================================
# BLOCK D: Fan PWM Control (X: 320..375, Y: 250..275)
# =========================================================================
# Gate protection R27 (100) & pull-down R26 (100k)
add_inst("Device:R_Small", "R27", "100", "Resistor_SMD:R_0603_1608Metric", 325.12, 256.54, rot=90, pin_count=2)
p1 = transform(325.12, 256.54, 0, 2.54, 90)
p2 = transform(325.12, 256.54, 0, -2.54, 90)
add_label("GPIO12{slash}PWM0", p1[0], p1[1], rot=180)
add_label("FAN_GATE", p2[0], p2[1], rot=0)

add_inst("Device:R_Small", "R26", "100k", "Resistor_SMD:R_0603_1608Metric", 335.28, 256.54, rot=0, pin_count=2)
p1 = transform(335.28, 256.54, 0, 2.54, 0)
p2 = transform(335.28, 256.54, 0, -2.54, 0)
add_label("FAN_GATE", p1[0], p1[1], rot=90)
add_label("GND", p2[0], p2[1], rot=270)

# Transistor Q5 (2N7002) at (345.44, 256.54) rot=0
# G: (-5.08, 0)    -> (340.36, 256.54)
# S: (2.54, -5.08) -> (347.98, 261.62)
# D: (2.54, 5.08)  -> (347.98, 251.46)
add_inst("Transistor_FET:Q_NMOS_GSD", "Q5", "2N7002", "Package_TO_SOT_SMD:SOT-23", 345.44, 256.54, rot=0, pin_count=3)
q5_g = transform(345.44, 256.54, -5.08, 0, 0)
q5_s = transform(345.44, 256.54, 2.54, -5.08, 0)
q5_d = transform(345.44, 256.54, 2.54, 5.08, 0)
add_label("FAN_GATE", q5_g[0], q5_g[1], rot=180)
add_label("GND", q5_s[0], q5_s[1], rot=270)
add_label("FAN_NEG", q5_d[0], q5_d[1], rot=90)

# J_FAN (Conn_01x02) at (360.68, 256.54) rot=0
# Pin 1: (-5.08, 0)     -> (355.6, 256.54) -> +5V
# Pin 2: (-5.08, -2.54) -> (355.6, 259.08) -> FAN_NEG
add_inst("Connector_Generic:Conn_01x02", "J_FAN", "JST_2P_FAN", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", 360.68, 256.54, rot=0, pin_count=2)
p1 = transform(360.68, 256.54, -5.08, 0, 0)
p2 = transform(360.68, 256.54, -5.08, -2.54, 0)
add_label("+5V", p1[0], p1[1], rot=180)
add_label("FAN_NEG", p2[0], p2[1], rot=180)

# Flyback Diode D10 (1N4148) rot=90: local K: (-3.81, 0), A: (3.81, 0)
# K: transform(368.3, 256.54, -3.81, 0, 90) = (368.3, 260.35) -> +5V
# A: transform(368.3, 256.54, 3.81, 0, 90)  = (368.3, 252.73) -> FAN_NEG
add_inst("Device:D", "D10", "1N4148", "Diode_SMD:D_SOD-323", 368.3, 256.54, rot=90, pin_count=2)
pk = transform(368.3, 256.54, -3.81, 0, 90)
pa = transform(368.3, 256.54, 3.81, 0, 90)
add_label("+5V", pk[0], pk[1], rot=270)
add_label("FAN_NEG", pa[0], pa[1], rot=90)


# =========================================================================
# 3. Assemble and Append to Schematic Content
# =========================================================================
all_elements = instances + wires + labels + junctions + no_connects
elements_str = "\n".join(all_elements)

last_paren = content.rfind(")")
new_content = content[:last_paren] + "\n" + elements_str + "\n)"

with open(SCHEMATIC_PATH, "w") as f:
    f.write(new_content)

print(f"Task 4 regenerated successfully: {len(instances)} components, {len(labels)} labels, {len(wires)} wires.")
