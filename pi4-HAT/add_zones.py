import uuid

PCB_FILE = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb"

with open(PCB_FILE, "r") as f:
    content = f.read()

# Define the 5 zones
zones = [
    # 1. In1.Cu: Continuous GND Plane
    {
        "layer": "In1.Cu",
        "net_name": "GND",
        "priority": 1,
        "clearance": 0.25,
        "thermal_gap": 0.3,
        "thermal_bridge": 0.4,
        "pts": [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)]
    },
    # 2. In2.Cu: +5V Power Plane (Buck output + Pi4 GPIO header + Amp)
    {
        "layer": "In2.Cu",
        "net_name": "+5V",
        "priority": 1,
        "clearance": 0.3,
        "thermal_gap": 0.3,
        "thermal_bridge": 0.5,
        "pts": [(100.5, 50.5), (175.0, 50.5), (175.0, 114.5), (100.5, 114.5)]
    },
    # 3. In2.Cu: +12V_IN Power Region (Car harness inlet + Relay + Filters)
    {
        "layer": "In2.Cu",
        "net_name": "+12V_IN",
        "priority": 1,
        "clearance": 0.3,
        "thermal_gap": 0.3,
        "thermal_bridge": 0.5,
        "pts": [(175.0, 50.5), (199.5, 50.5), (199.5, 75.0), (175.0, 75.0)]
    },
    # 4. In2.Cu: +3V3 Power Region (TH3122, DAC DVDD/AVDD, logic)
    {
        "layer": "In2.Cu",
        "net_name": "+3V3",
        "priority": 1,
        "clearance": 0.3,
        "thermal_gap": 0.3,
        "thermal_bridge": 0.4,
        "pts": [(175.0, 75.0), (199.5, 75.0), (199.5, 114.5), (175.0, 114.5)]
    },
    # 5. F.Cu: Top GND Flood
    {
        "layer": "F.Cu",
        "net_name": "GND",
        "priority": 0,
        "clearance": 0.25,
        "thermal_gap": 0.25,
        "thermal_bridge": 0.35,
        "pts": [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)]
    },
    # 6. B.Cu: Bottom GND Flood
    {
        "layer": "B.Cu",
        "net_name": "GND",
        "priority": 0,
        "clearance": 0.25,
        "thermal_gap": 0.25,
        "thermal_bridge": 0.35,
        "pts": [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)]
    }
]

zone_sexprs = []
for z in zones:
    pts_str = " ".join(f"(xy {x} {y})" for x, y in z["pts"])
    zone_sexprs.append(f"""\t(zone
\t\t(net_name "{z['net_name']}")
\t\t(layer "{z['layer']}")
\t\t(uuid "{str(uuid.uuid4())}")
\t\t(hatch edge 0.5)
\t\t(priority {z['priority']})
\t\t(connect_pads
\t\t\t(clearance {z['clearance']})
\t\t)
\t\t(min_thickness 0.2)
\t\t(filled_areas_thickness no)
\t\t(fill yes
\t\t\t(thermal_gap {z['thermal_gap']})
\t\t\t(thermal_bridge_width {z['thermal_bridge']})
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t{pts_str}
\t\t\t)
\t\t)
\t)""")

# Insert before final closing parenthesis
last_paren_idx = content.rfind(")")
new_content = content[:last_paren_idx] + "\n" + "\n".join(zone_sexprs) + "\n)\n"

with open(PCB_FILE, "w") as f:
    f.write(new_content)

print(f"Added {len(zones)} copper zones successfully.")
