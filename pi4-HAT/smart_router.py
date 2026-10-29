import pcbnew
import math
import shutil

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
BACKUP_PATH = '/tmp/test_backup.kicad_pcb'

def mm(v):
    return pcbnew.FromMM(v)

print("1. Restoring clean board baseline...")
shutil.copy(BACKUP_PATH, BOARD_PATH)
board = pcbnew.LoadBoard(BOARD_PATH)

# Clear existing zones
for z in list(board.Zones()):
    board.Remove(z)

print("2. Configuring 4-layer power & ground planes...")
def add_plane(net_name, layer_name, pts, priority=1):
    net = board.FindNet(net_name)
    if not net:
        print(f"ERROR: Net {net_name} not found!")
        return None
    zone = pcbnew.ZONE(board)
    zone.SetNet(net)
    zone.SetLayer(board.GetLayerID(layer_name))
    zone.SetAssignedPriority(priority)
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    poly = zone.Outline()
    poly.NewOutline()
    for x, y in pts:
        poly.Append(mm(x), mm(y))
    board.Add(zone)
    return zone

# In1.Cu: 100% continuous GND plane
add_plane('GND', 'In1.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=1)
# In2.Cu: Main +5V plane
add_plane('+5V', 'In2.Cu', [(100.5, 50.5), (175.0, 50.5), (175.0, 75.0), (199.5, 75.0), (199.5, 114.5), (100.5, 114.5)], priority=1)
# In2.Cu: KL30 (+12V inlet in top-right)
add_plane('KL30', 'In2.Cu', [(175.0, 50.5), (199.5, 50.5), (199.5, 75.0), (175.0, 75.0)], priority=1)
# F.Cu & B.Cu GND pours
add_plane('GND', 'F.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=0)
add_plane('GND', 'B.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=0)

board.Save(BOARD_PATH)
print("Board initialized with 5 planes.")
