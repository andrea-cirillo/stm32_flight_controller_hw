# ACwing FC rev A (from rev F/G): board from the netlist.
#   Outline: frame C, copied from rev E (40 x 40 mm, chamfered rear-right corner for the USB-C receptacle).
#   Holes: 4 x 3.2 mm plated grommet holes on the 20 x 20 pattern; flange keep-out r 2.75 (no tracks / vias on the
#          outer layers), component keep-out r 3.0 top / 3.6 bottom.
#   MCU at the board centre on the top side (rot 180: motor and ADC pins face east, RF pin north-west toward the chip
#   antenna kept at the left edge as rev E), IMU south of it near the centre, compass at the front corner, four
#   WS2812B mirrored about the front-rear diagonal, ESC link J2 on the top at the rear edge (8 mm west of
#   DimaQuadESC J1). Fixed parts first, the others go to the nearest legal spot from a target.
#   python3 gen_pcb_h.py <out dir> <netlist xml>
import sys, json, math, re, uuid, os
import xml.etree.ElementTree as ET
import pcbnew
from shapely.geometry import Polygon, Point, box as sbox
from shapely.ops import unary_union
sys.path.insert(0, '/home/claude/genFCB')
from kisch import uid

OUT, NETXML = sys.argv[1], sys.argv[2]
PROJECT = 'ACwing_FC_A'
OX, OY = 150.0, 100.0
HOLES = [(10, 10), (-10, 10), (-10, -10), (10, -10)]
KEEP_TOP, KEEP_BOT = 3.0, 3.6
def P(u, v): return pcbnew.VECTOR2I(pcbnew.FromMM(float(OX + u)), pcbnew.FromMM(float(OY - v)))
def B(v): return (pcbnew.ToMM(v.x) - OX, OY - pcbnew.ToMM(v.y))

board = pcbnew.BOARD()
board.SetCopperLayerCount(4)
ds = board.GetDesignSettings()
ds.SetBoardThickness(pcbnew.FromMM(1.0))
ds.SetAuxOrigin(P(-20, -20)); ds.SetGridOrigin(P(-20, -20))
# ---------------------------------------------------------------- outline: frame C (rev E) with the USB corner 0.8 mm out
# With the 20 x 20 holes, the grommet at (10, -10) reaches the USB-C pads (rev E position): the receptacle moves
# 0.85 mm outward along the diagonal, the chamfer with it, and the right / rear edges step out by 0.8 mm next to the
# chamfer so the front shell legs keep their edge clearance. Everywhere else the outline is the rev E one.
def seg(a, c):
    s_ = pcbnew.PCB_SHAPE(board); s_.SetShape(pcbnew.SHAPE_T_SEGMENT); s_.SetLayer(pcbnew.Edge_Cuts)
    s_.SetStart(P(*a)); s_.SetEnd(P(*c)); s_.SetWidth(pcbnew.FromMM(0.1)); board.Add(s_)
def arc(a, m, c):
    s_ = pcbnew.PCB_SHAPE(board); s_.SetShape(pcbnew.SHAPE_T_ARC); s_.SetLayer(pcbnew.Edge_Cuts)
    s_.SetArcGeometry(P(*a), P(*m), P(*c)); s_.SetWidth(pcbnew.FromMM(0.1)); board.Add(s_)
k3 = 3 * (1 - math.sqrt(0.5))
BUMP, CH = 0.8, 36.2                                  # step out; chamfer line u - v = CH (rev E: 35)
OUTLINE_PTS = [(-16.6, 20), (17, 20)]
seg((-16.6, 20), (17, 20)); arc((17, 20), (20 - k3, 20 - k3), (20, 17))
seg((20, 17), (20, -11.5)); seg((20, -11.5), (20 + BUMP, -11.5 - BUMP))
seg((20 + BUMP, -11.5 - BUMP), (20 + BUMP, 20 + BUMP - CH)); seg((20 + BUMP, 20 + BUMP - CH), (CH - 20 - BUMP, -20 - BUMP))
seg((CH - 20 - BUMP, -20 - BUMP), (11.5 + BUMP, -20 - BUMP)); seg((11.5 + BUMP, -20 - BUMP), (11.5, -20))
seg((11.5, -20), (-17, -20)); arc((-17, -20), (-20 + k3, -20 + k3), (-20, -17))
# rev H: front-left corner chamfered (v - u = 36.6) like the DimaQuadESC rev B charge-port corner below it, so a USB-C
# plug in the power board never runs under the FC (stack check 2026-10-18); the chip antenna stays inside the outline
seg((-20, -17), (-20, 16.6)); seg((-20, 16.6), (-16.6, 20))

ALLCU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
def rule_area(name, poly, layers, tracks=True, vias=True, pour=True):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True); z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowCopperPour(pour)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for L in layers:
        ls.AddLayer(L)
    z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for (x, y) in list(poly.exterior.coords)[:-1]:
        v = P(x, y); o.Append(v.x, v.y)
    board.Add(z)
ANT = sbox(-20.5, 9.0, -17.5, 20.5)             # chip antenna keep-out, as rev E
rule_area('ANTENNA_AE1', ANT, ALLCU, tracks=False)
for i, h in enumerate(HOLES):
    rule_area('GROMMET_CU_%d' % (i + 1), Point(h).buffer(2.75, 10), [pcbnew.F_Cu, pcbnew.B_Cu], pour=False)

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
FPD = {}
for ref, info in sorted(parts.items()):
    lib, name = info['fp'].split(':')
    fp = pcbnew.FootprintLoad(OUT + '/ACwing.pretty', name)
    if fp is None:
        raise SystemExit('footprint not found ' + info['fp'])
    fp.SetReference(ref); fp.SetValue(info['value']); fp.SetFPID(pcbnew.LIB_ID('ACwing', name))
    fp.SetPath(pcbnew.KIID_PATH('/' + uid('sym', ref, 1)))
    board.Add(fp); FPD[ref] = fp
    for pad in fp.Pads():
        ni = pin_net.get((ref, pad.GetNumber()))
        if ni is not None:
            pad.SetNet(ni)
    fp.SetAttributes(fp.GetAttributes() & ~(pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM))   # library copies carry no DNP flags
    if info.get('dnp'):
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
    if ref.startswith('TP'):
        for pad in fp.Pads():          # pogo pads: 1 mm free of foreign copper all around
            pad.SetLocalClearance(pcbnew.FromMM(1.0))

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
def pp(ref, num): return [B(p.GetPosition()) for p in FPD[ref].Pads() if p.GetNumber() == num][0]

# ---------------------------------------------------------------- fixed parts
FIXED = {   # ref: (u, v, rot, bottom)
    'H1': (10, 10, 0, False), 'H2': (-10, 10, 0, False), 'H3': (-10, -10, 0, False), 'H4': (10, -10, 0, False),
    'U2': (0.0, 0.0, 180, False),                   # layout update 2026-10-24: MCU exactly at the board centre
    'U1': (0.0, -7.6, 270, False),                  # IMU: south of the MCU, rot 270: INT1 / MISO face MCU pins 42 / 44
    'U3': (17.4, 17.4, 45, False), 'U4': (16.64, 14.2, 0, False),   # compass (front corner) and baro, as rev E
    'AE1': (-18.6, 14.5, -90, False), 'R34': (-16.95, 15.53, 90, False), 'C36': (-16.95, 17.45, 90, False),
    'J1': (15.767, -15.767, 45, False),             # USB-C at the chamfer, 0.85 mm further out than rev E
    'J3': (16.9, 3.6, 90, False),                   # Qwiic, right edge (front-right): GPS board above
    'J4': (16.9, -4.3, 90, False),                  # rev H: second Qwiic, right edge (rear-right): flow board
    'J7': (-18.4, 7.2, 0, False), 'J8': (-18.4, 4.1, 0, False),   # rev H: battery / power input pads, left edge
    'J5': (2.0, 16.85, 180, False),                 # ELRS, top edge (front-left)
    'J6': (-8.2, 16.85, 180, False),                # layout update: ESC link B on the front edge, next to J5 (same mouth direction)
    # RGB LEDs, mirrored about the front-rear diagonal u = v (and point-symmetric front / rear); rev A: D3 / D4 turned
    # 180 deg so their supply pins (VLED) face away from the magnetometer corner
    'D1': (-11.0, -18.4, 180, False), 'D2': (-18.4, -11.0, 270, False), 'D3': (11.0, 18.4, 180, False), 'D4': (18.4, 11.0, 270, False),
}
for ref, (u, v, r, bot) in FIXED.items():
    put(ref, u, v, r, bot)
# ESC link J2: TOP side, rear edge, mouth (fixing tabs, footprint +Y) toward -v. Not on the bottom: there it would sit
# right above DimaQuadESC J1 (both 2.9 mm tall, more than the 5 mm stack gap). Left of the USB-C corner, 8 mm west
# of DimaQuadESC J1: the 1:1 cable (loose wires) makes an S from the ESC top up to the FC top
put('J2', 0, 0, 0)
assert pp('J2', 'MP')[1] < pp('J2', '1')[1] - 1
U_J2 = 1.5
put('J2', U_J2, -20.0 + 0.35 + 0.9 - pp('J2', 'MP')[1], 0)
# pogo pads: 2 x 4 grid at 2.54 mm on the bottom, rear centre (same position and fixture as rev E): close to the SWD
# pins on the south side of the MCU
POGO = {'TP4': (-3.81, -14.27), 'TP5': (-1.27, -14.27), 'TP1': (1.27, -14.27), 'TP2': (3.81, -14.27),
        'TP6': (-3.81, -11.73), 'TP7': (-1.27, -11.73), 'TP8': (1.27, -11.73), 'TP3': (3.81, -11.73)}
for ref, (u, v) in POGO.items():
    put(ref, u, v, 0, bottom=True)
for ref in list(FIXED) + ['J2'] + list(POGO):
    FPD[ref].SetLocked(True)
print('J2 pins: 1 at (%.2f, %.2f), 8 at (%.2f, %.2f)' % (pp('J2', '1') + pp('J2', '8')))
print('J6 pins: 1 at (%.2f, %.2f), 8 at (%.2f, %.2f)' % (pp('J6', '1') + pp('J6', '8')))
# MLPF-WB55 (rot 0: A column west, A1 north): A3 (RF in) 2.05 mm straight north of RF1 (pin 21), A1 toward the antenna;
# the gap leaves room for the VDD pin 20 via and the CRSF_TX (pin 18) exit under the filter's ground column
p21 = pp('U2', '21')
put('U8', p21[0] + 0.25, p21[1] + 2.05 + 0.587, 0); FPD['U8'].SetLocked(True)
assert abs(pp('U8', 'A3')[0] - p21[0]) < 0.01 and pp('U8', 'A1')[1] > pp('U8', 'A3')[1]
pin = {n: pp('U2', n) for n in ('4', '7', '9', '13', '14', '20', '21', '23', '24', '25', '28', '29', '31', '33', '34', '37', '40', '43', '46', '48', '1', '8')}

# ---------------------------------------------------------------- movable parts: (ref, u, v, rot, bottom)
T = [
    # RF chain: matched filter right at RF1, crystal at the HSE pins (north-west corner of the MCU)
    ('Y1', -5.6, 2.4, 90, False),
    # MCU decoupling and support (bottom, under the MCU edges, next to their pins)
    ('C23', 0.7, 5.6, 0, True), ('C26', pin['23'][0] - 0.2, 5.4, 0, True), ('C27', pin['23'][0] - 1.4, 4.4, 90, True),
    ('C24', -4.6, -2.0, 0, True), ('C25', 4.6, -2.6, 0, True), ('C14', 4.6, 0.4, 0, True), ('C22', 5.6, 0.9, 90, True),
    ('C28', pin['40'][0], -4.6, 90, True), ('C9', 0.0, -5.4, 0, True), ('C15', 4.6, -0.6, 0, True), ('R14', 4.6, -1.6, 0, True),
    ('L1', -5.8, -1.2, 90, True), ('L2', -4.8, 0.6, 0, True), ('C29', -5.0, 1.8, 0, True),
    # ESC link support (bottom): series resistors between the MCU east pins and J2, ADC cap
    ('R20', 6.4, 2.6, 0, True), ('R21', 6.4, 1.6, 0, True), ('R22', 6.4, 3.6, 0, True), ('R23', 6.4, 4.6, 0, True),
    ('R24', -5.6, 1.2, 0, True), ('C1', 4.8, 4.8, 90, True),
    # rev H: ESC link B series resistors (bottom) between the MCU north / west pins (PA6, PA8-PA10) and J6
    ('R25', -5.4, 8.0, 0, True), ('R26', -5.4, 9.0, 0, True), ('R28', -3.8, 9.2, 90, True), ('R27', -7.0, 8.4, 0, True),
    # IMU / flash / sensor buses (bottom)
    ('C16', -0.6, -8.4, 0, True), ('C17', 0.6, -6.7, 0, True), ('R38', -2.4, -7.8, 90, True),
    ('R17', 2.0, -6.0, 90, True), ('R18', 3.0, -6.0, 90, True),
    ('U10', 5.6, -5.4, 0, True), ('C39', 2.0, -6.6, 90, True), ('R37', 2.0, -5.0, 90, True),
    ('R15', 8.6, -0.4, 0, True), ('R16', 8.6, 0.6, 0, True),
    # compass corner (bottom), as rev E
    ('C18', 17.76, 16.68, 0, True), ('C19', 16.28, 16.68, 90, True), ('C20', 13.0, 15.5, 0, True), ('C21', 15.88, 14.45, 0, True),
    # expansion LDO next to J3 (bottom)
    ('U11', 15.6, 4.6, 0, True), ('R40', 14.0, 6.6, 90, True), ('R41', 13.0, 6.6, 90, True), ('C43', 15.6, 2.4, 0, True), ('C44', 17.2, 6.4, 90, True),
    # RGB LEDs: supply diode, series resistor at D1, one cap under each LED (bottom)
    ('D11', 6.0, 13.0, 90, True), ('R39', -1.2, -6.4, 90, True),
    ('C40', -11.0, -16.4, 0, True), ('C41', -16.4, -11.0, 90, True), ('C42', 11.0, 16.4, 0, True), ('C45', 16.4, 11.0, 90, True),
    # USB, ESD, CC (rear-right)
    ('U7', 6.0, -12.8, 0, False), ('R12', 10.6, -14.6, 0, True), ('R13', 14.6, -10.6, 90, True),
    # rev H: input buck (top, rear-left corner, 21 mm from the board centre: the inductor field stays away from both
    # compasses and from the GPS board connectors above): L3 west, U12 rot 90 (SW / VIN row facing south)
    # layout update: input buck on the LEFT edge (old ESC link B spot), no longer in the corner between the rear LEDs D1 / D2;
    # 24 mm from the board centre, ~40 mm from the compass corner
    ('L3', -16.9, -4.6, 0, False), ('U12', -12.4, -5.0, 90, False), ('C47', -12.4, -1.9, 180, False), ('C49', -10.6, -2.8, 90, False),
    ('C6', -16.4, -8.4, 0, False), ('C46', -13.6, -7.6, 0, False),
    ('R47', -10.4, -6.0, 90, False), ('R48', -9.4, -6.0, 90, False),
    ('C2', -1.6, -12.4, 0, False),                 # VBAT bulk at J2, top (1206 is too tall for the bottom)
    # power path (top, east of the IMU, freed by the rev G buck / charge gate) and LDO (top, south of the IMU)
    ('Q5', 6.6, -4.4, 0, False), ('D9', 5.6, -7.2, 0, False), ('C7', 9.2, -2.0, 90, False), ('R2', 9.0, -5.6, 90, False),
    ('U5', -4.6, -7.8, 90, False), ('R3', -6.4, -8.6, 90, False), ('R4', -6.4, -9.6, 90, False), ('C8', -4.6, -5.8, 0, False),
    ('R42', 0.6, -17.2, 0, True),
    # sensing dividers (bottom)
    ('R8', 6.8, 6.6, 0, True), ('R9', 6.8, 7.6, 0, True), ('C12', 5.2, 7.2, 90, True),
    ('R10', -5.6, -5.2, 0, True), ('R11', -5.6, -6.2, 0, True),
]
ps = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(ps)
BP = Polygon([B(ps.Outline(0).CPoint(j)) for j in range(ps.Outline(0).PointCount())]).buffer(-0.3)
POGO_KEEP = unary_union([Point(pp(t, '1')).buffer(0.5 + 1.0) for t in POGO])
IMU_VIAS = sbox(-1.0, -6.0, 1.0, -3.9)          # rev A: bottom kept free for the IMU / SPI escape vias (route_h.py)
placed = set(FIXED) | {'J2', 'U8'} | set(POGO)
moved = []
for ref, tu, tv, trot, bot in T:
    fp = FPD[ref]
    occ = unary_union([cyard(FPD[r_]) for r_ in placed if FPD[r_].IsFlipped() == bot and not r_.startswith(('H', 'TP'))] or [Point(99, 99)])
    keep = unary_union([Point(h).buffer(KEEP_BOT if bot else KEEP_TOP) for h in HOLES] + [ANT] + ([POGO_KEEP, IMU_VIAS] if bot else []))
    best = None
    for rr in [0.1 * k for k in range(80)]:
        nk = max(1, int(6.28 * rr / 0.1))
        for kk in range(nk):
            a = 2 * math.pi * kk / nk
            q = (tu + rr * math.cos(a), tv + rr * math.sin(a))
            for rot in (trot, (trot + 90) % 360):
                put(ref, q[0], q[1], rot, bottom=bot)
                g = cyard(fp)
                if BP.contains(g) and not g.intersects(occ) and not g.intersects(keep):
                    best = (q, rot); break
            if best: break
        if best: break
    if best is None:
        raise SystemExit('no spot for ' + ref)
    placed.add(ref)
    d = math.hypot(best[0][0] - tu, best[0][1] - tv)
    if d > 0.3:
        moved.append('%s %.1f' % (ref, d))
print('moved > 0.3 mm:', ', '.join(moved))
missing = [r for r in FPD if r not in placed]
print('not placed:', missing)

pcbnew.SaveBoard(OUT + '/%s.kicad_pcb' % PROJECT, board)

# ---------------------------------------------------------------- project rules (after SaveBoard)
import shutil
shutil.copy('/tmp/claude-0/FC_A_good.kicad_pro', OUT + '/%s.kicad_pro' % PROJECT)   # SaveBoard wrote the defaults of the fresh board
print('footprints', len(FPD), 'nets', len(nets))
