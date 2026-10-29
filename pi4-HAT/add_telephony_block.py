import re
import uuid
import shutil
import subprocess

SCHEMATIC_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_sch"
BACKUP_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_sch.bak_tel"

# Restore clean backup
shutil.copy(BACKUP_PATH, SCHEMATIC_PATH)

def uid():
    return str(uuid.uuid4())

def get_sys_sym(lib, sym_name):
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
    sym_text = sym_text.replace(f'(symbol "{sym_name}"', f'(symbol "{lib}:{sym_name}"', 1)
    return sym_text

with open(SCHEMATIC_PATH) as f:
    content = f.read()

# 1. Add PAM8406D to lib_symbols at exact close paren of (lib_symbols ...)
lib_sym_start = content.find("(lib_symbols")
depth = 0
lib_sym_close_idx = -1
for i in range(lib_sym_start, len(content)):
    if content[i] == '(':
        depth += 1
    elif content[i] == ')':
        depth -= 1
        if depth == 0:
            lib_sym_close_idx = i
            break

if "Amplifier_Audio:PAM8406D" not in content:
    pam_sym = get_sys_sym("Amplifier_Audio", "PAM8406D")
    # Indent pam_sym with a tab so it matches other lib symbols
    indented_pam = "\n\t\t" + pam_sym.replace("\n", "\n\t")
    # Insert right before the closing paren of (lib_symbols)
    # The last characters before index lib_sym_close_idx are \n\t
    r_idx = content.rfind("\n\t)", lib_sym_start, lib_sym_close_idx + 1)
    content = content[:r_idx] + indented_pam + "\n\t)" + content[lib_sym_close_idx + 1:]

# Helper formatters
def format_symbol(lib_id, ref, val, fp, x, y, rot=0, pins=None, desc="", dsheet="~"):
    p_lines = ""
    if pins:
        for p in pins:
            p_lines += f'\t\t(pin "{p}" (uuid "{uid()}"))\n'
    return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rot})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "{ref}" (at {x} {round(y-2.54, 2)} 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "{val}" (at {x} {round(y-3.81, 2)} 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "{fp}" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Datasheet" "{dsheet}" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Description" "{desc}" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))
{p_lines}\t\t(instances
\t\t\t(project "pi4-HAT"
\t\t\t\t(path "/e63e39d7-6ac0-4ffd-8aa3-1841a4541b55"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)\n"""

def format_wire(x1, y1, x2, y2):
    return f"""\t(wire
\t\t(pts
\t\t\t(xy {x1} {y1}) (xy {x2} {y2})
\t\t)
\t\t(stroke (width 0) (type default))
\t\t(uuid "{uid()}")
\t)\n"""

def format_label(name, x, y, rot=0, justify="left"):
    return f"""\t(label "{name}"
\t\t(at {x} {y} {rot})
\t\t(effects (font (size 1.27 1.27)) (justify {justify}))
\t\t(uuid "{uid()}")
\t)\n"""

def format_no_connect(x, y):
    return f"""\t(no_connect
\t\t(at {x} {y})
\t\t(uuid "{uid()}")
\t)\n"""

def format_junction(x, y):
    return f"""\t(junction
\t\t(at {x} {y})
\t\t(diameter 0.9144)
\t\t(color 0 0 0 0)
\t\t(uuid "{uid()}")
\t)\n"""

elements = []

# Title text for the block
elements.append(f"""\t(text "OEM Hands-Free Telephony & DB25 Interface (BlueBus Compatible)"
\t\t(exclude_from_sim no)
\t\t(at 315.0 166.0 0)
\t\t(effects (font (size 2.0 2.0) (bold yes)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)\n""")

# 1. PAM8406D IC U7
u7_pins = [str(i) for i in range(1, 17)]
elements.append(format_symbol("Amplifier_Audio:PAM8406D", "U7", "PAM8406D", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 365.76, 190.50, 0, u7_pins, "5W Class-D Audio Amp"))

# 2. Connector J_TEL 1x06
j_tel_pins = [str(i) for i in range(1, 7)]
elements.append(format_symbol("Connector_Generic:Conn_01x06", "J_TEL", "TCU_IO_DB25", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", 416.56, 187.96, 0, j_tel_pins, "DB25 Telephone Harness Interface"))

# 3. Connector J_MIC 1x02
j_mic_pins = ["1", "2"]
elements.append(format_symbol("Connector_Generic:Conn_01x02", "J_MIC", "MIC_OUT_USB", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", 439.42, 215.90, 0, j_mic_pins, "Microphone Output to USB Sound Card"))

# 4. Transistor Q4 2N7002
elements.append(format_symbol("Transistor_FET:Q_NMOS_GSD", "Q4", "2N7002", "Package_TO_SOT_SMD:SOT-23", 403.86, 200.66, 0, ["1", "2", "3"], "TEL_MUTE Open Drain Pull-Down"))

# 5. Ferrite Beads
elements.append(format_symbol("Device:L_Ferrite", "FB1", "120R/2A", "Inductor_SMD:L_0805_2012Metric", 391.16, 182.88, 90, ["1", "2"]))
elements.append(format_symbol("Device:L_Ferrite", "FB2", "120R/2A", "Inductor_SMD:L_0805_2012Metric", 391.16, 185.42, 90, ["1", "2"]))
elements.append(format_symbol("Device:L_Ferrite", "FB3", "120R/2A", "Inductor_SMD:L_0805_2012Metric", 320.04, 180.34, 90, ["1", "2"]))

# 6. Capacitors
elements.append(format_symbol("Device:C_Small", "C26", "10uF", "Capacitor_SMD:C_0805_2012Metric", 373.38, 175.26, 0, ["1", "2"])) # +5V decoupling
elements.append(format_symbol("Device:C_Small", "C27", "0.1uF", "Capacitor_SMD:C_0603_1608Metric", 355.60, 175.26, 0, ["1", "2"])) # VDD decoupling
elements.append(format_symbol("Device:C_Small", "C28", "1uF", "Capacitor_SMD:C_0603_1608Metric", 342.90, 203.20, 0, ["1", "2"])) # VREF
elements.append(format_symbol("Device:C_Small", "C29", "1uF", "Capacitor_SMD:C_0603_1608Metric", 332.74, 180.34, 90, ["1", "2"])) # INL coupling
elements.append(format_symbol("Device:C_Small", "C30", "10uF", "Capacitor_SMD:C_0805_2012Metric", 402.59, 182.88, 90, ["1", "2"])) # OUT_L+ DC block
elements.append(format_symbol("Device:C_Small", "C31", "10uF", "Capacitor_SMD:C_0805_2012Metric", 402.59, 185.42, 90, ["1", "2"])) # OUT_L- DC block
elements.append(format_symbol("Device:C_Small", "C32", "10uF", "Capacitor_SMD:C_0805_2012Metric", 419.10, 236.22, 0, ["1", "2"])) # MIC Bias filter
elements.append(format_symbol("Device:C_Small", "C33", "10uF", "Capacitor_SMD:C_0805_2012Metric", 426.72, 215.90, 90, ["1", "2"])) # MIC DC block

# 7. Resistors
elements.append(format_symbol("Device:R_Small", "R39", "1k", "Resistor_SMD:R_0603_1608Metric", 383.54, 200.66, 90, ["1", "2"])) # MUTE gate
elements.append(format_symbol("Device:R_Small", "R40", "100k", "Resistor_SMD:R_0603_1608Metric", 393.70, 205.74, 0, ["1", "2"])) # MUTE pull-down
elements.append(format_symbol("Device:R_Small", "R41", "1k", "Resistor_SMD:R_0603_1608Metric", 330.20, 193.04, 90, ["1", "2"])) # SHDN series
elements.append(format_symbol("Device:R_Small", "R42", "100k", "Resistor_SMD:R_0603_1608Metric", 340.36, 198.12, 0, ["1", "2"])) # SHDN pull-down
elements.append(format_symbol("Device:R_Small", "R43", "10k", "Resistor_SMD:R_0603_1608Metric", 342.90, 180.34, 90, ["1", "2"])) # INL input res
elements.append(format_symbol("Device:R_Small", "R44", "100", "Resistor_SMD:R_0603_1608Metric", 411.48, 228.60, 90, ["1", "2"])) # MIC filter res
elements.append(format_symbol("Device:R_Small", "R45", "2.2k", "Resistor_SMD:R_0603_1608Metric", 419.10, 223.52, 0, ["1", "2"])) # MIC bias pull-up

# Wires and connections

# Audio Out + path
elements.append(format_wire(381.00, 182.88, 387.35, 182.88)) # U7 pin 1 to FB1 pin 1
elements.append(format_wire(394.97, 182.88, 400.05, 182.88)) # FB1 pin 2 to C30 pin 1
elements.append(format_wire(405.13, 182.88, 411.48, 182.88)) # C30 pin 2 to J_TEL pin 1
elements.append(format_label("TEL_OUT+", 408.0, 182.88, 0))

# Audio Out - path
elements.append(format_wire(381.00, 185.42, 387.35, 185.42)) # U7 pin 3 to FB2 pin 1
elements.append(format_wire(394.97, 185.42, 400.05, 185.42)) # FB2 pin 2 to C31 pin 1
elements.append(format_wire(405.13, 185.42, 411.48, 185.42)) # C31 pin 2 to J_TEL pin 2
elements.append(format_label("TEL_OUT-", 408.0, 185.42, 0))

# Audio Input path (PI_AUDIO_L to INL)
elements.append(format_label("PI_AUDIO_L", 310.0, 180.34, 0, "right"))
elements.append(format_wire(310.0, 180.34, 316.23, 180.34)) # to FB3 pin 1
elements.append(format_wire(323.85, 180.34, 330.20, 180.34)) # FB3 pin 2 to C29 pin 1
elements.append(format_wire(335.28, 180.34, 340.36, 180.34)) # C29 pin 2 to R43 pin 1
elements.append(format_wire(345.44, 180.34, 350.52, 180.34)) # R43 pin 2 to U7 pin 7

# Top Power Rail (+5V)
elements.append(format_wire(350.52, 172.72, 375.0, 172.72))
elements.append(format_label("+5V", 350.52, 172.72, 0, "right"))
elements.append(format_wire(360.68, 172.72, 360.68, 175.26)) # U7 pin 6 (VDD)
elements.append(format_junction(360.68, 172.72))
elements.append(format_wire(365.76, 172.72, 365.76, 175.26)) # U7 pin 4 (PVDDL)
elements.append(format_junction(365.76, 172.72))
elements.append(format_wire(368.30, 172.72, 368.30, 175.26)) # U7 pin 13 (PVDDR)
elements.append(format_junction(368.30, 172.72))

# Decoupling caps on +5V
elements.append(format_wire(355.60, 172.72, 355.60, 172.72))
elements.append(format_wire(355.60, 172.72, 355.60, 175.26-2.54)) # C27 top
elements.append(format_junction(355.60, 172.72))
elements.append(format_wire(355.60, 175.26+2.54, 355.60, 180.0))
elements.append(format_label("GND", 355.60, 180.0, 90))

elements.append(format_wire(373.38, 172.72, 373.38, 175.26-2.54)) # C26 top
elements.append(format_junction(373.38, 172.72))
elements.append(format_wire(373.38, 175.26+2.54, 373.38, 180.0))
elements.append(format_label("GND", 373.38, 180.0, 90))

# MODE (pin 9) and MUTE (pin 5) to +5V
elements.append(format_wire(350.52, 195.58, 347.98, 195.58)) # pin 5
elements.append(format_wire(350.52, 198.12, 347.98, 198.12)) # pin 9
elements.append(format_wire(347.98, 195.58, 347.98, 198.12))
elements.append(format_junction(347.98, 195.58))
elements.append(format_wire(347.98, 195.58, 347.98, 190.0))
elements.append(format_label("+5V", 347.98, 190.0, 90))

# Bottom Ground Rail (GND)
elements.append(format_wire(358.0, 208.28, 370.0, 208.28))
elements.append(format_label("GND", 358.0, 208.28, 0, "right"))
elements.append(format_wire(360.68, 205.74, 360.68, 208.28)) # U7 pin 11 (GND)
elements.append(format_junction(360.68, 208.28))
elements.append(format_wire(365.76, 205.74, 365.76, 208.28)) # U7 pin 2 (PGNDL)
elements.append(format_junction(365.76, 208.28))
elements.append(format_wire(368.30, 205.74, 368.30, 208.28)) # U7 pin 15 (PGNDR)
elements.append(format_junction(368.30, 208.28))

# INR (pin 10) to GND
elements.append(format_wire(350.52, 185.42, 345.44, 185.42))
elements.append(format_label("GND", 345.44, 185.42, 0, "right"))

# VREF (pin 8) with C28 to GND
elements.append(format_wire(350.52, 200.66, 342.90, 200.66)) # U7 pin 8 to C28 top
elements.append(format_wire(342.90, 205.74, 342.90, 208.28)) # C28 bottom to GND
elements.append(format_label("GND", 342.90, 208.28, 90))

# SHDN control (pin 12) from GPIO17
elements.append(format_wire(350.52, 193.04, 340.36, 193.04)) # U7 pin 12 to R42 top
elements.append(format_junction(340.36, 193.04))
elements.append(format_wire(340.36, 193.04, 340.36, 195.58)) # R42 pin 1
elements.append(format_wire(340.36, 200.66, 340.36, 204.0)) # R42 pin 2 to GND
elements.append(format_label("GND", 340.36, 204.0, 90))

elements.append(format_wire(340.36, 193.04, 332.74, 193.04)) # to R41 pin 2
elements.append(format_wire(327.66, 193.04, 323.0, 193.04)) # R41 pin 1 to label
elements.append(format_label("GPIO17", 323.0, 193.04, 0, "right"))

# No-connects on U7 unused pins 14 and 16
elements.append(format_no_connect(381.00, 195.58)) # U7 pin 14
elements.append(format_no_connect(381.00, 198.12)) # U7 pin 16

# Q4 MUTE Circuit
# Gate from GPIO23
elements.append(format_wire(398.78, 200.66, 393.70, 200.66)) # Q4 pin 1 (G) to R40 top
elements.append(format_junction(393.70, 200.66))
elements.append(format_wire(393.70, 200.66, 393.70, 203.20)) # R40 pin 1
elements.append(format_wire(393.70, 208.28, 393.70, 212.0)) # R40 pin 2 to GND
elements.append(format_label("GND", 393.70, 212.0, 90))

elements.append(format_wire(393.70, 200.66, 386.08, 200.66)) # to R39 pin 2
elements.append(format_wire(381.00, 200.66, 376.0, 200.66)) # R39 pin 1 to label
elements.append(format_label("GPIO23", 376.0, 200.66, 0, "right"))

# Source
elements.append(format_wire(406.40, 205.74, 406.40, 209.0)) # Q4 pin 2 (S)
elements.append(format_label("GND", 406.40, 209.0, 90))

# Drain to TEL_MUTE
elements.append(format_wire(406.40, 195.58, 411.48, 195.58)) # Q4 pin 3 (D) to J_TEL pin 6
elements.append(format_label("TEL_MUTE", 408.0, 195.58, 0))

# J_TEL pins 4, 5
elements.append(format_wire(411.48, 190.50, 407.0, 190.50)) # J_TEL pin 4 (GND/Shield)
elements.append(format_label("GND", 407.0, 190.50, 0, "right"))

elements.append(format_no_connect(411.48, 193.04)) # J_TEL pin 5 (TEL_ON spare)

# J_TEL pin 3 (TEL_MIC+) to Mic circuit
elements.append(format_wire(411.48, 187.96, 419.10, 187.96))
elements.append(format_label("TEL_MIC+", 413.0, 187.96, 0))
elements.append(format_wire(419.10, 187.96, 419.10, 215.90)) # down to node

# Node at 419.10, 215.90
elements.append(format_junction(419.10, 215.90))
elements.append(format_wire(419.10, 215.90, 419.10, 220.98)) # to R45 top
elements.append(format_wire(419.10, 215.90, 424.18, 215.90)) # to C33 pin 1

# Bias supply: +5V -> R44 -> node V_MIC_BIAS (at 419.10, 228.60)
elements.append(format_wire(404.0, 228.60, 408.94, 228.60)) # +5V to R44 pin 1
elements.append(format_label("+5V", 404.0, 228.60, 0, "right"))
elements.append(format_wire(414.02, 228.60, 419.10, 228.60)) # R44 pin 2 to node
elements.append(format_junction(419.10, 228.60))

elements.append(format_wire(419.10, 226.06, 419.10, 228.60)) # R45 pin 2 to node
elements.append(format_wire(419.10, 228.60, 419.10, 233.68)) # node to C32 pin 1
elements.append(format_wire(419.10, 238.76, 419.10, 242.0)) # C32 pin 2 to GND
elements.append(format_label("GND", 419.10, 242.0, 90))

# C33 to J_MIC
elements.append(format_wire(429.26, 215.90, 434.34, 215.90)) # to J_MIC pin 1
elements.append(format_label("MIC_OUT", 431.0, 215.90, 0))

# J_MIC pin 2 to GND
elements.append(format_wire(434.34, 218.44, 430.0, 218.44))
elements.append(format_label("GND", 430.0, 218.44, 0, "right"))

# Append all elements before the final closing parenthesis
last_paren = content.rfind(")")
new_content = content[:last_paren] + "\n".join(elements) + "\n)\n"

with open(SCHEMATIC_PATH, "w") as f:
    f.write(new_content)

print(f"Successfully added {len(elements)} schematic objects to pi4-HAT.kicad_sch.")
