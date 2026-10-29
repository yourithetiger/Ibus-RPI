import re

PCB_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb"

with open(PCB_PATH) as f:
    text = f.read()

# 1. Update layers block to add In1.Cu and In2.Cu if not present
if '(4 "In1.Cu" signal)' not in text:
    old_layers = '(0 "F.Cu" signal)\n\t\t(2 "B.Cu" signal)'
    new_layers = '(0 "F.Cu" signal)\n\t\t(4 "In1.Cu" signal)\n\t\t(6 "In2.Cu" signal)\n\t\t(2 "B.Cu" signal)'
    assert old_layers in text, "old_layers not found"
    text = text.replace(old_layers, new_layers)
    print("Added In1.Cu and In2.Cu to layers.")

# 2. Update stackup
stackup_str = """(stackup
			(layer "F.SilkS"
				(type "Top Silk Screen")
			)
			(layer "F.Paste"
				(type "Top Solder Paste")
			)
			(layer "F.Mask"
				(type "Top Solder Mask")
				(thickness 0.01)
			)
			(layer "F.Cu"
				(type "copper")
				(thickness 0.035)
			)
			(layer "dielectric 1"
				(type "prepreg")
				(thickness 0.1)
				(material "FR4")
				(epsilon_r 4.5)
				(loss_tangent 0.02)
			)
			(layer "In1.Cu"
				(type "copper")
				(thickness 0.035)
			)
			(layer "dielectric 2"
				(type "core")
				(thickness 1.204)
				(material "FR4")
				(epsilon_r 4.5)
				(loss_tangent 0.02)
			)
			(layer "In2.Cu"
				(type "copper")
				(thickness 0.035)
			)
			(layer "dielectric 3"
				(type "prepreg")
				(thickness 0.1)
				(material "FR4")
				(epsilon_r 4.5)
				(loss_tangent 0.02)
			)
			(layer "B.Cu"
				(type "copper")
				(thickness 0.035)
			)
			(layer "B.Mask"
				(type "Bottom Solder Mask")
				(thickness 0.01)
			)
			(layer "B.Paste"
				(type "Bottom Solder Paste")
			)
			(layer "B.SilkS"
				(type "Bottom Silk Screen")
			)
			(copper_finish "None")
			(dielectric_constraints no)
		)"""

old_stackup_match = re.search(r'\(stackup\s*(.*?)(?=\n\t\t\)\n\t\t\(pad_to_mask_clearance)', text, re.DOTALL)
if old_stackup_match:
    text = text[:old_stackup_match.start(0)] + stackup_str + text[old_stackup_match.end(0)+3:]
    print("Stackup replaced with JLCPCB 4-layer stackup.")

with open(PCB_PATH, "w") as f:
    f.write(text)

print("PCB 4-layer configuration updated successfully.")
