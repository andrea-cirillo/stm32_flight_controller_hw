# Grid A* router (rev F copy: the rev E per-net keep-out boxes removed) for the last few open connections (F.Cu, B.Cu, In2 inside the VDD island; vias allowed).
# Obstacles = copper of other nets inflated by half width + clearance; refillable pours (B.Cu GND, In1 GND,
# In2 VDD island) are not obstacles because the zone filler will clear around the new copper.
import sys, math, heapq, re
import numpy as np
import pcbnew
from PIL import Image, ImageDraw
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union

BOARD = sys.argv[1]
OX, OY = 150.0, 100.0
RES = 0.05
X0, Y0, X1, Y1 = -26.0, -26.0, 26.0, 26.0        # routed window (board coords, mm)
NX, NY = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
import os
W, CLR = 0.15, float(os.environ.get("ASTAR_CLR", "0.16"))
VIA_D = 0.45
b = pcbnew.LoadBoard(BOARD)
def mm(v): return (pcbnew.ToMM(v.x) - OX, OY - pcbnew.ToMM(v.y))
def P(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY - y))
def to_px(x, y): return ((x - X0) / RES, (Y1 - y) / RES)
def to_mm(i, j): return (X0 + (i + 0.5) * RES, Y1 - (j + 0.5) * RES)

ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps); o = ps.Outline(0)
BOARDP = Polygon([mm(o.CPoint(j)) for j in range(o.PointCount())],
                 [[mm(ps.Hole(0, k).CPoint(j)) for j in range(ps.Hole(0, k).PointCount())] for k in range(ps.HoleCount(0))])
# rev C: In2 signals only inside the VDD pour, antenna keep-out from its rule area
def zpoly(z):
    o = z.Outline()
    return unary_union([Polygon([mm(o.Outline(i).CPoint(j)) for j in range(o.Outline(i).PointCount())]) for i in range(o.OutlineCount())])
ISLAND = unary_union([zpoly(z) for z in b.Zones() if not z.GetIsRuleArea() and z.GetZoneName() == 'VDD_In2'])
ANT = unary_union([zpoly(z) for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'ANTENNA_AE1'])
GROM = unary_union([zpoly(z) for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('GROMMET_CU')])
TPS = [(f.GetReference(), mm(f.GetPosition()), list(f.Pads())[0].GetNetname()) for f in b.GetFootprints() if f.GetReference().startswith('TP')]
# USB pair: >= 2 mm from the IMU courtyard and clear of the motor-stage pours on every layer
_u1 = [f for f in b.GetFootprints() if f.GetReference() == 'U1'][0]
_u1.BuildCourtyardCaches()
_c = _u1.GetCourtyard(pcbnew.F_CrtYd)
U1KO = Polygon([mm(_c.Outline(0).CPoint(j)) for j in range(_c.Outline(0).PointCount())]).buffer(2.0)
STAGES = unary_union([zpoly(z) for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.F_Cu)
                      and (re.match(r'M\d_N_pour', z.GetZoneName()) or '_st' in z.GetZoneName())]).buffer(0.5)

def raster(geoms, inflate):
    img = Image.new('1', (NX, NY), 0); d = ImageDraw.Draw(img)
    for g in geoms:
        g = g.buffer(inflate) if inflate else g
        for pg in (g.geoms if hasattr(g, 'geoms') else [g]):
            if pg.is_empty: continue
            d.polygon([to_px(*c) for c in pg.exterior.coords], fill=1)
            for h in pg.interiors:
                d.polygon([to_px(*c) for c in h.coords], fill=0)
    return np.array(img, dtype=bool).T          # [i, j]

def pad_poly(p, layer):
    s = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s, layer, 0, pcbnew.FromMM(0.005))
    return unary_union([Polygon([mm(s.Outline(i).CPoint(j)) for j in range(s.Outline(i).PointCount())]) for i in range(s.OutlineCount())])

LAY = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
def build(net):
    """per-layer blocked grids for a net (for a track centre) + via-blocked grid"""
    obst = {L: [] for L in LAY}
    mine = {L: [] for L in LAY}
    holes = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                ds = p.GetDrillSize()
                hc = Point(*mm(p.GetPosition()))
                holes.append(hc.buffer(pcbnew.ToMM(min(ds.x, ds.y)) / 2) if ds.x == ds.y else
                             LineString([mm(p.GetPosition()), mm(p.GetPosition())]).buffer(pcbnew.ToMM(max(ds.x, ds.y)) / 2))
            for L in LAY:
                if p.IsOnLayer(L):
                    if p.GetNetname() == net and p.GetNetname():
                        mine[L].append(pad_poly(p, L))
                    else:
                        obst[L].append((pad_poly(p, L), p.GetNetname()))
    for t in b.GetTracks():
        own = t.GetNetname() == net
        if t.GetClass() == 'PCB_VIA':
            c = Point(*mm(t.GetPosition()))
            if not own:                      # rev E: an own via is not a hole obstacle (it trapped A* starting from a via)
                holes.append(c.buffer(pcbnew.ToMM(t.GetDrill()) / 2))
            for L in LAY:
                g = c.buffer(pcbnew.ToMM(t.GetWidth()) / 2)
                mine[L].append(g) if own else obst[L].append((g, t.GetNetname()))
        elif t.GetLayer() in LAY:
            g = LineString([mm(t.GetStart()), mm(t.GetEnd())]).buffer(pcbnew.ToMM(t.GetWidth()) / 2)
            mine[t.GetLayer()].append(g) if own else obst[t.GetLayer()].append((g, t.GetNetname()))
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.F_Cu):
            continue
        if z.GetZoneName().startswith('GND_Bot'):
            continue
        fp_ = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(fp_.OutlineCount()):
            pg = Polygon([mm(fp_.Outline(i).CPoint(j)) for j in range(fp_.Outline(i).PointCount())])
            mine[pcbnew.F_Cu].append(pg) if z.GetNetname() == net else obst[pcbnew.F_Cu].append((pg, z.GetNetname()))
    for z in b.Zones():                      # rev E: the shunt pours are reserved (the DSN has them as keep-outs too)
        if not z.GetIsRuleArea() and z.GetZoneName() in ('VBAT_RAW_bot', 'VBAT_shunt_bot') and z.GetNetname() != net:
            obst[pcbnew.B_Cu].append((zpoly(z), z.GetNetname()))
    inner = BOARDP.buffer(-0.35)
    outside = box(X0, Y0, X1, Y1).difference(inner)
    blocked = {}
    def clr(n):
        base = float(__import__('os').environ.get('A_CLR', '0.11'))
        own = 0.16 if net.startswith('USB_D') else base
        oth = 0.21 if re.match(r'M\d_N', n or '') else (0.16 if (n or '').startswith('USB_D') else base)
        return max(own, oth)
    def infl(lst, extra):
        out = []
        for g, n in lst:
            out.append(g.buffer(extra + clr(n)))
        return out
    for L in LAY:
        g = raster(infl(obst[L], W / 2), 0)
        g |= raster(holes, W / 2 + 0.22)
        g |= raster([outside, ANT], W / 2)
        if L in (pcbnew.F_Cu, pcbnew.B_Cu):
            g |= raster([GROM], W / 2 + 0.06)
        if L == pcbnew.B_Cu:
            g |= raster([Point(c).buffer(1.5) for (_, c, n) in TPS if n != net], W / 2)
        if L == pcbnew.In2_Cu:
            g |= ~raster([ISLAND.buffer(-0.3)], 0)
        if net.startswith('USB_D'):
            g |= raster([U1KO, STAGES], W / 2)
        blocked[L] = g
    vb = np.zeros_like(blocked[LAY[0]])
    for L in LAY:
        vb |= raster(infl(obst[L], VIA_D / 2), 0)
    vb |= raster(holes, VIA_D / 2 + 0.3)
    vb |= raster([outside, ANT, GROM], VIA_D / 2)
    vb |= raster([Point(c).buffer(1.5) for (_, c, n) in TPS if n != net], VIA_D / 2)
    if net.startswith('USB_D'):
        vb |= raster([U1KO, STAGES], VIA_D / 2)
    goal_src = {L: raster(mine[L], 0) for L in LAY}
    return blocked, vb, goal_src, mine

def astar(start_cells, goal, blocked, vb):
    """start_cells: list of (L, i, j); goal: dict L -> bool grid. 8-connected, layer change = via."""
    INF = 1e18
    dist = {}
    pq = []
    for s in start_cells:
        dist[s] = 0.0; heapq.heappush(pq, (0.0, s))
    prev = {}
    gi = {L: np.argwhere(goal[L]) for L in LAY}
    tgt = np.concatenate([gi[L] for L in LAY if len(gi[L])]) if any(len(gi[L]) for L in LAY) else None
    cx, cy = tgt[:, 0].mean(), tgt[:, 1].mean()
    def h(i, j): return 0.0
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    n = 0
    while pq:
        d, (L, i, j) = heapq.heappop(pq)
        if d > dist.get((L, i, j), INF): continue
        n += 1
        if n > 12_000_000: break
        if goal[L][i, j] and (L, i, j) not in start_set:
            path = [(L, i, j)]
            while path[-1] in prev: path.append(prev[path[-1]])
            return path[::-1]
        for di, dj, c in moves:
            a, bb = i + di, j + dj
            if 0 <= a < NX and 0 <= bb < NY and not blocked[L][a, bb]:
                nd = d + c * (1.0 if L == pcbnew.F_Cu else 1.3)
                if nd < dist.get((L, a, bb), INF):
                    dist[(L, a, bb)] = nd; prev[(L, a, bb)] = (L, i, j); heapq.heappush(pq, (nd, (L, a, bb)))
        if not vb[i, j]:
            for L2 in LAY:
                if L2 != L and not blocked[L2][i, j]:
                    nd = d + 25
                    if nd < dist.get((L2, i, j), INF):
                        dist[(L2, i, j)] = nd; prev[(L2, i, j)] = (L, i, j); heapq.heappush(pq, (nd, (L2, i, j)))
    return None

def simplify(path):
    """merge collinear runs -> list of (layer, [pts]) + via positions"""
    segs, vias = [], []
    cur_L, pts = path[0][0], [path[0][1:]]
    for k in range(1, len(path)):
        L, i, j = path[k]
        if L != cur_L:
            vias.append((i, j)); segs.append((cur_L, pts)); cur_L, pts = L, [(i, j)]
            continue
        pts.append((i, j))
    segs.append((cur_L, pts))
    out = []
    for L, pts in segs:
        keep = [pts[0]]
        for k in range(1, len(pts) - 1):
            a, c, e = keep[-1], pts[k], pts[k + 1]
            d1 = (np.sign(c[0] - a[0]), np.sign(c[1] - a[1])); d2 = (np.sign(e[0] - c[0]), np.sign(e[1] - c[1]))
            if d1 != d2: keep.append(c)
        keep.append(pts[-1])
        out.append((L, keep))
    return out, vias

def groups_of(net):
    sys.argv_bak = sys.argv
    import importlib.util
    spec = importlib.util.spec_from_file_location('fx', '/home/claude/gen/fixup.py')
    return None

# --- connectivity groups (reuse the geometric grouping from fixup.py) ---
src = open('/home/claude/gen/fixup.py').read()
gsrc = src[src.index('CU = [pcbnew.F_Cu'):src.index('# 1. remove dangling track stubs')]
ns = dict(pcbnew=pcbnew, b=b, mm=mm, Point=Point, LineString=LineString, Polygon=Polygon, unary_union=unary_union,
          pad_shape=lambda p, L: pad_poly(p, L))
exec(gsrc, ns)
groups = ns['groups']

nets = sys.argv[2:] if len(sys.argv) > 2 else None
if not nets:
    nets = sorted(str(n) for n in b.GetNetsByName().keys() if str(n) and str(n) not in ('GND', 'VBAT') and not re.match(r'M\d_N', str(n)))
done = []
for net in nets:
    FINE = ('PWM_M4', 'VBAT_SNS', 'BARO_INT', 'UART_TX', 'LED_REAR', 'LED_FRONT')
    W = 0.2 if net.startswith('USB_D') else (0.1 if net in FINE else (0.2 if net in ('VSYS', 'VBUS', 'VBAT_F') else 0.15))
    for it in range(5):
        gs = groups(net)
        if len(gs) <= 1:
            break
        blocked, vb, _, _ = build(net)
        def cells(grp):
            g = {L: raster([x[1] for x in grp if L in x[0]], 0) for L in LAY}
            return g
        A, Bg = cells(gs[1]), cells(gs[0])           # route the smaller island to the main group
        start = [(L, int(i), int(j)) for L in LAY for i, j in np.argwhere(A[L]) if not blocked[L][i, j]]
        if not start:
            # free the cells under the start island itself
            for L in LAY:
                blocked[L] &= ~A[L]
            start = [(L, int(i), int(j)) for L in LAY for i, j in np.argwhere(A[L])]
        for L in LAY:
            blocked[L] &= ~Bg[L]
        start_set = set(start)
        path = astar(start, Bg, blocked, vb)
        if path is None:
            print('A* FAILED', net); break
        segs, vias = simplify(path)
        for L, pts in segs:
            for a, c in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b); t.SetStart(P(*to_mm(*a))); t.SetEnd(P(*to_mm(*c)))
                t.SetWidth(pcbnew.FromMM(W)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t)
        for (i, j) in vias:
            v = pcbnew.PCB_VIA(b); v.SetPosition(P(*to_mm(i, j))); v.SetWidth(pcbnew.FromMM(VIA_D))
            v.SetDrill(pcbnew.FromMM(0.2)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(b.FindNet(net)); b.Add(v)
        print('A* routed', net, 'segments', sum(len(p) - 1 for _, p in segs), 'vias', len(vias))
        done.append(net)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(BOARD, b)
