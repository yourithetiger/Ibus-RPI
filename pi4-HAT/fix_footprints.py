import re

SCH_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_sch"

with open(SCH_PATH) as f:
    text = f.read()

fixes = {
    "J_CAR_3P": "pi4-HAT:TE_MQS_3PIN",
    "J_CAR_6P": "pi4-HAT:TE_MQS_6PIN",
    "FL1": "Inductor_SMD:L_CommonModeChoke_TDK_ACM7060",
    "L1": "Inductor_SMD:L_Wuerth_WE-PD-Typ-7345",
    "U3": "Package_TO_SOT_SMD:SOT-23-6",
    "SW_DVR_CFG": "Button_Switch_SMD:SW_DIP_SPSTx03_Slide_6.7x9.18mm_W8.61mm_P2.54mm_LowProfile",
    "C1": "Capacitor_SMD:C_0603_1608Metric",
    "R1": "Resistor_SMD:R_0603_1608Metric",
    "R2": "Resistor_SMD:R_0603_1608Metric",
    "JP1": "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
    "U1": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
}

for ref, new_fp in fixes.items():
    # Find symbol block with Reference ref
    pattern = rf'(\(symbol\s+\(lib_id \"[^\"]+\"\).*?\(property \"Reference\" \"{ref}\".*?\(property \"Footprint\" \")[^\"]*(\")'
    m = re.search(pattern, text, re.DOTALL)
    if m:
        text = text[:m.start(1)] + m.group(1) + new_fp + m.group(2) + text[m.end(2):]
        print(f"Updated footprint for {ref} -> {new_fp}")
    else:
        print(f"Warning: Reference {ref} not matched!")

with open(SCH_PATH, "w") as f:
    f.write(text)

print("Footprint updates complete.")
