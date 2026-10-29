import pcbnew
import heapq
import math
import shutil
import time

BOARD_PATH = '/home/Youri621/E39Project/Ibus-RPI/pi4-HAT/pi4-HAT.kicad_pcb'
BACKUP_PATH = '/tmp/test_backup.kicad_pcb'

def mm(v):
    return pcbnew.FromMM(v)

print("1. Restoring clean board baseline...")
shutil.copy(BACKUP_PATH, BOARD_PATH)
board = pcbnew.LoadBoard(BOARD_PATH)

for z in list(board.Zones()):
    board.Remove(z)

print("2. Configuring 4-layer power & ground planes...")
def add_plane(net_name, layer_name, pts, priority=1):
    net = board.FindNet(net_name)
    if not net:
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

# 5 Copper Planes
add_plane('GND', 'In1.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=1)
add_plane('+5V', 'In2.Cu', [(100.5, 50.5), (175.0, 50.5), (175.0, 75.0), (199.5, 75.0), (199.5, 114.5), (100.5, 114.5)], priority=1)
add_plane('+12V_IN', 'In2.Cu', [(175.0, 50.5), (199.5, 50.5), (199.5, 75.0), (175.0, 75.0)], priority=1)
add_plane('GND', 'F.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=0)
add_plane('GND', 'B.Cu', [(100.5, 50.5), (199.5, 50.5), (199.5, 114.5), (100.5, 114.5)], priority=0)

X_MIN, X_MAX = 100.0, 200.0
Y_MIN, Y_MAX = 50.0, 115.0
GRID_RES = 0.25

W_CELLS = int(round((X_MAX - X_MIN) / GRID_RES)) + 1
H_CELLS = int(round((Y_MAX - Y_MIN) / GRID_RES)) + 1

def to_grid(x, y):
    gx = int(round((x - X_MIN) / GRID_RES))
    gy = int(round((y - Y_MIN) / GRID_RES))
    return max(0, min(W_CELLS - 1, gx)), max(0, min(H_CELLS - 1, gy))

def to_coord(gx, gy):
    return round(X_MIN + gx * GRID_RES, 2), round(Y_MIN + gy * GRID_RES, 2)

print(f"3. Building obstacle map on {GRID_RES}mm grid...")
pad_owner = {}

def dist_point_to_rect(px, py, rx, ry, hw, hh):
    dx = max(0.0, abs(px - rx) - hw)
    dy = max(0.0, abs(py - ry) - hh)
    return math.hypot(dx, dy)

for fp in board.GetFootprints():
    is_u4 = (fp.GetReference() == 'U4')
    for pad in fp.Pads():
        pos = pad.GetPosition()
        px = pos.x / 1e6
        py = pos.y / 1e6
        net_code = pad.GetNetCode()
        size = pad.GetSize()
        hw = size.x / 2e6
        hh = size.y / 2e6
        
        clr = 0.15 if is_u4 else 0.22
        gx0, gy0 = to_grid(px - hw - clr, py - hh - clr)
        gx1, gy1 = to_grid(px + hw + clr, py + hh + clr)
        
        is_tht = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        layers = [0, 1] if is_tht else [0]
        
        for l in layers:
            for gx in range(gx0, gx1 + 1):
                for gy in range(gy0, gy1 + 1):
                    cx, cy = to_coord(gx, gy)
                    if dist_point_to_rect(cx, cy, px, py, hw, hh) <= clr:
                        key = (l, gx, gy)
                        if key in pad_owner:
                            if pad_owner[key] != net_code:
                                pad_owner[key] = -1
                        else:
                            pad_owner[key] = net_code

print(f"Obstacle map initialized: {len(pad_owner)} cells.")

def a_star(start_coord, end_coord, net_code, is_smd_start=True, is_smd_end=True):
    start_gx, start_gy = to_grid(*start_coord)
    end_gx, end_gy = to_grid(*end_coord)
    
    start_l = 0 if is_smd_start else 1
    start_state = (start_l, start_gx, start_gy)
    
    open_set = []
    heapq.heappush(open_set, (0, 0, start_l, start_gx, start_gy))
    came_from = {}
    g_score = {start_state: 0}
    
    dirs = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
    ]
    
    found = None
    dist_total = math.hypot(start_coord[0] - end_coord[0], start_coord[1] - end_coord[1])
    
    while open_set:
        f, current_g, l, gx, gy = heapq.heappop(open_set)
        curr = (l, gx, gy)
        
        # Check destination reach
        if (gx, gy) == (end_gx, end_gy):
            if not is_smd_end or l == 0:
                found = curr
                break
            
        if current_g > g_score.get(curr, float('inf')):
            continue
            
        for dx, dy, cost in dirs:
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < W_CELLS and 0 <= ny < H_CELLS:
                if dx != 0 and dy != 0:
                    o1 = pad_owner.get((l, gx + dx, gy))
                    o2 = pad_owner.get((l, gx, gy + dy))
                    if (o1 is not None and o1 != net_code) or (o2 is not None and o2 != net_code):
                        continue
                        
                neighbor = (l, nx, ny)
                owner = pad_owner.get(neighbor)
                if owner is not None and owner != net_code:
                    continue
                    
                # Prefer B.Cu for long runs (> 12mm)
                layer_factor = 0.8 if (dist_total > 12.0 and l == 1) else 1.0
                tentative_g = current_g + cost * layer_factor
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = curr
                    g_score[neighbor] = tentative_g
                    h = math.hypot(nx - end_gx, ny - end_gy)
                    heapq.heappush(open_set, (tentative_g + h, tentative_g, l, nx, ny))
                    
        # Via transition (cost: 3.5)
        other_l = 1 - l
        via_ok = True
        for vl in [0, 1]:
            for vdx in [-1, 0, 1]:
                for vdy in [-1, 0, 1]:
                    vo = pad_owner.get((vl, gx + vdx, gy + vdy))
                    if vo is not None and vo != net_code:
                        via_ok = False
                        break
                if not via_ok:
                    break
        if via_ok:
            via_state = (other_l, gx, gy)
            tentative_g = current_g + 3.5
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
    for i in range(len(path)):
        l, gx, gy = path[i]
        is_via = (i > 0 and path[i-1][0] != l)
        if is_via:
            for vl in [0, 1]:
                for vdx in [-1, 0, 1]:
                    for vdy in [-1, 0, 1]:
                        vk = (vl, gx + vdx, gy + vdy)
                        pad_owner[vk] = net_code
        else:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    k = (l, gx + dx, gy + dy)
                    pad_owner[k] = net_code
                    
    return path

def simplify_points(pts):
    if len(pts) <= 2:
        return pts
    simplified = [pts[0]]
    for i in range(1, len(pts) - 1):
        dx1 = pts[i][0] - simplified[-1][0]
        dy1 = pts[i][1] - simplified[-1][1]
        dx2 = pts[i+1][0] - pts[i][0]
        dy2 = pts[i+1][1] - pts[i][1]
        if abs(dx1 * dy2 - dy1 * dx2) > 1e-5 or (dx1 * dx2 + dy1 * dy2) < 0:
            simplified.append(pts[i])
    simplified.append(pts[-1])
    return simplified

def apply_path_to_board(path, net, start_coord, end_coord, width_mm=0.25):
    if not path or len(path) < 2:
        return
    curr_l, start_gx, start_gy = path[0]
    seg_pts = [start_coord, to_coord(start_gx, start_gy)]
    
    for i in range(1, len(path)):
        l, gx, gy = path[i]
        coord = to_coord(gx, gy)
        if l != curr_l:
            clean_pts = simplify_points(seg_pts)
            for j in range(len(clean_pts) - 1):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(clean_pts[j][0]), mm(clean_pts[j][1])))
                t.SetEnd(pcbnew.VECTOR2I(mm(clean_pts[j+1][0]), mm(clean_pts[j+1][1])))
                t.SetWidth(mm(width_mm))
                t.SetLayer(pcbnew.F_Cu if curr_l == 0 else pcbnew.B_Cu)
                t.SetNet(net)
                board.Add(t)
            vx, vy = clean_pts[-1]
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
            
    seg_pts.append(end_coord)
    clean_pts = simplify_points(seg_pts)
    for j in range(len(clean_pts) - 1):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(clean_pts[j][0]), mm(clean_pts[j][1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(clean_pts[j+1][0]), mm(clean_pts[j+1][1])))
        t.SetWidth(mm(width_mm))
        t.SetLayer(pcbnew.F_Cu if curr_l == 0 else pcbnew.B_Cu)
        t.SetNet(net)
        board.Add(t)

print("4. Extracting active nets...")
plane_nets = {'GND', '+5V', '+12V_IN'}
pads_by_net = {}

for fp in board.GetFootprints():
    for pad in fp.Pads():
        netname = pad.GetNetname()
        if not netname or netname in plane_nets:
            continue
        if netname not in pads_by_net:
            pads_by_net[netname] = []
        is_smd = (pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD)
        pads_by_net[netname].append((fp.GetReference(), pad.GetNumber(), pad.GetPosition().x/1e6, pad.GetPosition().y/1e6, is_smd))

all_segments = []
for net_name, pads in pads_by_net.items():
    if len(pads) <= 1:
        continue
    remaining = pads[:]
    curr = remaining.pop(0)
    while remaining:
        nearest_idx = min(range(len(remaining)), key=lambda i: math.hypot(remaining[i][2]-curr[2], remaining[i][3]-curr[3]))
        nxt = remaining.pop(nearest_idx)
        dist = math.hypot(nxt[2]-curr[2], nxt[3]-curr[3])
        all_segments.append({
            'net_name': net_name,
            'p1': (curr[2], curr[3]),
            'p2': (nxt[2], nxt[3]),
            'smd1': curr[4],
            'smd2': nxt[4],
            'dist': dist,
            'ref1': curr[0],
            'ref2': nxt[0]
        })
        curr = nxt

all_segments.sort(key=lambda s: (0 if any(x in s['net_name'] for x in ['SDA', 'SCL', 'PCM']) else 1, s['dist']))
print(f"Total segments to route: {len(all_segments)}")

routed_count = 0
failed_count = 0
t0 = time.time()

for seg in all_segments:
    net_name = seg['net_name']
    net = board.FindNet(net_name) or board.FindNet(net_name.replace('/', '{slash}'))
    if not net:
        continue
    w = 0.35 if any(x in net_name for x in ['RAW', 'FILT', 'SW_', 'AUDIO', 'TEL_']) else 0.25
    path = a_star(seg['p1'], seg['p2'], net.GetNetCode(), is_smd_start=seg['smd1'], is_smd_end=seg['smd2'])
    if path:
        apply_path_to_board(path, net, seg['p1'], seg['p2'], width_mm=w)
        routed_count += 1
    else:
        failed_count += 1
        print(f"  [FAIL] {net_name} ({seg['ref1']} -> {seg['ref2']}, {seg['dist']:.1f}mm)")

t1 = time.time()
print(f"Routing complete in {t1-t0:.1f}s: {routed_count} routed, {failed_count} failed out of {len(all_segments)}.")

print("5. Refilling all zones...")
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD_PATH)
print("Board saved successfully.")
