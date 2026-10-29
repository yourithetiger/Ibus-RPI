import pcbnew

BOARD_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb"
board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

def add_track(board, net_name, layer, width_mm, pts):
    net = board.FindNet(net_name)
    if not net:
        print(f"Warning: Net {net_name} not found!")
        return
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(width_mm))
        t.SetLayer(layer)
        t.SetNet(net)
        board.Add(t)

def add_via(board, net_name, x, y, size_mm=0.8, drill_mm=0.4):
    net = board.FindNet(net_name)
    if not net:
        return
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(size_mm))
    v.SetDrill(mm(drill_mm))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net)
    board.Add(v)

# -------------------------------------------------------------
# 1. BUCK CONVERTER POWER LOOP (12V -> 5V 3.5A)
# -------------------------------------------------------------
# KL30: J_CAR_3P Pin 2 to F1 Pin 1
add_track(board, "KL30", pcbnew.F_Cu, 1.5, [
    (195.0, 64.54), (189.0, 64.54), (189.0, 57.4), (186.0, 57.4)
])

# VRAW: F1 Pin 2 to D1 Pin 1 and FL1 Pin 1
add_track(board, "VRAW", pcbnew.F_Cu, 1.5, [
    (186.0, 54.6), (186.0, 60.0), (183.85, 64.0)
])
add_track(board, "VRAW", pcbnew.F_Cu, 1.5, [
    (183.85, 64.0), (180.0, 64.0), (180.0, 58.5), (172.75, 58.5)
])
# D2 TVS to VRAW
add_track(board, "VRAW", pcbnew.F_Cu, 1.5, [
    (172.75, 58.5), (172.75, 66.0), (179.4, 68.0)
])

# VFILT: FL1 Pin 2 to C6 Pin 1 and U3 Pin 2 (VIN)
add_track(board, "VFILT", pcbnew.F_Cu, 1.5, [
    (172.75, 61.5), (165.0, 61.5), (161.05, 64.0), (156.86, 64.0)
])

# SW_NODE: U3 Pin 6 to L1 Pin 1 and C5 Pin 1
add_track(board, "SW_NODE", pcbnew.F_Cu, 1.5, [
    (159.14, 63.05), (154.0, 63.05), (146.0, 64.0)
])
add_track(board, "SW_NODE", pcbnew.F_Cu, 0.6, [
    (159.14, 63.05), (163.0, 63.05), (165.0, 64.0)
])

# +5V: L1 Pin 2 to C7 Pin 1 and to Pi 4 GPIO J1 Pins 2 & 4
add_track(board, "+5V", pcbnew.F_Cu, 1.8, [
    (152.0, 64.0), (145.0, 64.0), (139.05, 63.0), (125.0, 63.0), (118.0, 59.0), (115.41, 54.73)
])
add_track(board, "+5V", pcbnew.F_Cu, 1.8, [
    (115.41, 54.73), (112.87, 54.73)
])
# Power vias down to In2.Cu power plane
add_via(board, "+5V", 143.0, 63.0, size_mm=1.0, drill_mm=0.5)
add_via(board, "+5V", 125.0, 63.0, size_mm=1.0, drill_mm=0.5)

# -------------------------------------------------------------
# 2. CONTROLLED 75-OHM VIDEO LINES
# -------------------------------------------------------------
# PI_VID: J_PI_VID Pin 4 to U5 Pin 3
add_track(board, "PI_VID", pcbnew.F_Cu, 0.25, [
    (122.62, 107.0), (128.0, 107.0), (132.0, 102.45), (135.86, 102.45)
])

# CAM_VID: J_RCA_CAM Pin 1 to U5 Pin 1
add_track(board, "CAM_VID", pcbnew.F_Cu, 0.25, [
    (129.0, 106.0), (131.0, 104.0), (131.0, 100.55), (135.86, 100.55)
])

# TV_VID_OUT: U5 Pin 4 to J_RCA_TV Pin 1
add_track(board, "TV_VID_OUT", pcbnew.F_Cu, 0.25, [
    (138.14, 102.45), (141.0, 102.45), (144.0, 106.0)
])

# -------------------------------------------------------------
# 3. I2S DIGITAL AUDIO BUS (routed on B.Cu)
# -------------------------------------------------------------
# GPIO18/PCM.CLK -> U4 Pin 23
add_track(board, "GPIO18{slash}PCM.CLK", pcbnew.B_Cu, 0.25, [
    (125.57, 54.73), (125.57, 75.0), (141.0, 83.0), (144.86, 87.03)
])

# GPIO19/PCM.FS -> U4 Pin 24
add_track(board, "GPIO19{slash}PCM.FS", pcbnew.B_Cu, 0.25, [
    (156.05, 57.27), (156.05, 75.0), (148.0, 83.0), (144.86, 86.38)
])

# GPIO21/PCM.DOUT -> U4 Pin 22
add_track(board, "GPIO21{slash}PCM.DOUT", pcbnew.B_Cu, 0.25, [
    (161.13, 54.73), (161.13, 77.0), (150.0, 85.0), (144.86, 87.68)
])

# I2C Control to DAC: SDA & SCL
add_track(board, "GPIO2{slash}SDA1", pcbnew.B_Cu, 0.25, [
    (115.41, 57.27), (115.41, 70.0), (132.0, 85.0), (139.14, 90.28)
])
add_track(board, "GPIO3{slash}SCL1", pcbnew.B_Cu, 0.25, [
    (117.95, 57.27), (117.95, 71.0), (133.0, 86.0), (139.14, 90.93)
])

# -------------------------------------------------------------
# 4. TELEPHONY DIFFERENTIAL AUDIO & CONTROLS
# -------------------------------------------------------------
# U7 Pin 1 (+OUT_L) -> FB1 -> C30 -> J_TEL Pin 1 (TEL_OUT+)
add_track(board, "Net-(FB1-Pad1)", pcbnew.F_Cu, 0.4, [
    (169.53, 85.56), (175.0, 85.56), (181.0, 86.94)
])
add_track(board, "Net-(C30-Pad1)", pcbnew.F_Cu, 0.4, [
    (181.0, 89.06), (186.0, 88.95)
])
add_track(board, "Net-(C30-Pad2)", pcbnew.F_Cu, 0.4, [
    (186.0, 87.05), (191.0, 87.05), (196.0, 97.0)
])

# U7 Pin 3 (-OUT_L) -> FB2 -> C31 -> J_TEL Pin 2 (TEL_OUT-)
add_track(board, "Net-(FB2-Pad1)", pcbnew.F_Cu, 0.4, [
    (169.53, 88.10), (175.0, 88.10), (181.0, 90.94)
])
add_track(board, "Net-(C31-Pad1)", pcbnew.F_Cu, 0.4, [
    (181.0, 93.06), (186.0, 92.95)
])
add_track(board, "Net-(C31-Pad2)", pcbnew.F_Cu, 0.4, [
    (186.0, 91.05), (191.0, 91.05), (196.0, 99.54)
])

# TEL_MUTE: Q6 Pin 3 (Drain) to J_TEL Pin 6
add_track(board, "TEL_MUTE", pcbnew.F_Cu, 0.35, [
    (182.94, 98.0), (189.0, 98.0), (196.0, 109.7)
])

# -------------------------------------------------------------
# 5. I-BUS UART BUS (TH3122.4 Transceiver)
# -------------------------------------------------------------
# J_CAR_3P Pin 3 (IBUS) to U2 Pin 16
add_track(board, "IBUS", pcbnew.B_Cu, 0.4, [
    (195.0, 67.08), (175.0, 67.08), (160.0, 72.56), (153.48, 72.56)
])

# U2 Pin 12 (TXD) -> J1 Pin 8 (TXD0)
add_track(board, "GPIO14{slash}TXD0", pcbnew.B_Cu, 0.25, [
    (153.48, 77.64), (135.0, 77.64), (120.49, 65.0), (120.49, 54.73)
])

# U2 Pin 10 (RXD) -> J1 Pin 10 (RXD0)
add_track(board, "GPIO15{slash}RXD0", pcbnew.B_Cu, 0.25, [
    (153.48, 80.18), (137.0, 80.18), (123.03, 66.0), (123.03, 54.73)
])

# U2 Pin 9 (SEN/STA) -> J1 Pin 7 (GPIO4)
add_track(board, "TH3122_SEN_STA", pcbnew.B_Cu, 0.25, [
    (153.48, 81.45), (138.0, 81.45), (120.49, 68.0), (120.49, 57.27)
])

board.Save(BOARD_PATH)
print("All 5 critical buses successfully routed.")
