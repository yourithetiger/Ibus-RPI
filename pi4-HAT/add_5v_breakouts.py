import pcbnew
import math

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

net_5v = board.FindNet('+5V')

pads_5v = [
    ('C23', '1', (-1.0, 0.0)),
    ('C6', '1', (1.0, 0.0)),
    ('C24', '1', (1.0, 0.0)),
    ('C7', '1', (-1.0, 0.0)),
    ('U5', '5', (1.2, 0.0)),
    ('R13', '2', (0.0, -1.0)),
    ('U7', '5', (-1.2, 0.0)),
    ('U7', '9', (0.0, 1.2)),
    ('D10', '1', (-1.0, 0.0)),
    ('L1', '2', (1.5, 0.0)),
    ('R3', '1', (0.0, 1.0)),
    ('D7', '1', (-1.0, 0.0)),
    ('R44', '1', (-1.0, 0.0))
]

for ref, pin, (dx, dy) in pads_5v:
    fp = board.FindFootprintByReference(ref)
    p = [pad for pad in fp.Pads() if pad.GetNumber() == pin][0]
    px = p.GetPosition().x / 1e6
    py = p.GetPosition().y / 1e6
    
    vx = px + dx
    vy = py + dy
    
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
    via.SetWidth(mm(0.6))
    via.SetDrill(mm(0.3))
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetNet(net_5v)
    board.Add(via)
    
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I(mm(px), mm(py)))
    track.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
    track.SetWidth(mm(0.35))
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(net_5v)
    board.Add(track)
    print(f"Added +5V via for {ref}.{pin} at ({vx:.2f}, {vy:.2f})")

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD_PATH)
print("Saved +5V breakouts and refilled zones.")
