import pcbnew

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
board = pcbnew.LoadBoard(BOARD_PATH)

def pt(x, y):
    return pcbnew.VECTOR2I(int(x * 1e6), int(y * 1e6))

net_12v = board.FindNet('+12V_IN')

# 1. Connect FL1.2 to U3.3
pts_fl1_u3 = [(175.25, 61.5), (161.0, 61.5), (159.14, 64.95)]
for i in range(len(pts_fl1_u3) - 1):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(pts_fl1_u3[i][0], pts_fl1_u3[i][1]))
    t.SetEnd(pt(pts_fl1_u3[i+1][0], pts_fl1_u3[i+1][1]))
    t.SetWidth(int(0.8 * 1e6))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(net_12v)
    board.Add(t)

# 2. Connect U3.3 to U2.15
pts_u3_u2 = [(159.14, 64.95), (155.0, 69.0), (153.47, 73.83)]
for i in range(len(pts_u3_u2) - 1):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(pts_u3_u2[i][0], pts_u3_u2[i][1]))
    t.SetEnd(pt(pts_u3_u2[i+1][0], pts_u3_u2[i+1][1]))
    t.SetWidth(int(0.5 * 1e6))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(net_12v)
    board.Add(t)

# 3. Connect U2.15 to C2.1
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(153.47, 73.83))
t.SetEnd(pt(161.22, 83.0))
t.SetWidth(int(0.4 * 1e6))
t.SetLayer(pcbnew.B_Cu)
t.SetNet(net_12v)
board.Add(t)

# 4. Connect U2.1 to C3.1
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(148.53, 72.56))
t.SetEnd(pt(141.22, 82.0))
t.SetWidth(int(0.4 * 1e6))
t.SetLayer(pcbnew.B_Cu)
t.SetNet(net_12v)
board.Add(t)

# 5. Connect C3.1 to SW_BENCH.1
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(141.22, 82.0))
t.SetEnd(pt(126.31, 71.0))
t.SetWidth(int(0.4 * 1e6))
t.SetLayer(pcbnew.B_Cu)
t.SetNet(net_12v)
board.Add(t)

# Remove all isolated copper islands on all zones
for z in board.Zones():
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD_PATH)
print("Connected +12V_IN cleanly and refilled zones.")
