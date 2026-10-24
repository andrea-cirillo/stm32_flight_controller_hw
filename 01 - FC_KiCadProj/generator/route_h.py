# DimaQuadFC rev F - planes, fixed RF / LDO / sensor details, MCU ground, pogo stubs, GND fan-out.
#   In1  GND solid (minus the antenna keep-out)
#   In2  VDD pour (minus the antenna keep-out), also carries signals
#   F.Cu RF chain pre-routed: RF1 -> MLPF-WB55 -> 0.36 mm line (50 ohm over In1) -> tuning R34 / C36 -> antenna
#   B.Cu pogo pads: 1 mm free of foreign copper, each tied by a short stub to a via
#   python3 route_h.py <board>
import sys, math, os
import pcbnew
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union

BOARD = sys.argv[1]
OX, OY = 150.0, 100.0
b = pcbnew.LoadBoard(BOARD)
def P(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(float(OX + x)), pcbnew.FromMM(float(OY - y)))
def B(v): return (pcbnew.ToMM(v.x) - OX, OY - pcbnew.ToMM(v.y))
def net(n): return b.FindNet(n)
def polyset(ps):
    return unary_union([Polygon([B(ps.Outline(i).CPoint(j)) for j in range(ps.Outline(i).PointCount())]) for i in range(ps.OutlineCount())])
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps)
BOARD_POLY = polyset(ps)
FPS = {f.GetReference(): f for f in b.GetFootprints()}
def pad(ref, num): return [p for p in FPS[ref].Pads() if p.GetNumber() == num][0]
def padxy(ref, num): return B(pad(ref, num).GetPosition())
def pad_poly(p, layer, grow=0.0):
    s = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s, layer, pcbnew.FromMM(grow), pcbnew.FromMM(0.005))
    return polyset(s)

for t in list(b.GetTracks()):
    b.Delete(t)
for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Delete(z)
ANT = polyset([z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'ANTENNA_AE1'][0].Outline())

def zone(netname, layer, poly, prio=0, name='', thermal=True, clearance=0.25):
    for pg in (list(poly.geoms) if poly.geom_type == 'MultiPolygon' else [poly]):
        if pg.area < 0.3:
            continue
        z = pcbnew.ZONE(b)
        z.SetLayer(layer); z.SetNet(net(netname)); z.SetAssignedPriority(prio); z.SetZoneName(name or netname)
        z.SetLocalClearance(pcbnew.FromMM(clearance)); z.SetMinThickness(pcbnew.FromMM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
        z.SetThermalReliefGap(pcbnew.FromMM(0.25)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.3))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for (x, y) in list(pg.simplify(0.01).exterior.coords)[:-1]:
            v = P(x, y); ol.Append(v.x, v.y)
        for hole in pg.interiors:
            ol.NewHole()
            for (x, y) in list(hole.coords)[:-1]:
                v = P(x, y); ol.Append(v.x, v.y, 0, ol.HoleCount(0) - 1)
        b.Add(z)

VIAS = []
def via(netname, x, y, d=0.45, drill=0.2):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(x, y)); v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(net(netname)); v.SetLocked(True)
    b.Add(v); VIAS.append((x, y))
ADDED = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
def track(netname, a, c, L, w=0.25):
    if a == c:
        return
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(L)
    t.SetNet(net(netname)); t.SetLocked(True); b.Add(t)
    ADDED[L].append((netname, LineString([a, c]).buffer(w / 2)))
def path(netname, pts, L, w=0.25):
    for a, c in zip(pts, pts[1:]):
        track(netname, a, c, L, w)

HOLES = [(10, 10), (-10, 10), (-10, -10), (10, -10)]
TPS = {f.GetReference(): B(f.GetPosition()) for f in b.GetFootprints() if f.GetReference().startswith('TP')}
NO_VIA = unary_union([ANT] + [Point(h).buffer(2.75 + 0.25) for h in HOLES])
INNER = BOARD_POLY.buffer(-0.45)
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH) and p.GetNetname() == '':
            INNER = INNER.difference(Point(*B(p.GetPosition())).buffer(pcbnew.ToMM(p.GetDrillSize().x) / 2 + 0.3))
PADS = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(L) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                PADS.append((fp.GetReference(), p.GetNumber(), p.GetNetname(), L, pad_poly(p, L), B(p.GetPosition())))
_FC = {}
def foreign(netname, L):
    k = (netname, L, len(ADDED[L]))
    if k not in _FC:
        _FC[k] = unary_union([pp for (_, _, n, l, pp, _) in PADS if l == L and n != netname] +
                             [g for (n, g) in ADDED[L] if n != netname])
    return _FC[k]
def tp_ok(q, netname, r=0.225):
    return all(math.dist(q, c) >= 0.5 + 1.0 + r for t, c in TPS.items() if pad(t, '1').GetNetname() != netname)
def via_ok(q, netname, spacing=0.7):
    if not INNER.contains(Point(q).buffer(0.225)) or Point(q).buffer(0.225).intersects(NO_VIA):
        return False
    if any(math.dist(q, v) < spacing for v in VIAS):
        return False
    vb = Point(q).buffer(0.225 + 0.2)
    if vb.intersects(foreign(netname, pcbnew.F_Cu)) or vb.intersects(foreign(netname, pcbnew.B_Cu)):
        return False
    return tp_ok(q, netname)

def stub_via(nn, c, L, rs=(0.55, 0.7, 0.85, 1.0, 1.2, 1.45), w=0.2, avoid=None):
    """short stub from pad centre c to the nearest legal via spot"""
    for r in rs:
        for k in range(36):
            a = 2 * math.pi * k / 36
            q = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
            if not via_ok(q, nn):
                continue
            if LineString([c, q]).buffer(w / 2 + 0.13).intersects(foreign(nn, L)):
                continue
            if avoid is not None and LineString([c, q]).buffer(w / 2 + 0.1).intersects(avoid):
                continue
            track(nn, c, q, L, w); via(nn, *q)
            return q
    why = {}
    for r in rs:
        for k in range(36):
            a = 2 * math.pi * k / 36
            q = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
            vb = Point(q).buffer(0.425)
            key = ('inner' if not INNER.contains(Point(q).buffer(0.225)) else 'novia' if Point(q).buffer(0.225).intersects(NO_VIA)
                   else 'spacing' if any(math.dist(q, v) < 0.7 for v in VIAS) else 'F' if vb.intersects(foreign(nn, pcbnew.F_Cu))
                   else 'B' if vb.intersects(foreign(nn, pcbnew.B_Cu)) else 'tp' if not tp_ok(q, nn) else 'line')
            why[key] = why.get(key, 0) + 1
    print('  no via spot for', nn, c, why)

# ------------------------------------------------------------------ planes
zone('GND', pcbnew.In1_Cu, BOARD_POLY.difference(ANT), 0, 'GND_In1')
zone('VDD', pcbnew.In2_Cu, BOARD_POLY.difference(ANT), 0, 'VDD_In2')

# ------------------------------------------------------------------ RF chain (F.Cu)
rf1, mi, mo = padxy('U2', '21'), padxy('U8', 'A3'), padxy('U8', 'A1')
track('RF_IN', rf1, mi, pcbnew.F_Cu, 0.25)
r1, r2, c1, c2 = padxy('R34', '1'), padxy('R34', '2'), padxy('C36', '1'), padxy('C36', '2')
ON, FN = pad('U8', 'A1').GetNetname(), pad('R34', '2').GetNetname()
# 50 ohm line: north out of the filter, north of the (-10, 10) grommet flange, west to the tuning resistor
yl = 13.3                                   # layout update: 0.6 mm lower, under the J6 pin row (front edge)
RF_PTS = [mo, (mo[0], 11.6), (mo[0] - (yl - 11.6), yl), (r1[0] + 1.2, yl), (r1[0], yl + 1.2 if yl + 1.2 < r1[1] else r1[1]), r1]
RF_PTS = [p_ for i, p_ in enumerate(RF_PTS) if i == 0 or p_ != RF_PTS[i - 1]]
path(ON, RF_PTS, pcbnew.F_Cu, 0.36)
track(FN, r2, c1, pcbnew.F_Cu, 0.36)
track(FN, r2, padxy('AE1', '1'), pcbnew.F_Cu, 0.36)
# filter ground: A2, B1, B2, B3 tied on F.Cu, two vias east of the B column
g = {n: padxy('U8', n) for n in ('A2', 'B1', 'B2', 'B3')}
path('GND', [g['B1'], g['B2'], g['B3']], pcbnew.F_Cu, 0.2)
track('GND', g['A2'], g['B2'], pcbnew.F_Cu, 0.2)
gv = (g['B1'][0] + 0.5, g['B1'][1] + 0.5)            # one ground via, north-east of the B column
track('GND', g['B1'], gv, pcbnew.F_Cu, 0.2); via('GND', *gv)
# VDD pin 20 (between RF1 and the filter's ground column): fixed stub north to a via (C23 on the bottom)
p20 = padxy('U2', '20')
v20 = (p20[0] + 0.15, p20[1] + 1.0)
track('VDD', p20, v20, pcbnew.F_Cu, 0.2); via('VDD', *v20)
cg = (c2[0] + 0.0, c2[1] + 0.75)
track('GND', c2, cg, pcbnew.F_Cu, 0.25); via('GND', *cg)
print('RF line', ' -> '.join('(%.2f, %.2f)' % p_ for p_ in RF_PTS), 'length %.1f mm' % sum(math.dist(a, c) for a, c in zip(RF_PTS, RF_PTS[1:])))

# ------------------------------------------------------------------ U2 exposed pad: 3 x 3 via array, VSSRF / VSSSMPS tied to the pad
ep = padxy('U2', '49')
for i in (-1, 0, 1):
    for j in (-1, 0, 1):
        via('GND', ep[0] + i * 1.0, ep[1] + j * 1.0)
for n in ('22', '32'):
    c = padxy('U2', n)
    d = (ep[0] - c[0], ep[1] - c[1])
    d = (math.copysign(1, d[0]), 0) if abs(d[0]) > abs(d[1]) else (0, math.copysign(1, d[1]))
    track('GND', c, (c[0] + d[0] * 0.75, c[1] + d[1] * 0.75), pcbnew.F_Cu, 0.2)

def unit(p, q):
    d = math.dist(p, q); return ((q[0] - p[0]) / d, (q[1] - p[1]) / d)
# ------------------------------------------------------------------ U12 input buck (VSON-10): GND pins 3 (ILIM), 5 (RT), 10 tied to the
# exposed pad on F.Cu, two vias in the pad to the In1 GND plane (single ground point at the IC, LM5166 layout notes)
epb = padxy('U12', '11')
for n in ('3', '5', '10'):           # straight in along the pin axis (pins 5 and 10 sit at the pad ends, pin 3 mid-row)
    c_ = padxy('U12', n); dd = math.dist(c_, epb)
    o_ = FPS['U12'].GetOrientationDegrees()
    ax_ = (math.cos(math.radians(o_)), math.sin(math.radians(o_)))      # footprint x axis in board (u, v)
    t_ = ((epb[0] - c_[0]) * ax_[0] + (epb[1] - c_[1]) * ax_[1])
    track('GND', c_, (c_[0] + ax_[0] * (t_ - math.copysign(0.55, t_)), c_[1] + ax_[1] * (t_ - math.copysign(0.55, t_))), pcbnew.F_Cu, 0.2)
eo = FPS['U12'].GetOrientationDegrees()
for d_ in (-0.6, 0.6):
    vx = (epb[0] + d_ * math.sin(math.radians(eo)), epb[1] + d_ * math.cos(math.radians(eo)))
    via('GND', *vx, d=0.5, drill=0.3)

# rev A (buck on the left edge): VIN pin 7 (north row) straight to the input cap C47, 0.3 mm (HV)
p7, c47 = padxy('U12', '7'), padxy('C47', '1')        # C47 rot 180: its VBAT pad faces pin 7
path('VBAT', [p7, (p7[0], p7[1] + 0.7), (c47[0], p7[1] + 0.7), c47], pcbnew.F_Cu, 0.3)

# ------------------------------------------------------------------ LDO U5 (DFN-6, 0.4 mm): VSYS pins tied, GND escape, router stubs
u5 = {p.GetNumber(): B(p.GetPosition()) for p in FPS['U5'].Pads()}
out = unit(u5['5'], u5['2'])                       # away from the package, pins 1-3 side
al = unit(u5['1'], u5['3'])                        # along the pin 1-3 column
track('VSYS', u5['3'], u5['4'], pcbnew.F_Cu, 0.2)
track('VSYS', u5['3'], (u5['3'][0] + 0.55 * out[0], u5['3'][1] + 0.55 * out[1]), pcbnew.F_Cu, 0.25)
g5 = (u5['2'][0] + 1.03 * out[0], u5['2'][1] + 1.03 * out[1])
track('GND', u5['2'], g5, pcbnew.F_Cu, 0.15)
stub_via('GND', g5, pcbnew.F_Cu, rs=(0.45, 0.6, 0.75, 0.9, 1.1, 1.3, 1.6, 1.9, 2.3), w=0.15)
track('VSYS', u5['1'], (u5['1'][0] + 0.55 * out[0] - 0.35 * al[0], u5['1'][1] + 0.55 * out[1] - 0.35 * al[1]), pcbnew.F_Cu, 0.2)
# ADJ (pin 5, middle of the inner column) and VDD (pin 6): stubs out of the 0.4 mm pitch for the router
track(pad('U5', '5').GetNetname(), u5['5'], (u5['5'][0] - 0.7 * out[0], u5['5'][1] - 0.7 * out[1]), pcbnew.F_Cu, 0.15)
track('VDD', u5['6'], (u5['6'][0] - 0.55 * out[0] - 0.35 * al[0], u5['6'][1] - 0.55 * out[1] - 0.35 * al[1]), pcbnew.F_Cu, 0.2)
# U11 (same package): GND pad 2 out west to a via, VSYS pins 4 and 6 tied
u11 = {p.GetNumber(): B(p.GetPosition()) for p in FPS['U11'].Pads()}
L11 = pcbnew.B_Cu if FPS['U11'].IsFlipped() else pcbnew.F_Cu
wx = -1 if u11['2'][0] < u11['5'][0] else 1
q11 = (u11['2'][0] + 0.45 * wx, u11['2'][1])
track('GND', u11['2'], q11, L11, 0.15)
stub_via('GND', q11, L11, rs=(0.5, 0.65, 0.8, 1.0), w=0.15)

# ------------------------------------------------------------------ rev A (MCU centred): IMU fan-out on F.Cu, straight from the MCU
# south row (pin 42 IMU_INT1, pin 44 SPI_MISO) to the IMU pins facing it (U1 rot 270)
for nn_ in ('IMU_INT1', 'SPI_MISO'):
    a_ = [B(p.GetPosition()) for p in FPS['U2'].Pads() if p.GetNetname() == nn_][0]
    c_ = [B(p.GetPosition()) for p in FPS['U1'].Pads() if p.GetNetname() == nn_][0]
    m_ = (a_[0], a_[1] - 0.8)
    path(nn_, [a_, m_, (c_[0], c_[1] + 1.2), c_] if abs(a_[0] - c_[0]) > 0.01 else [a_, c_], pcbnew.F_Cu, 0.15)
    print('IMU fan-out', nn_, a_, '->', c_)

# escape vias for the IMU pins enclosed by the INT1 / MISO fan-out (SHUB_SCL, SHUB_SDA) and for MCU pin 43 (SPI_SCK)
for nn_, ref_, dq in (('SHUB_SCL', 'U1', (-0.05, 0.9)), ('SHUB_SDA', 'U1', (0.05, 1.45)), ('SPI_SCK', 'U2', (0.0, -0.9))):
    a_ = [B(p.GetPosition()) for p in FPS[ref_].Pads() if p.GetNetname() == nn_][0]
    q_ = (a_[0] + dq[0], a_[1] + dq[1])
    track(nn_, a_, q_, pcbnew.F_Cu, 0.15); via(nn_, *q_)
    print('escape via', nn_, q_)

# LED supply to the front LEDs D3 / D4, kept away from the magnetometer U3 (the LED current changes with the colour):
# B.Cu from the supply diode D11 along the board interior, a via on the far side of each LED supply pin
d11 = padxy('D11', '1')
for led, cap, dv in (('D3', 'C42', (-0.95, -0.35)), ('D4', 'C45', (-0.35, -0.95))):
    p4 = padxy(led, '4'); cp = [B(p.GetPosition()) for p in FPS[cap].Pads() if p.GetNetname() == 'VLED'][0]
    vq = (p4[0] + dv[0], p4[1] + dv[1])
    track('VLED', p4, vq, pcbnew.F_Cu, 0.25); via('VLED', *vq)
    pts = [d11, (12.6, d11[1]), cp, (cp[0] + 1.2, cp[1]), vq] if led == 'D4' else [d11, (d11[0], d11[1] + 0.9), vq]
    path('VLED', pts, pcbnew.B_Cu, 0.25)
    if led == 'D3':
        track('VLED', vq, cp, pcbnew.B_Cu, 0.25)
    print('VLED to', led, 'pin 4', p4, 'via', vq, 'min distance to U3 %.1f mm' % min(LineString(pts).distance(Point(padxy('U3', '3'))), math.dist(p4, padxy('U3', '3'))))

# ------------------------------------------------------------------ compass: C1 cap under the IIS2MDC corner (F.Cu stub - via - B.Cu stub)
for (rt, nt, rb, nb_) in [('U3', '5', 'C18', '1')]:
    nn = pad(rt, nt).GetNetname(); ct, cb = padxy(rt, nt), padxy(rb, nb_)
    best = None
    for i in range(-50, 51):
        for j in range(-50, 51):
            q = ((ct[0] + cb[0]) / 2 + i * 0.03, (ct[1] + cb[1]) / 2 + j * 0.03)
            if not via_ok(q, nn, 0.7):
                continue
            if LineString([ct, q]).buffer(0.075 + 0.1).intersects(foreign(nn, pcbnew.F_Cu)): continue
            if LineString([cb, q]).buffer(0.075 + 0.1).intersects(foreign(nn, pcbnew.B_Cu)): continue
            d = math.dist(ct, q) + math.dist(cb, q)
            if best is None or d < best[0]: best = (d, q)
    if best:
        track(nn, ct, best[1], pcbnew.F_Cu, 0.15); track(nn, cb, best[1], pcbnew.B_Cu, 0.15); via(nn, *best[1])
    print('%s: %s' % (nn, 'via at (%.2f, %.2f)' % best[1] if best else 'NO SPOT'))
_m = ((padxy('U3', '6')[0] + padxy('U3', '8')[0]) / 2 - 0.23, (padxy('U3', '6')[1] + padxy('U3', '8')[1]) / 2)
track('GND', padxy('U3', '6'), _m, pcbnew.F_Cu, 0.15)
track('GND', _m, padxy('U3', '8'), pcbnew.F_Cu, 0.15)

# ------------------------------------------------------------------ pogo pads: B.Cu stub to a via, outward
tp_log = []
for t, c in sorted(TPS.items()):
    nn = pad(t, '1').GetNetname()
    best = None
    for r in [1.0 + 0.1 * k for k in range(31)]:
        for k in range(48):
            a = 2 * math.pi * k / 48
            q = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
            if not via_ok(q, nn, 0.75):
                continue
            seg = LineString([c, q])
            if any(seg.distance(Point(c2_)) < 0.5 + 1.0 + 0.075 for t2, c2_ in TPS.items()
                   if t2 != t and pad(t2, '1').GetNetname() != nn):
                continue
            if seg.buffer(0.075 + 0.15).intersects(foreign(nn, pcbnew.B_Cu)):
                continue
            best = q; break
        if best:
            break
    if best is None:
        tp_log.append(t + ' FAILED'); continue
    track(nn, c, best, pcbnew.B_Cu, 0.2)
    via(nn, *best)
    tp_log.append('%s %s' % (t, nn))
print('pogo stubs:', '; '.join(tp_log))

# ------------------------------------------------------------------ GND fan-out: every GND pad gets its own via to In1
SKIP = {('U2', n) for n in ('22', '32', '49')} | {('U8', n) for n in ('A2', 'B1', 'B2', 'B3')} | \
       {('C36', '2'), ('U5', '2'), ('U11', '2'), ('U3', '6')} | {('U12', n) for n in ('3', '5', '10', '11')}
fan = {'ok': 0, 'fail': []}
def fanout(ref, num, nn, L, c):
    for r in (0.55, 0.7, 0.85, 1.0, 1.2, 1.45, 1.75, 2.1, 2.5):
        for k in range(36):
            a = 2 * math.pi * k / 36
            q = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
            if not via_ok(q, nn):
                continue
            seg = LineString([c, q]).buffer(0.125 + 0.13)
            if seg.intersects(foreign(nn, L)) or LineString([c, q]).buffer(0.125).intersects(ANT):
                continue
            if L == pcbnew.B_Cu and not all(LineString([c, q]).distance(Point(c2_)) >= 1.575 for t2, c2_ in TPS.items() if pad(t2, '1').GetNetname() != nn):
                continue
            track(nn, c, q, L)
            via(nn, *q)
            fan['ok'] += 1
            return
    fan['fail'].append('%s.%s' % (ref, num))
for (ref, num, nn, L, poly, c) in sorted(PADS, key=lambda x: (x[2], x[0], x[1])):
    if nn != 'GND' or (ref, num) in SKIP or ref.startswith(('H', 'TP')):
        continue
    if pad(ref, num).GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
        continue
    fanout(ref, num, nn, L, c)
print('fan-out vias:', fan['ok'], 'failed:', fan['fail'])

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(BOARD, b)
