# DimaQuadGPS rev C: board from the netlist. 30 x 30 mm, r 2 corners, centred on (150, 100) like the FC (same
# 20 x 20 hole pattern as FC rev F), 2 layers, 1.0 mm. Rev D fixed: SAM-M10Q (top, 0 deg), J1 (Qwiic in, TOP, right edge),
# J2 (Qwiic out, TOP, rear edge), holes: nothing taller than ~1 mm on the bottom (stack check with FC rev H, 6 mm standoffs).
# The other parts start from a target spot and move to the nearest legal one (courtyards, hole keep-outs, outline).
import sys, re, json, math, uuid
import xml.etree.ElementTree as ET
import pcbnew
from shapely.geometry import Polygon, Point, box as sbox
from shapely.ops import unary_union
from shapely.affinity import rotate as srot

OUT, NETXML = sys.argv[1], sys.argv[2]
PROJECT = 'ACwing_GPS_A'
OX, OY = 150.0, 100.0
HALF, RC = 15.0, 2.0
HOLES = [(10, 10), (-10, 10), (-10, -10), (10, -10)]       # board frame (u right, v up), mm
HOLE_KEEP = 2.6                                     # M2 nylon standoff / nut
def P(u, v): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY - v))
def B(v): return (pcbnew.ToMM(v.x) - OX, OY - pcbnew.ToMM(v.y))
NS = uuid.UUID('6f1c2d1e-3b7a-4c55-9a0e-1d2c3b4a5f60')
def uid(*k): return str(uuid.uuid5(NS, '/'.join(map(str, k))))

board = pcbnew.BOARD()
board.SetCopperLayerCount(2)
ds = board.GetDesignSettings()
ds.SetBoardThickness(pcbnew.FromMM(1.0))
ds.SetAuxOrigin(P(-HALF, -HALF)); ds.SetGridOrigin(P(-HALF, -HALF))

# ---------------------------------------------------------------- outline: rounded square
def seg(a, b_):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(P(*a)); s.SetEnd(P(*b_)); s.SetWidth(pcbnew.FromMM(0.1)); board.Add(s)
def arc(c, a, mid, b_):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetArcGeometry(P(*a), P(*mid), P(*b_)); s.SetWidth(pcbnew.FromMM(0.1)); board.Add(s)
h, r = HALF, RC
k = r * (1 - math.sqrt(0.5))
seg((-h + r, h), (h - r, h)); seg((h, h - r), (h, -h + r)); seg((h - r, -h), (-h + r, -h)); seg((-h, -h + r), (-h, h - r))
arc(None, (h - r, h), (h - k, h - k), (h, h - r)); arc(None, (h, -h + r), (h - k, -h + k), (h - r, -h))
arc(None, (-h + r, -h), (-h + k, -h + k), (-h, -h + r)); arc(None, (-h, h - r), (-h + k, h - k), (-h + r, h))

# ---------------------------------------------------------------- nets and footprints
root = ET.parse(NETXML).getroot()
nets, pin_net = {}, {}
for n in root.find('nets').findall('net'):
    name = n.get('name').lstrip('/')
    if name.startswith('unconnected'):
        continue
    ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni
    for nd in n.findall('node'):
        pin_net[(nd.get('ref'), nd.get('pin'))] = ni
parts = json.load(open(OUT + '/%s.kicad_sch.parts.json' % PROJECT))
def fp_dir(lib):
    return OUT + '/ACwing_GPS.pretty' if lib == 'ACwing_GPS' else '/usr/share/kicad/footprints/%s.pretty' % lib
FPD = {}
for ref, info in sorted(parts.items()):
    lib, name = info['fp'].split(':')
    fp = pcbnew.FootprintLoad(fp_dir(lib), name)
    if fp is None and lib == 'ACwing_GPS':
        fp = None
    if fp is None:
        raise SystemExit('footprint not found ' + info['fp'])
    fp.SetReference(ref); fp.SetValue(info['value']); fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetPath(pcbnew.KIID_PATH('/' + uid('sym', ref, 1)))
    board.Add(fp); FPD[ref] = fp
    for pad in fp.Pads():
        ni = pin_net.get((ref, pad.GetNumber()))
        if ni is not None:
            pad.SetNet(ni)
    if info.get('dnp'):
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)

def put(ref, u, v, rot, bottom=False):
    fp = FPD[ref]
    if fp.IsFlipped():
        fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(rot); fp.SetPosition(P(u, v))
    if bottom:
        fp.Flip(fp.GetPosition(), False)

def cyard(fp):
    fp.BuildCourtyardCaches()
    c = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    return unary_union([Polygon([B(c.Outline(i).CPoint(j)) for j in range(c.Outline(i).PointCount())]) for i in range(c.OutlineCount())])

# fixed parts
for i, (u, v) in enumerate(HOLES):
    put('H%d' % (i + 1), u, v, 0)
put('U1', 0, 0, 0)          # rev D: axis-aligned, so the Qwiic connectors fit on the top side at the edge midpoints
# rev D: J1 on the TOP, mouth (fixing tabs) toward +u at the right edge, tabs 0.3 mm inside the outline
for rot in (90, 270):
    put('J1', 0, 0, rot, bottom=False)
    mp = [B(p.GetPosition()) for p in FPD['J1'].Pads() if p.GetNumber() == 'MP']
    sig = [B(p.GetPosition()) for p in FPD['J1'].Pads() if p.GetNumber() == '1']
    if mp[0][0] > sig[0][0] + 1:
        break
u_j = HALF - 0.35 - 0.9 - mp[0][0]
V_J1 = 3.6                                         # rev B: aligned with FC J3 (right edge, v = +3.6)
put('J1', u_j, V_J1, rot, bottom=False)
# rev D: J2 on the TOP, mouth toward -v at the rear edge (cable down to the flow board under the battery tray)
for rot2 in (0, 180):
    put('J2', 0, 0, rot2, bottom=False)
    mp2 = [B(p.GetPosition()) for p in FPD['J2'].Pads() if p.GetNumber() == 'MP']
    sig2 = [B(p.GetPosition()) for p in FPD['J2'].Pads() if p.GetNumber() == '1']
    if mp2[0][1] < sig2[0][1] - 1:
        break
v_j = -HALF + 0.35 + 0.9 - mp2[0][1]
put('J2', 0, v_j, rot2, bottom=False)
for f in ('U1', 'J1', 'J2', 'H1', 'H2', 'H3', 'H4'):
    FPD[f].SetLocked(True)
for p_ in FPD['U1'].Pads():                       # module ground pads: solid to the top pour (RF ground)
    if p_.GetNetname() == 'GND':
        p_.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
pin1 = [B(p.GetPosition()) for p in FPD['J1'].Pads() if p.GetNumber() == '1'][0]
print('J1 rot %d at u %.3f; pin 1 at (%.2f, %.2f); J2 rot %d at v %.3f' % (rot, u_j, pin1[0], pin1[1], rot2, v_j))
pad = {(ref, p.GetNumber()): B(p.GetPosition()) for ref in ('U1', 'J1') for p in FPD[ref].Pads() if p.GetNumber()}
s = 1                                  # rev B: backup supply / LED driver in the lower half, J2 at the rear edge

# movable parts: (ref, target u, v, rotation, bottom). Bottom-side layout:
#   right: J1 (Qwiic in) + bus bulk cap; rear edge: J2 (Qwiic out); centre: decoupling under the SAM VCC/V_IO pads;
#   centre: compass, right above the quietest spot of the FC (its IMU, away from the four motor stages) and
#   >= 6 mm from the LDO, the supercap and the cable; lower band: backup supply, LED driver, test pads.
T = [
    ('C1', 9.0, 4.6, 0, True),
    ('C3', pad[('U1', '17')][0], pad[('U1', '17')][1], 0, True), ('C4', pad[('U1', '2')][0], pad[('U1', '2')][1], 0, True),
    ('U3', 0.0, 0.0, 0, True), ('C6', -0.7, 2.1, 180, True), ('C7', 1.9, -0.5, 90, True),
    ('R3', -8.6, 1.6, 90, True), ('R4', -7.4, 1.6, 90, True),
    ('C5', -0.8, -5.4, 0, True), ('D1', -3.6, -5.8, 0, True), ('R1', -3.4, -4.4, 90, True),
    ('Q1', 5.8, -5.2, 0, True), ('R2', 5.8, -3.0, 90, True),
    ('TP1', -12.8, 5.0, 0, True), ('TP2', -12.8, 2.5, 0, True), ('TP3', -12.8, 0.0, 0, True),
    ('TP4', -12.8, -2.5, 0, True), ('TP5', -12.8, -5.0, 0, True),
    ('D2', 5.6, -12.6, 0, False),
]
ps = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(ps)
BP = Polygon([B(ps.Outline(0).CPoint(j)) for j in range(ps.Outline(0).PointCount())]).buffer(-0.25)
keep = unary_union([Point(hh).buffer(HOLE_KEEP + 0.05) for hh in HOLES])
placed = {'U1', 'J1', 'J2'}
for ref, tu, tv, trot, bot in T:
    fp = FPD[ref]
    occ = unary_union([cyard(FPD[r_]) for r_ in placed if FPD[r_].IsFlipped() == bot] or [Point(99, 99)])
    best = None
    for rr in [0.1 * k for k in range(60)]:
        nk = max(1, int(6.28 * rr / 0.1))
        for kk in range(nk):
            a = 2 * math.pi * kk / nk
            q = (tu + rr * math.cos(a), tv + rr * math.sin(a))
            for rot in (trot, (trot + 90) % 180):
                put(ref, q[0], q[1], rot, bottom=bot)
                g = cyard(fp)
                if BP.contains(g) and not g.intersects(occ) and not g.intersects(keep):
                    best = (q, rot); break
            if best: break
        if best: break
    if best is None:
        raise SystemExit('no spot for ' + ref)
    placed.add(ref)
    if math.hypot(best[0][0] - tu, best[0][1] - tv) > 0.05:
        print('  %s moved %.2f mm' % (ref, math.hypot(best[0][0] - tu, best[0][1] - tv)))

# ---------------------------------------------------------------- U3 escape (LGA-12, 0.5 mm pitch, bottom), locked
# Freerouting could not finish the compass on its own: the pins get short fixed stubs, the rest is autorouted.
def pp(ref, num): return [B(p.GetPosition()) for p in FPD[ref].Pads() if p.GetNumber() == num][0]
def track(net, pts, w=0.15, layer=pcbnew.B_Cu):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(layer); t.SetNet(nets[net]); t.SetLocked(True); board.Add(t)
def via(net, q):
    v_ = pcbnew.PCB_VIA(board); v_.SetPosition(P(*q)); v_.SetWidth(pcbnew.FromMM(0.5)); v_.SetDrill(pcbnew.FromMM(0.3))
    v_.SetViaType(pcbnew.VIATYPE_THROUGH); v_.SetNet(nets[net]); v_.SetLocked(True); board.Add(v_)
p = {n: pp('U3', n) for n in ('1', '3', '4', '5', '6', '8', '9', '10')}
xl = p['3'][0]; xr = p['9'][0]
side = -1 if xl < xr else 1                      # left column (pins 1-4) toward -u on this side
c6 = pp('C6', '1'); c7 = pp('C7', '1')
track('MAG_C1', [p['5'], (p['5'][0], c6[1]), c6] if abs(p['5'][0] - c6[0]) > 0.01 else [p['5'], c6])
track('+3V3', [p['9'], p['10']])
track('+3V3', [p['9'], (c7[0], p['9'][1]), c7] if abs(p['9'][1] - c7[1]) > 0.01 else [p['9'], c7])
gv = (p['6'][0] + 0.35, c6[1] - 0.45 * (1 if c6[1] > p['6'][1] else -1))
track('GND', [p['6'], (p['6'][0], gv[1]), gv]); via('GND', gv)
gv2 = (xr + 0.45 * (1 if xr > xl else -1), p['8'][1] + 1.0 * (1 if c6[1] > p['6'][1] else -1))
track('GND', [p['8'], (gv2[0], p['8'][1]), gv2]); via('GND', gv2)
xe = xl - 1.4 * (1 if xr > xl else -1)
for n, net in (('1', 'I2C_SCL'), ('4', 'I2C_SDA')):
    track(net, [p[n], (xe, p[n][1])])
# CS (pin 3, +3V3) sits between SCL and SDA on the far column from the other supply pins: it joins pin 10 with a
# short hop on the top layer (two vias), the only top track under the module body
sg = 1 if xr > xl else -1
va = (xl - 0.75 * sg, p['3'][1])
vb_y = p['10'][1] + 0.7 * (1 if p['10'][1] > p['9'][1] else -1)
vb = (xr + 0.2 * sg, vb_y)
track('+3V3', [p['3'], va]); via('+3V3', va)
track('+3V3', [p['10'], (p['10'][0], vb_y), vb]); via('+3V3', vb)
track('+3V3', [va, vb], w=0.2, layer=pcbnew.F_Cu)
c7g = pp('C7', '2'); dd = ((c7g[0] - c7[0]), (c7g[1] - c7[1])); ln_ = math.hypot(*dd)
gv3 = (c7g[0] + 0.8 * dd[0] / ln_, c7g[1] + 0.8 * dd[1] / ln_)
track('GND', [c7g, gv3]); via('GND', gv3)                 # C7 ground: own via (its pad is boxed in by the escape)
for jr in ('J1', 'J2'):                                    # Qwiic ground pin (1): own via past the end of the pin row
    j1_, j2_ = pp(jr, '1'), pp(jr, '2')
    dd_ = (j1_[0] - j2_[0], j1_[1] - j2_[1]); ln2 = math.hypot(*dd_)
    gv4 = (j1_[0] + 1.05 * dd_[0] / ln2, j1_[1] + 1.05 * dd_[1] / ln2)
    track('GND', [j1_, gv4], w=0.3); via('GND', gv4)
print('U3 escape: C6 pad1 %s, C7 pad1 %s, GND vias %s %s' % (c6, c7, gv, gv2))

# ---------------------------------------------------------------- GND fan-out (rev B): every small GND pad gets its own via,
# so no pad depends on a pour fragment that the autorouted tracks may cut off
from shapely.geometry import LineString as _LS
def _padpoly(p_, layer, grow):
    sp = pcbnew.SHAPE_POLY_SET(); p_.TransformShapeToPolygon(sp, layer, pcbnew.FromMM(grow), pcbnew.FromMM(0.005))
    return unary_union([Polygon([B(sp.Outline(i).CPoint(j)) for j in range(sp.Outline(i).PointCount())]) for i in range(sp.OutlineCount())])
vias_at = [B(t.GetPosition()) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
gnd_done = {pp_ for pp_ in (pp('J1', '1'), pp('J2', '1'), p['6'], p['8'], pp('C7', '2'))}
holes_k = unary_union([Point(hh).buffer(HOLE_KEEP + 0.3) for hh in HOLES])
segs_ = []
nfan, nfail = 0, []
for f in FPD.values():
    if f.GetReference() in ('U1', 'U3') or f.GetReference().startswith('H'):
        continue
    L = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
    allp = [q for g in FPD.values() for q in g.Pads() if q.IsOnLayer(pcbnew.F_Cu) or q.IsOnLayer(pcbnew.B_Cu)]   # copper pads, both layers (vias go through)
    for p_ in f.Pads():
        if p_.GetNetname() != 'GND' or B(p_.GetPosition()) in gnd_done:
            continue
        c = B(p_.GetPosition())
        foreign = unary_union([_padpoly(q, pcbnew.F_Cu if q.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu, 0.2) for q in allp if q.GetNetname() != 'GND'] + segs_)
        foreign_L = unary_union([_padpoly(q, L, 0.2) for q in allp if q.GetNetname() != 'GND' and q.IsOnLayer(L)] + segs_)
        done = False
        for rr in (0.6, 0.8, 1.0, 1.2, 1.5, 1.8, 2.2, 2.6, 3.0, 3.5):
            for kk in range(36):
                a = 2 * math.pi * kk / 36
                q = (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a))
                vg = Point(q).buffer(0.25 + 0.2)
                if not BP.buffer(-0.3).contains(vg) or vg.intersects(foreign) or vg.intersects(holes_k):
                    continue
                if any(math.dist(q, v) < 0.8 for v in vias_at):
                    continue
                ln = _LS([c, q]).buffer(0.15 + 0.2)
                if ln.intersects(foreign_L):
                    continue
                track('GND', [c, q], w=0.3, layer=L); via('GND', q); vias_at.append(q); segs_.append(ln); nfan += 1; done = True
                break
            if done: break
        if not done:
            nfail.append('%s.%s' % (f.GetReference(), p_.GetNumber()))
            if '--debug' in sys.argv:
                why = {}
                for rr in (0.6, 1.0, 1.5, 2.2, 3.0):
                    for kk in range(12):
                        a = 2 * math.pi * kk / 12; q = (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)); vg = Point(q).buffer(0.45)
                        r_ = 'edge' if not BP.buffer(-0.3).contains(vg) else 'foreign' if vg.intersects(foreign) else 'hole' if vg.intersects(holes_k) else 'via' if any(math.dist(q, v) < 0.8 for v in vias_at) else 'line' if _LS([c, q]).buffer(0.35).intersects(foreign_L) else 'ok'
                        why[r_] = why.get(r_, 0) + 1
                print('  fan-out', f.GetReference(), p_.GetNumber(), why)
print('GND fan-out vias', nfan, 'failed', nfail)

# ---------------------------------------------------------------- zones and rule areas
def zone_from(poly, layer, net=None, name='', rule=False, prio=0, vias_ok=False):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if rule:
        z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(not vias_ok)
        z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    else:
        z.SetNet(nets[net]); z.SetAssignedPriority(prio)
        z.SetLocalClearance(pcbnew.FromMM(0.2)); z.SetMinThickness(pcbnew.FromMM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(pcbnew.FromMM(0.25)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.3))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(name)
    ol = z.Outline(); ol.NewOutline()
    for (u, v) in list(poly.exterior.coords)[:-1]:
        p_ = P(u, v); ol.Append(p_.x, p_.y)
    board.Add(z)
    return z
full = sbox(-HALF, -HALF, HALF, HALF)
zone_from(full, pcbnew.F_Cu, 'GND', 'GND_Top')
zone_from(full, pcbnew.B_Cu, 'GND', 'GND_Bot')
for i, hh in enumerate(HOLES):
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        zone_from(Point(hh).buffer(HOLE_KEEP, 16), L, name='HOLE_KEEP_%d' % (i + 1), rule=True)
# no autorouted tracks on the top under the SAM-M10Q (keep-out up to the pad inner halves, so tracks leave the pads
# outward; solid module ground, stitched to the bottom pour by
# vias): Freerouting wire keep-out only (route_gps.py), so that the locked CS hop above passes the KiCad DRC
json.dump({'SAM_BODY': list(srot(sbox(-6.0, -6.0, 6.0, 6.0), 0, origin=(0, 0)).exterior.coords)}, open(OUT + '/route_keepouts.json', 'w'))

pcbnew.SaveBoard(OUT + '/%s.kicad_pcb' % PROJECT, board)

# ---------------------------------------------------------------- project rules (written after SaveBoard, which
# would otherwise store the defaults of the fresh board). Based on the FC project file.
pro = json.load(open('/home/claude/outD/DimaQuadFC_D.kicad_pro'))
ns = pro['net_settings']
base = [c for c in ns['classes'] if c['name'] == 'Default'][0]
d = dict(base); d.update(clearance=0.15, track_width=0.2, via_diameter=0.5, via_drill=0.3)
pw = dict(d); pw.update(name='Power', track_width=0.4)
fi = dict(d); fi.update(name='Fine', track_width=0.15, clearance=0.15)   # rev B: long I2C runs, keep the via hole clearance
ns['classes'] = [d, pw, fi]
ns['netclass_patterns'] = [{'netclass': 'Power', 'pattern': n} for n in ('+3V3', 'GND')] + \
                          [{'netclass': 'Fine', 'pattern': n} for n in ('I2C_SCL', 'I2C_SDA', 'MAG_C1')]
ns['netclass_assignments'] = None
rr = pro['board']['design_settings']['rules']
rr.update(min_clearance=0.1, min_track_width=0.15, min_via_diameter=0.45, min_via_annular_width=0.1,
          min_through_hole_diameter=0.3, min_hole_clearance=0.25, min_copper_edge_clearance=0.3, min_resolved_spokes=1)
pro['meta']['filename'] = PROJECT + '.kicad_pro'
json.dump(pro, open(OUT + '/%s.kicad_pro' % PROJECT, 'w'), indent=2)
print('footprints', len(FPD), 'nets', len(nets))
