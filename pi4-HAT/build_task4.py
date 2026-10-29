import uuid
import re

def uid():
    return str(uuid.uuid4())

def get_sym(lib_file, sym_name, new_lib_name=None):
    with open(f'/usr/share/kicad/symbols/{lib_file}.kicad_sym') as f:
        text = f.read()
    target = f'(symbol "{sym_name}"'
    idx = text.find(target)
    if idx == -1:
        raise ValueError(f'{sym_name} not found in {lib_file}')
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

# Custom symbol: TS5A3159
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

# Custom symbol: TLV3012
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

print("Symbols defined.")
