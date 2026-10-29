import pcbnew
import math

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

# List of 19 signals to J1: (net_name, start_pad_ref, start_pin, j1_pin)
j1_signals = [
    ("GPIO14/TXD0", "U2", "11", "8"),
    ("GPIO15/RXD0", "R8", "2", "10"),
    ("GPIO18/PCM.CLK", "U4", "21", "12"),
    ("GPIO19/PCM.FS", "U4", "23", "35"),
    ("GPIO21/PCM.DOUT", "U4", "22", "40"),
    ("GPIO2/SDA1", "U4", "11", "3"),
    ("GPIO3/SCL1", "U4", "12", "5"),
    ("GPIO16", "R11", "1", "36"),
    ("GPIO17", "R41", "1", "11"),
    ("GPIO22", "D3", "2", "15"),
    ("GPIO23", "R39", "1", "16"),
    ("GPIO24", "D11", "2", "18"),
    ("GPIO25", "D9", "2", "22"),
    ("GPIO26", "R37", "2", "37"),
    ("GPIO12/PWM0", "R27", "1", "32"),
    ("GPIO13/PWM1", "R22", "2", "33"),
    ("ID_SDA", "U1", "5", "27"),
    ("ID_SCL", "U1", "6", "28"),
    ("RELAY_CTRL", "R16", "1", "13")
]

j1 = board.FindFootprintByReference("J1")

routes_done = 0
for net_name, src_ref, src_pin_num, j1_pin_num in j1_signals:
    net = board.FindNet(net_name) or board.FindNet(net_name.replace('/', '{slash}'))
    if not net:
        print(f"Net {net_name} not found!")
        continue
    src_fp = board.FindFootprintByReference(src_ref)
    if not src_fp:
        continue
    src_pad = [p for p in src_fp.Pads() if p.GetNumber() == src_pin_num][0]
    j1_pad = [p for p in j1.Pads() if p.GetNumber() == j1_pin_num][0]
    
    sx = src_pad.GetPosition().x / 1e6
    sy = src_pad.GetPosition().y / 1e6
    jx = j1_pad.GetPosition().x / 1e6
    jy = j1_pad.GetPosition().y / 1e6
    
    # Via position near source pad: offset by 1.2mm towards J1 X or outward
    vx = sx + (0.8 if jx > sx else -0.8)
    vy = sy - 1.2 # slightly north towards J1
    
    # 1. Track on F.Cu from source pad to via
    t1 = pcbnew.PCB_TRACK(board)
    t1.SetStart(pcbnew.VECTOR2I(mm(sx), mm(sy)))
    t1.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
    t1.SetWidth(mm(0.25))
    t1.SetLayer(pcbnew.F_Cu)
    t1.SetNet(net)
    board.Add(t1)
    
    # 2. Via from F.Cu to B.Cu
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
    via.SetWidth(mm(0.6))
    via.SetDrill(mm(0.3))
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetNet(net)
    board.Add(via)
    
    # 3. Track on B.Cu: dogleg to jx, then straight north to jy
    # Segment A on B.Cu: from (vx, vy) to (jx, vy - abs(jx - vx))
    mid_y = max(jy + 2.0, vy - 2.0)
    t2 = pcbnew.PCB_TRACK(board)
    t2.SetStart(pcbnew.VECTOR2I(mm(vx), mm(vy)))
    t2.SetEnd(pcbnew.VECTOR2I(mm(jx), mm(mid_y)))
    t2.SetWidth(mm(0.25))
    t2.SetLayer(pcbnew.B_Cu)
    t2.SetNet(net)
    board.Add(t2)
    
    # Segment B on B.Cu: from (jx, mid_y) straight north to (jx, jy)
    t3 = pcbnew.PCB_TRACK(board)
    t3.SetStart(pcbnew.VECTOR2I(mm(jx), mm(mid_y)))
    t3.SetEnd(pcbnew.VECTOR2I(mm(jx), mm(jy)))
    t3.SetWidth(mm(0.25))
    t3.SetLayer(pcbnew.B_Cu)
    t3.SetNet(net)
    board.Add(t3)
    
    routes_done += 1
    print(f"Routed {net_name} to J1 pin {j1_pin_num}")

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD_PATH)
print(f"Successfully routed {routes_done}/19 signals to J1 header.")
