import pcbnew
import heapq
import math
import shutil

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
# Restore clean board with 5 planes
shutil.copy('/tmp/test_backup.kicad_pcb', BOARD_PATH)

board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

# Re-inject 5 planes
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

# Grid parameters
X_MIN, X_MAX = 100.0, 200.0
Y_MIN, Y_MAX = 50.0, 115.0
GRID_RES = 0.5  # 0.5mm grid

W_CELLS = int(round((X_MAX - X_MIN) / GRID_RES)) + 1
H_CELLS = int(round((Y_MAX - Y_MIN) / GRID_RES)) + 1

def to_grid(x, y):
    gx = int(round((x - X_MIN) / GRID_RES))
    gy = int(round((y - Y_MIN) / GRID_RES))
    return max(0, min(W_CELLS - 1, gx)), max(0, min(H_CELLS - 1, gy))

def to_coord(gx, gy):
    return round(X_MIN + gx * GRID_RES, 2), round(Y_MIN + gy * GRID_RES, 2)

print(f"Grid initialized: {W_CELLS} x {H_CELLS} x 2 layers")

# Build obstacle map
# Layer 0 = F.Cu, Layer 1 = B.Cu
# obstacles[(layer, gx, gy)] = net_code (or -1 if clearance zone / edge)
obstacles = {}

for fp in board.GetFootprints():
    for pad in fp.Pads():
        pos = pad.GetPosition()
        px = pos.x / 1e6
        py = pos.y / 1e6
        net_code = pad.GetNetCode()
        size = pad.GetSize()
        radius = max(size.x, size.y) / 2e6 + 0.35
        
        gx0, gy0 = to_grid(px - radius, py - radius)
        gx1, gy1 = to_grid(px + radius, py + radius)
        
        # THT blocks both F.Cu and B.Cu, SMD blocks only F.Cu
        layers = [0, 1] if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else [0]
        for l in layers:
            for gx in range(gx0, gx1 + 1):
                for gy in range(gy0, gy1 + 1):
                    cx, cy = to_coord(gx, gy)
                    if (cx - px)**2 + (cy - py)**2 <= radius**2:
                        key = (l, gx, gy)
                        # If inside pad body, mark as net_code
                        if (cx - px)**2 + (cy - py)**2 <= (radius - 0.3)**2:
                            obstacles[key] = net_code
                        else:
                            # Clearance zone around pad: impassable for other nets
                            if key not in obstacles:
                                obstacles[key] = -1

print("Obstacle map built.")

def a_star(start_coord, end_coord, net_code, pref_layer=1):
    start_gx, start_gy = to_grid(*start_coord)
    end_gx, end_gy = to_grid(*end_coord)
    
    start_state = (0, start_gx, start_gy)
    
    open_set = []
    heapq.heappush(open_set, (0, 0, 0, start_gx, start_gy))
    came_from = {}
    g_score = {start_state: 0}
    
    dirs = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
    ]
    
    found = None
    while open_set:
        f, current_g, l, gx, gy = heapq.heappop(open_set)
        curr = (l, gx, gy)
        
        if (gx, gy) == (end_gx, end_gy):
            found = curr
            break
            
        if current_g > g_score.get(curr, float('inf')):
            continue
            
        for dx, dy, cost in dirs:
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < W_CELLS and 0 <= ny < H_CELLS:
                neighbor = (l, nx, ny)
                obs = obstacles.get(neighbor)
                if obs is not None and obs != net_code and obs != 0:
                    continue # Blocked
                # Prefer B.Cu for long runs by reducing cost on B.Cu
                move_cost = cost * (0.8 if l == 1 else 1.2)
                tentative_g = current_g + move_cost
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = curr
                    g_score[neighbor] = tentative_g
                    h = math.hypot(nx - end_gx, ny - end_gy)
                    heapq.heappush(open_set, (tentative_g + h, tentative_g, l, nx, ny))
                    
        # Via to other layer (cost: 3.0)
        other_l = 1 - l
        via_state = (other_l, gx, gy)
        obs_via = obstacles.get(via_state)
        if obs_via is None or obs_via == net_code:
            tentative_g = current_g + 3.0
            if tentative_g < g_score.get(via_state, float('inf')):
                came_from[via_state] = curr
                g_score[via_state] = tentative_g
                h = math.hypot(gx - end_gx, gy - end_gy)
                heapq.heappush(open_set, (tentative_g + h, tentative_g, other_l, gx, gy))
                
    if not found:
        return None
        
    path = []
    curr = found
    while curr in came_from:
        path.append(curr)
        curr = came_from[curr]
    path.append(start_state)
    path.reverse()
    
    # Mark path in obstacle map
    for l, gx, gy in path:
        obstacles[(l, gx, gy)] = net_code
        # Mark neighbor cells as clearance keepout
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                k = (l, gx + dx, gy + dy)
                if k not in obstacles:
                    obstacles[k] = -1
                    
    return path

# Test routing the 19 J1 signals
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
routed = 0
for net_name, src_ref, src_pin_num, j1_pin_num in j1_signals:
    net = board.FindNet(net_name) or board.FindNet(net_name.replace('/', '{slash}'))
    src_fp = board.FindFootprintByReference(src_ref)
    src_pad = [p for p in src_fp.Pads() if p.GetNumber() == src_pin_num][0]
    j1_pad = [p for p in j1.Pads() if p.GetNumber() == j1_pin_num][0]
    
    start_pt = (src_pad.GetPosition().x / 1e6, src_pad.GetPosition().y / 1e6)
    end_pt = (j1_pad.GetPosition().x / 1e6, j1_pad.GetPosition().y / 1e6)
    
    path = a_star(start_pt, end_pt, net.GetNetCode())
    if path:
        routed += 1
        print(f"  [OK] {net_name} ({len(path)} steps)")
        # Apply track segments to board
        curr_l, start_gx, start_gy = path[0]
        seg_pts = [to_coord(start_gx, start_gy)]
        for i in range(1, len(path)):
            l, gx, gy = path[i]
            coord = to_coord(gx, gy)
            if l != curr_l:
                # Add track
                for j in range(len(seg_pts) - 1):
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pcbnew.VECTOR2I(mm(seg_pts[j][0]), mm(seg_pts[j][1])))
                    t.SetEnd(pcbnew.VECTOR2I(mm(seg_pts[j+1][0]), mm(seg_pts[j+1][1])))
                    t.SetWidth(mm(0.25))
                    t.SetLayer(pcbnew.F_Cu if curr_l == 0 else pcbnew.B_Cu)
                    t.SetNet(net)
                    board.Add(t)
                # Add via
                vx, vy = seg_pts[-1]
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                via.SetWidth(mm(0.6))
                via.SetDrill(mm(0.3))
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetNet(net)
                board.Add(via)
                curr_l = l
                seg_pts = [coord]
            else:
                seg_pts.append(coord)
        if len(seg_pts) >= 2:
            for j in range(len(seg_pts) - 1):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(seg_pts[j][0]), mm(seg_pts[j][1])))
                t.SetEnd(pcbnew.VECTOR2I(mm(seg_pts[j+1][0]), mm(seg_pts[j+1][1])))
                t.SetWidth(mm(0.25))
                t.SetLayer(pcbnew.F_Cu if curr_l == 0 else pcbnew.B_Cu)
                t.SetNet(net)
                board.Add(t)
    else:
        print(f"  [FAIL] {net_name}")

print(f"Routed {routed}/19 signals via dynamic A*.")
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD_PATH)
