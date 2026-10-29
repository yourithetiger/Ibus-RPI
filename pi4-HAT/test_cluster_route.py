import pcbnew
import math

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

# Test routing local nets of buck converter
# U3.6 to C5.1 (BOOT_NODE)
# U3.2 to C5.2 and L1.1 (SW_NODE)
# D2.1 to FL1.1 (VFILT)

routes = [
    ("BOOT_NODE", (159.14, 63.05), (165.22, 64.0), 0.3, pcbnew.F_Cu),
    ("SW_NODE", (156.86, 64.0), (166.78, 64.0), 0.8, pcbnew.F_Cu),
    ("SW_NODE", (156.86, 64.0), (146.0, 64.0), 1.0, pcbnew.F_Cu),
    ("VFILT", (172.6, 68.0), (172.75, 58.5), 1.0, pcbnew.F_Cu),
]

for net_name, pt1, pt2, width, layer in routes:
    net = board.FindNet(net_name)
    if not net:
        print(f"Net {net_name} not found!")
        continue
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(pt1[0]), mm(pt1[1])))
    t.SetEnd(pcbnew.VECTOR2I(mm(pt2[0]), mm(pt2[1])))
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    print(f"Added track for {net_name}")

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD_PATH)
print("Saved.")
