import pcbnew

BOARD_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb"
board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

for fp in board.GetFootprints():
    ref = fp.Reference()
    val = fp.Value()
    
    # Hide values from silkscreen
    val.SetVisible(False)
    
    # Minimum compliant text size in KiCad constraints: 0.8mm x 0.8mm
    ref.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    ref.SetTextThickness(mm(0.12))
    
    fp_pos = fp.GetPosition()
    fp_x = fp_pos.x / 1e6
    fp_y = fp_pos.y / 1e6
    ref_name = ref.GetText()
    
    if ref_name.startswith("MH"):
        ref.SetVisible(False)
    elif ref_name == "J1":
        # Centered above the 40-pin header
        ref.SetPosition(pcbnew.VECTOR2I(mm(137.0), mm(52.5)))
    elif ref_name.startswith("J_CAR") or ref_name == "J_TEL":
        ref.SetPosition(pcbnew.VECTOR2I(mm(fp_x - 6.0), mm(fp_y)))
    elif ref_name in ["J_RCA_CAM", "J_RCA_TV", "J_PI_VID", "J_REV", "J_TV_TRIG", "J_MIC"]:
        ref.SetPosition(pcbnew.VECTOR2I(mm(fp_x), mm(fp_y - 5.0)))
    elif ref_name in ["SW_DVR_CFG", "J_DVR", "J_FAN"]:
        ref.SetPosition(pcbnew.VECTOR2I(mm(fp_x + 5.5), mm(fp_y)))
    else:
        # Default offset
        ref.SetPosition(pcbnew.VECTOR2I(mm(fp_x), mm(fp_y - 1.8)))

board.Save(BOARD_PATH)
print("Updated silkscreen.")
