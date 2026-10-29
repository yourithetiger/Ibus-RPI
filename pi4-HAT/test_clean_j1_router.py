import pcbnew
import heapq
import math
import shutil

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
shutil.copy('/tmp/test_backup.kicad_pcb', BOARD_PATH)
board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

# 1. 5 Planes
def add_plane(net_name, layer_name, pts, priority=1):
    net = board.FindNet(net_name)
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

add_plane('GND', 'In1.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=1)
add_plane('+5V', 'In2.Cu', [(100.5, 50.5), (175.0, 50.5), (175.0, 75.0), (199.5, 75.0), (199.5, 114.5), (100.5, 114.5)], priority=1)
add_plane('KL30', 'In2.Cu', [(175.0, 50.5), (199.5, 50.5), (199.5, 75.0), (175.0, 75.0)], priority=1)
add_plane('GND', 'F.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=0)
add_plane('GND', 'B.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=0)

# Grid parameters for B.Cu routing
X_MIN, X_MAX = 100.0, 200.0
Y_MIN, Y_MAX = 50.0, 115.0
GRID_RES = 0.5

W_CELLS = int(round((X_MAX - X_MIN) / GRID_RES)) + 1
H_CELLS = int(round((Y_MAX - Y_MIN) / GRID_RES)) + 1

def to_grid(x, y):
    gx = int(round((x - X_MIN) / GRID_RES))
    gy = int(round((y - Y_MIN) / GRID_RES))
    return max(0, min(W_CELLS - 1, gx)), max(0, min(H_CELLS - 1, gy))

def to_coord(gx, gy):
    return round(X_MIN + gx * GRID_RES, 2), round(Y_MIN + gy * GRID_RES, 2)

# B.Cu obstacle map: obstacles[(gx, gy)] = net_code
obstacles_bcu = {}

# Populate THT pad obstacles on B.Cu
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            pos = pad.GetPosition()
            px = pos.x / 1e6
            py = pos.y / 1e6
            net_code = pad.GetNetCode()
            size = pad.GetSize()
            pad_radius = max(size.x, size.y) / 2e6
            # Total clearance radius: pad_radius + 0.20 (clearance) + 0.125 (half track) = pad_radius + 0.325mm
            clr_radius = pad_radius + 0.35
            
            gx0, gy0 = to_grid(px - clr_radius, py - clr_radius)
            gx1, gy1 = to_grid(px + clr_radius, py + clr_radius)
            
            for gx in range(gx0, gx1 + 1):
                for gy in range(gy0, gy1 + 1):
                    cx, cy = to_coord(gx, gy)
                    dist = math.hypot(cx - px, cy - py)
                    if dist <= clr_radius:
                        key = (gx, gy)
                        if dist <= pad_radius:
                            obstacles_bcu[key] = net_code
                        else:
                            obstacles_bcu[key] = -1

print(f"B.Cu obstacle map initialized with {len(obstacles_bcu)} cells.")

def a_star_bcu(start_coord, end_coord, net_code):
    start_gx, start_gy = to_grid(*start_coord)
    end_gx, end_gy = to_grid(*end_coord)
    
    start_state = (start_gx, start_gy)
    open_set = []
    heapq.heappush(open_set, (0, 0, start_gx, start_gy))
    came_from = {}
    g_score = {start_state: 0}
    
    dirs = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
    ]
    
    found = None
    while open_set:
        f, current_g, gx, gy = heapq.heappop(open_set)
        curr = (gx, gy)
        
        if (gx, gy) == (end_gx, end_gy):
            found = curr
            break
            
        if current_g > g_score.get(curr, float('inf')):
            continue
            
        for dx, dy, cost in dirs:
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < W_CELLS and 0 <= ny < H_CELLS:
                neighbor = (nx, ny)
                obs = obstacles_bcu.get(neighbor)
                if obs is not None and obs != net_code and obs != 0:
                    continue # Blocked
                    
                tentative_g = current_g + cost
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = curr
                    g_score[neighbor] = tentative_g
                    h = math.hypot(nx - end_gx, ny - end_gy)
                    heapq.heappush(open_set, (tentative_g + h, tentative_g, nx, ny))
                    
    if not found:
        return None
        
    path = []
    curr = found
    while curr in came_from:
        path.append(curr)
        curr = came_from[curr]
    path.append(start_state)
    path.reverse()
    
    # Mark path + clearance in B.Cu obstacle map
    for gx, gy in path:
        obstacles_bcu[(gx, gy)] = net_code
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                k = (gx + dx, gy + dy)
                if k not in obstacles_bcu or obstacles_bcu[k] != net_code:
                    obstacles_bcu[k] = -1
                    
    return path

# 19 J1 signals
j1_signals = [
    ("GPIO14/TXD0", "U2", "11", "8", (1.5, 0.0)),
    ("GPIO15/RXD0", "R8", "2", "10", (0.0, 1.2)),
    ("GPIO18/PCM.CLK", "U4", "21", "12", (1.5, 0.0)),
    ("GPIO19/PCM.FS", "U4", "23", "35", (1.5, 0.0)),
    ("GPIO21/PCM.DOUT", "U4", "22", "40", (1.5, 0.0)),
    ("GPIO2/SDA1", "U4", "11", "3", (-1.5, 0.0)),
    ("GPIO3/SCL1", "U4", "12", "5", (-1.5, 0.0)),
    ("GPIO16", "R11", "1", "36", (0.0, -1.2)),
    ("GPIO17", "R41", "1", "11", (0.0, 1.2)),
    ("GPIO22", "D3", "2", "15", (1.2, 0.0)),
    ("GPIO23", "R39", "1", "16", (0.0, 1.2)),
    ("GPIO24", "D11", "2", "18", (1.2, 0.0)),
    ("GPIO25", "D9", "2", "22", (1.2, 0.0)),
    ("GPIO26", "R37", "2", "37", (0.0, -1.2)),
    ("GPIO12/PWM0", "R27", "1", "32", (0.0, 1.2)),
    ("GPIO13/PWM1", "R22", "2", "33", (0.0, -1.2)),
    ("ID_SDA", "U1", "5", "27", (1.5, 0.0)),
    ("ID_SCL", "U1", "6", "28", (1.5, 0.0)),
    ("RELAY_CTRL", "R16", "1", "13", (0.0, 1.2))
]

j1 = board.FindFootprintByReference("J1")
routed = 0

for net_name, src_ref, src_pin_num, j1_pin_num, via_offset in j1_signals:
    net = board.FindNet(net_name) or board.FindNet(net_name.replace('/', '{slash}'))
    src_fp = board.FindFootprintByReference(src_ref)
    src_pad = [p for p in src_fp.Pads() if p.GetNumber() == src_pin_num][0]
    j1_pad = [p for p in j1.Pads() if p.GetNumber() == j1_pin_num][0]
    
    sx = src_pad.GetPosition().x / 1e6
    sy = src_pad.GetPosition().y / 1e6
    jx = j1_pad.GetPosition().x / 1e6
    jy = j1_pad.GetPosition().y / 1e6
    
    vx = sx + via_offset[0]
    vy = sy + via_offset[1]
    
    # 1. Exit trace on F.Cu
    t_fcu = pcbnew.PCB_TRACK(board)
    t_fcu.SetStart(pcbnew.VECTOR2I(mm(sx), mm(sy)))
    t_fcu.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
    t_fcu.SetWidth(mm(0.25))
    t_fcu.SetLayer(pcbnew.F_Cu)
    t_fcu.SetNet(net)
    board.Add(t_fcu)
    
    # 2. Via from F.Cu to B.Cu
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
    via.SetWidth(mm(0.6))
    via.SetDrill(mm(0.3))
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetNet(net)
    board.Add(via)
    
    # 3. Route on B.Cu using A*
    path = a_star_bcu((vx, vy), (jx, jy), net.GetNetCode())
    if path:
        routed += 1
        print(f"  [OK] {net_name} ({len(path)} steps)")
        for i in range(len(path) - 1):
            p1 = to_coord(path[i][0], path[i][1])
            p2 = to_coord(path[i+1][0], path[i+1][1])
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(p1[0]), mm(p1[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(p2[0]), mm(p2[1])))
            t.SetWidth(mm(0.25))
            t.SetLayer(pcbnew.B_Cu)
            t.SetNet(net)
            board.Add(t)
    else:
        print(f"  [FAIL] {net_name}")

print(f"Routed {routed}/19 signals cleanly.")
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD_PATH)
