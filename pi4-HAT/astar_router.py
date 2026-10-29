import heapq
import math
import pcbnew

BOARD_PATH = "/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb"
board = pcbnew.LoadBoard(BOARD_PATH)

def mm(v):
    return pcbnew.FromMM(v)

# Grid parameters
X_MIN = 100.0
X_MAX = 200.0
Y_MIN = 50.0
Y_MAX = 115.0
GRID_RES = 0.5  # 0.5mm step for fast and clean routing

WIDTH_CELLS = int(round((X_MAX - X_MIN) / GRID_RES)) + 1
HEIGHT_CELLS = int(round((Y_MAX - Y_MIN) / GRID_RES)) + 1

def to_grid(x, y):
    gx = int(round((x - X_MIN) / GRID_RES))
    gy = int(round((y - Y_MIN) / GRID_RES))
    return max(0, min(WIDTH_CELLS - 1, gx)), max(0, min(HEIGHT_CELLS - 1, gy))

def to_coord(gx, gy):
    return round(X_MIN + gx * GRID_RES, 2), round(Y_MIN + gy * GRID_RES, 2)

# Build obstacle map for each layer: 0 = F.Cu, 1 = B.Cu
# Value stored in cell: set of netnames that are allowed (or None if impassable/edge)
print(f"Initializing grid: {WIDTH_CELLS} x {HEIGHT_CELLS} x 2 layers...")
# layer 0 = F.Cu, layer 1 = B.Cu
# We use dict for sparse obstacle map: (layer, gx, gy) -> net_code
obstacles = {}

# Populate obstacles from pads
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        pos = pad.GetPosition()
        px = pos.x / 1e6
        py = pos.y / 1e6
        net_code = pad.GetNetCode()
        
        # Clearance radius in mm
        # Through-hole blocks both layers, SMD blocks only its layer
        size = pad.GetSize()
        radius = max(size.x, size.y) / 2e6 + 0.35  # pad radius + 0.35mm clearance
        
        gx0, gy0 = to_grid(px - radius, py - radius)
        gx1, gy1 = to_grid(px + radius, py + radius)
        
        layers_blocked = [0, 1] if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else ([0] if pad.IsOnLayer(pcbnew.F_Cu) else [1])
        
        for layer in layers_blocked:
            for gx in range(gx0, gx1 + 1):
                for gy in range(gy0, gy1 + 1):
                    cx, cy = to_coord(gx, gy)
                    if (cx - px)**2 + (cy - py)**2 <= radius**2:
                        key = (layer, gx, gy)
                        # If cell already has obstacle, mark as multi-net (blocked for all)
                        if key in obstacles:
                            if obstacles[key] != net_code:
                                obstacles[key] = -1  # universal block
                        else:
                            obstacles[key] = net_code

print("Obstacle map built.")

def a_star_route(start_coord, end_coord, net_code, preferred_layer=0):
    start_gx, start_gy = to_grid(*start_coord)
    end_gx, end_gy = to_grid(*end_coord)
    
    start_state = (preferred_layer, start_gx, start_gy)
    
    # Priority queue: (f_score, cost, layer, gx, gy)
    open_set = []
    heapq.heappush(open_set, (0, 0, preferred_layer, start_gx, start_gy))
    
    came_from = {}
    g_score = {start_state: 0}
    
    # 8-connected orthogonal + diagonal neighbors
    directions = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
    ]
    
    found_state = None
    
    while open_set:
        f, current_g, layer, gx, gy = heapq.heappop(open_set)
        current = (layer, gx, gy)
        
        if (gx, gy) == (end_gx, end_gy):
            found_state = current
            break
            
        if current_g > g_score.get(current, float('inf')):
            continue
            
        # 1. Neighbor transitions on same layer
        for dx, dy, move_cost in directions:
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < WIDTH_CELLS and 0 <= ny < HEIGHT_CELLS:
                neighbor = (layer, nx, ny)
                
                # Check obstacle collision
                obs_net = obstacles.get(neighbor)
                if obs_net is not None and obs_net != net_code:
                    continue  # Blocked by foreign net pad/track
                    
                tentative_g = current_g + move_cost
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = math.hypot(nx - end_gx, ny - end_gy)
                    heapq.heappush(open_set, (tentative_g + h, tentative_g, layer, nx, ny))
                    
        # 2. Layer change via transition (via cost: 5.0)
        other_layer = 1 - layer
        via_state = (other_layer, gx, gy)
        via_obs = obstacles.get(via_state)
        if via_obs is None or via_obs == net_code:
            tentative_g = current_g + 5.0
            if tentative_g < g_score.get(via_state, float('inf')):
                came_from[via_state] = current
                g_score[via_state] = tentative_g
                h = math.hypot(gx - end_gx, gy - end_gy)
                heapq.heappush(open_set, (tentative_g + h, tentative_g, other_layer, gx, gy))
                
    if not found_state:
        return None
        
    # Reconstruct path
    path = []
    curr = found_state
    while curr in came_from:
        path.append(curr)
        curr = came_from[curr]
    path.append(start_state)
    path.reverse()
    
    # Mark routed path into obstacle map
    for layer, gx, gy in path:
        obstacles[(layer, gx, gy)] = net_code
        
    return path

def simplify_and_apply(board, net_name, path, width_mm):
    net = board.FindNet(net_name)
    if not net or len(path) < 2:
        return
        
    current_layer, start_gx, start_gy = path[0]
    seg_points = [to_coord(start_gx, start_gy)]
    
    for i in range(1, len(path)):
        layer, gx, gy = path[i]
        coord = to_coord(gx, gy)
        
        if layer != current_layer:
            # Add track for previous layer
            if len(seg_points) >= 2:
                for j in range(len(seg_points) - 1):
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pcbnew.VECTOR2I(mm(seg_points[j][0]), mm(seg_points[j][1])))
                    t.SetEnd(pcbnew.VECTOR2I(mm(seg_points[j+1][0]), mm(seg_points[j+1][1])))
                    t.SetWidth(mm(width_mm))
                    t.SetLayer(pcbnew.F_Cu if current_layer == 0 else pcbnew.B_Cu)
                    t.SetNet(net)
                    board.Add(t)
            # Add via
            vx, vy = seg_points[-1]
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
            via.SetWidth(mm(0.8))
            via.SetDrill(mm(0.4))
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetNet(net)
            board.Add(via)
            
            # Start new segment on other layer
            current_layer = layer
            seg_points = [coord]
        else:
            seg_points.append(coord)
            
    # Flush remaining segments
    if len(seg_points) >= 2:
        for j in range(len(seg_points) - 1):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(seg_points[j][0]), mm(seg_points[j][1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(seg_points[j+1][0]), mm(seg_points[j+1][1])))
            t.SetWidth(mm(width_mm))
            t.SetLayer(pcbnew.F_Cu if current_layer == 0 else pcbnew.B_Cu)
            t.SetNet(net)
            board.Add(t)

# Route Critical Nets
critical_routes = [
    # 1. Power
    ("KL30", (195.0, 64.54), (186.0, 57.4), 1.2, 0),
    ("VRAW", (186.0, 54.6), (183.85, 64.0), 1.2, 0),
    ("VRAW", (183.85, 64.0), (172.75, 58.5), 1.2, 0),
    ("VRAW", (172.75, 58.5), (179.4, 68.0), 1.2, 0),
    ("VFILT", (172.75, 61.5), (161.05, 64.0), 1.2, 0),
    ("VFILT", (161.05, 64.0), (156.86, 64.0), 1.2, 0),
    ("SW_NODE", (159.14, 63.05), (146.0, 64.0), 1.2, 0),
    ("+5V", (152.0, 64.0), (139.05, 63.0), 1.4, 0),
    ("+5V", (139.05, 63.0), (115.41, 54.73), 1.4, 0),
    ("+5V", (115.41, 54.73), (112.87, 54.73), 1.4, 0),
    
    # 2. Video
    ("PI_VID", (122.62, 107.0), (135.86, 102.45), 0.25, 0),
    ("CAM_VID", (129.0, 106.0), (135.86, 100.55), 0.25, 0),
    ("TV_VID_OUT", (138.14, 102.45), (144.0, 106.0), 0.25, 0),
    
    # 3. Audio I2S (prefer B.Cu layer 1)
    ("GPIO18{slash}PCM.CLK", (125.57, 54.73), (144.86, 87.03), 0.25, 1),
    ("GPIO19{slash}PCM.FS", (156.05, 57.27), (144.86, 86.38), 0.25, 1),
    ("GPIO21{slash}PCM.DOUT", (161.13, 54.73), (144.86, 87.68), 0.25, 1),
    ("GPIO2{slash}SDA1", (115.41, 57.27), (139.14, 90.28), 0.25, 1),
    ("GPIO3{slash}SCL1", (117.95, 57.27), (139.14, 90.93), 0.25, 1),
    
    # 4. Telephony
    ("Net-(FB1-Pad1)", (169.53, 85.56), (181.0, 86.94), 0.4, 0),
    ("Net-(C30-Pad1)", (181.0, 89.06), (186.0, 88.95), 0.4, 0),
    ("Net-(C30-Pad2)", (186.0, 87.05), (196.0, 97.0), 0.4, 0),
    ("Net-(FB2-Pad1)", (169.53, 88.10), (181.0, 90.94), 0.4, 0),
    ("Net-(C31-Pad1)", (181.0, 93.06), (186.0, 92.95), 0.4, 0),
    ("Net-(C31-Pad2)", (186.0, 91.05), (196.0, 99.54), 0.4, 0),
    ("TEL_MUTE", (182.94, 98.0), (196.0, 109.7), 0.35, 0),
    
    # 5. I-Bus UART (prefer B.Cu)
    ("IBUS", (195.0, 67.08), (153.48, 72.56), 0.35, 1),
    ("GPIO14{slash}TXD0", (153.48, 77.64), (120.49, 54.73), 0.25, 1),
    ("GPIO15{slash}RXD0", (153.48, 80.18), (123.03, 54.73), 0.25, 1),
    ("TH3122_SEN_STA", (153.48, 81.45), (120.49, 57.27), 0.25, 1)
]

print(f"Routing {len(critical_routes)} critical nets via A*...")
routed_count = 0
for net_name, start_pt, end_pt, width_mm, pref_layer in critical_routes:
    net = board.FindNet(net_name)
    if not net:
        print(f"SKIP: {net_name} not found")
        continue
    path = a_star_route(start_pt, end_pt, net.GetNetCode(), preferred_layer=pref_layer)
    if path:
        simplify_and_apply(board, net_name, path, width_mm)
        routed_count += 1
        print(f"  [OK] {net_name} ({len(path)} steps)")
    else:
        print(f"  [FAIL] {net_name}: No collision-free path found!")

board.Save(BOARD_PATH)
print(f"Routed {routed_count}/{len(critical_routes)} nets collision-free.")
