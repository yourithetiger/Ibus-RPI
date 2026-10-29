import pcbnew
import math

BOARD_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb"
BACKUP_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb.bak_layout"

board = pcbnew.LoadBoard(BOARD_PATH)
board.Save(BACKUP_PATH)

def mm(val):
    return pcbnew.FromMM(val)

# 1. Clear old Edge.Cuts drawings
drawings = list(board.GetDrawings())
for d in drawings:
    if d.GetLayerName() == "Edge.Cuts":
        board.Remove(d)

print("Cleared old Edge.Cuts.")

# 2. Add 100 x 65 mm outline with 3mm rounded corners
# X: 100.0 to 200.0
# Y: 50.0 to 115.0
X0, Y0 = 100.0, 50.0
W, H = 100.0, 65.0
R = 3.0

def add_line(x1, y1, x2, y2):
    line = pcbnew.PCB_SHAPE()
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetLayer(pcbnew.Edge_Cuts)
    line.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    line.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    line.SetWidth(mm(0.1))
    board.Add(line)

def add_arc(cx, cy, start_angle_deg, end_angle_deg):
    arc = pcbnew.PCB_SHAPE()
    arc.SetShape(pcbnew.SHAPE_T_ARC)
    arc.SetLayer(pcbnew.Edge_Cuts)
    arc.SetWidth(mm(0.1))
    
    rad1 = math.radians(start_angle_deg)
    rad_mid = math.radians((start_angle_deg + end_angle_deg) / 2.0)
    rad2 = math.radians(end_angle_deg)
    
    # In KiCad screen coords: Y is DOWN. 
    p_start = pcbnew.VECTOR2I(mm(cx + R * math.cos(rad1)), mm(cy + R * math.sin(rad1)))
    p_mid = pcbnew.VECTOR2I(mm(cx + R * math.cos(rad_mid)), mm(cy + R * math.sin(rad_mid)))
    p_end = pcbnew.VECTOR2I(mm(cx + R * math.cos(rad2)), mm(cy + R * math.sin(rad2)))
    
    arc.SetArcGeometry(p_start, p_mid, p_end)
    board.Add(arc)

# 4 straight segments
add_line(X0 + R, Y0, X0 + W - R, Y0) # Top
add_line(X0 + W, Y0 + R, X0 + W, Y0 + H - R) # Right
add_line(X0 + W - R, Y0 + H, X0 + R, Y0 + H) # Bottom
add_line(X0, Y0 + H - R, X0, Y0 + R) # Left

# 4 corner arcs
add_arc(X0 + W - R, Y0 + R, -90, 0) # Top-Right
add_arc(X0 + W - R, Y0 + H - R, 0, 90) # Bottom-Right
add_arc(X0 + R, Y0 + H - R, 90, 180) # Bottom-Left
add_arc(X0 + R, Y0 + R, 180, 270) # Top-Left

print("Added 100 x 65 mm board outline with 3mm fillets.")

# 3. Position and rotate footprints
# Raspberry Pi 4 mounting reference:
# MH1 (TL) at (108.0, 56.0)
# MH2 (TR) at (166.0, 56.0)
# MH3 (BL) at (108.0, 105.0)
# MH4 (BR) at (166.0, 105.0)
# J1 (40-pin) Pin 1 at (112.87, 58.54) (so Pin 2 is at Y=56.0)

placements = {
    # Mechanical & Headers
    "MH1": (108.0, 56.0, 0),
    "MH2": (166.0, 56.0, 0),
    "MH3": (108.0, 105.0, 0),
    "MH4": (166.0, 105.0, 0),
    "J1": (112.87, 58.54, 0),

    # Right Edge Automotive & Phone Connectors
    "J_CAR_3P": (195.0, 62.0, 270),
    "J_CAR_6P": (195.0, 82.0, 270),
    "J_TEL": (195.0, 102.0, 270),

    # Bottom Edge AV & Camera Connectors
    "J_PI_VID": (116.0, 110.0, 0),
    "J_RCA_CAM": (132.0, 110.0, 0),
    "J_RCA_TV": (148.0, 110.0, 0),
    "J_REV": (164.0, 110.0, 0),
    "J_TV_TRIG": (176.0, 110.0, 0),
    "J_MIC": (188.0, 110.0, 0),

    # Left Edge Configuration & Auxiliary Connectors
    "SW_DVR_CFG": (104.5, 78.0, 90),
    "J_DVR": (104.5, 90.0, 90),
    "J_FAN": (104.5, 102.0, 90),

    # Power Supply Stage (TPS54302, Choke, TVS, Caps)
    "F1": (186.0, 56.0, 90),
    "D1": (186.0, 62.0, 0),
    "FL1": (178.0, 62.0, 0),
    "D2": (178.0, 56.0, 90),
    "C5": (174.0, 60.0, 0),
    "C6": (174.0, 64.0, 0),
    "U3": (168.0, 62.0, 0),
    "L1": (160.0, 62.0, 0),
    "C4": (168.0, 56.5, 0),
    "R5": (165.0, 66.0, 90),
    "R6": (165.0, 69.0, 90),
    "C7": (154.0, 60.0, 0),
    "C8": (154.0, 64.0, 0),
    "C25": (148.0, 62.0, 0),

    # I-Bus Transceiver (TH3122.4)
    "U2": (154.0, 74.0, 0),
    "D3": (161.0, 71.0, 0),
    "D4": (161.0, 75.0, 0),
    "R3": (147.0, 71.0, 90),
    "R4": (147.0, 75.0, 90),
    "C2": (154.0, 80.0, 0),
    "C3": (147.0, 79.0, 0),

    # Audio DAC & Filters (PCM5122)
    "U4": (146.0, 90.0, 0),
    "L2": (138.0, 87.0, 90),
    "C12": (138.0, 90.0, 0),
    "C13": (138.0, 93.0, 0),
    "C14": (154.0, 87.0, 0),
    "C15": (154.0, 90.0, 0),
    "C16": (154.0, 93.0, 0),
    "C17": (138.0, 96.0, 90),
    "C18": (141.0, 96.0, 90),
    "C19": (144.0, 96.0, 90),
    "C20": (147.0, 96.0, 90),
    "C21": (150.0, 96.0, 90),
    "C22": (153.0, 96.0, 90),
    "R7": (134.0, 90.0, 90),
    "R8": (134.0, 93.0, 90),
    "R9": (134.0, 96.0, 90),
    "R10": (158.0, 87.0, 90),
    "R11": (158.0, 90.0, 90),
    "R12": (158.0, 93.0, 90),
    "R13": (158.0, 96.0, 90),
    "R14": (161.0, 90.0, 90),
    "D5": (161.0, 93.0, 0),
    "R17": (156.0, 100.0, 90),
    "R18": (159.0, 100.0, 90),
    "R19": (162.0, 100.0, 90),

    # Relay K1 & Drivers
    "K1": (170.0, 82.0, 0),
    "Q1": (180.0, 80.0, 0),
    "D7": (180.0, 84.0, 0),
    "R16": (177.0, 87.0, 90),

    # Telephone Amplifier (PAM8406D) & MUTE
    "U7": (178.0, 94.0, 0),
    "FB1": (186.0, 92.0, 90),
    "FB2": (186.0, 96.0, 90),
    "C30": (190.0, 92.0, 90),
    "C31": (190.0, 96.0, 90),
    "FB3": (170.0, 94.0, 90),
    "C29": (166.0, 94.0, 90),
    "R43": (166.0, 97.0, 90),
    "C26": (174.0, 100.0, 0),
    "C27": (178.0, 100.0, 0),
    "C28": (182.0, 100.0, 0),
    "R41": (172.0, 102.0, 90),
    "R42": (175.0, 102.0, 0),
    "Q4": (186.0, 102.0, 0),
    "R39": (182.0, 104.0, 90),
    "R40": (186.0, 106.0, 0),

    # Microphone Circuit
    "R44": (191.0, 106.0, 0),
    "R45": (191.0, 109.0, 0),
    "C32": (187.0, 106.0, 0),
    "C33": (187.0, 109.0, 90),

    # Video Switch (TS5A3159) & Reverse Logic
    "U5": (140.0, 103.0, 0),
    "C23": (144.0, 103.0, 0),
    "C24": (147.0, 103.0, 0),
    "R24": (136.0, 103.0, 90),
    "R25": (136.0, 106.0, 90),
    "Q2": (154.0, 104.0, 0),
    "D8": (158.0, 102.0, 0),
    "D9": (158.0, 105.0, 0),
    "D11": (151.0, 104.0, 0),
    "D12": (151.0, 107.0, 0),
    "R22": (160.0, 108.0, 90),
    "R23": (164.0, 108.0, 90),

    # DVR Battery Cutoff (TLV3012, DMP32D4S)
    "U6": (122.0, 80.0, 0),
    "Q3": (114.0, 80.0, 0),
    "SW_BENCH": (122.0, 72.0, 0),
    "R28": (118.0, 72.0, 90),
    "R29": (115.0, 76.0, 90),
    "R30": (118.0, 76.0, 90),
    "R31": (121.0, 76.0, 90),
    "R32": (124.0, 76.0, 90),
    "R33": (127.0, 76.0, 90),
    "R34": (115.0, 84.0, 90),
    "R35": (118.0, 84.0, 90),
    "R36": (121.0, 84.0, 90),
    "R37": (124.0, 84.0, 90),
    "R38": (127.0, 84.0, 90),
    "C9": (122.0, 88.0, 0),
    "C10": (117.0, 88.0, 0),
    "C11": (114.0, 88.0, 0),

    # HAT EEPROM
    "U1": (126.0, 66.0, 0),
    "R1": (120.0, 65.0, 90),
    "R2": (120.0, 68.0, 90),
    "JP1": (126.0, 71.0, 0),
    "C1": (131.0, 66.0, 0),

    # Fan Controller
    "Q5": (110.0, 98.0, 0),
    "R26": (110.0, 94.0, 90),
    "R27": (114.0, 94.0, 90),
    "D10": (110.0, 102.0, 0),
}

placed_count = 0
for ref, (x, y, rot) in placements.items():
    fp = board.FindFootprintByReference(ref)
    if fp:
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        placed_count += 1
    else:
        print(f"Warning: footprint {ref} not found on board!")

print(f"Successfully positioned and oriented {placed_count} footprints.")

board.Save(BOARD_PATH)
print("Board saved to", BOARD_PATH)
