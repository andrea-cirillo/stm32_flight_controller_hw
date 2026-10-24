# EMI check for the FC sensors: magnetometer U3 (IIS2MDC) and IMU U1 (LSM6DSV16X).
#   1. Static magnetic field at the magnetometer from on-board currents: Biot-Savart on every routed track segment of the
#      current-carrying nets (worst-case currents below, contributions added in magnitude: no cancellation by the return
#      path, so this is an upper bound), plus the stray field of the inductors (dipole estimate).
#   2. Distances from both sensors to the switching nodes / inductors / fast edges, on every copper layer.
#   3. In1 ground plane under both sensors (solid reference, no slots).
#   python3 emi_check.py <board.kicad_pcb> [label]
import sys, math
import pcbnew
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

b = pcbnew.LoadBoard(sys.argv[1]); LABEL = sys.argv[2] if len(sys.argv) > 2 else ''
OX, OY = 150.0, 100.0
def B(v): return (pcbnew.ToMM(v.x) - OX, OY - pcbnew.ToMM(v.y))
F = {f.GetReference(): f for f in b.GetFootprints()}
Z = {pcbnew.F_Cu: 0.0, pcbnew.In1_Cu: -0.2, pcbnew.In2_Cu: -0.8, pcbnew.B_Cu: -1.0}   # 1.0 mm board, JLC 4-layer stack
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
# currents (A): VDD 60 mA average (MCU + radio + sensors), VEXP 150 mA (GPS 100 + flow 35), VLED 4 LEDs x 36 mA
# (full white), VSYS / VREG 0.5 A (buck limit), VBUS bench only
I = {'VBAT': 0.6, 'BUCK_SW': 1.25, 'VREG': 0.5, 'VSYS': 0.5, 'VDD': 0.06, 'VEXP': 0.15, 'VLED': 0.144, 'VBUS': 0.5,
     'SMPS_LX': 0.1, 'VFBSMPS': 0.1}
MU0 = 4e-7 * math.pi
def seg_field(p, a, c, cur):
    """|B| (uT) at point p from a straight segment a-c (3D, mm) carrying cur (A)"""
    a, c, p = [tuple(x / 1000 for x in t) for t in (a, c, p)]
    L = math.dist(a, c)
    if L == 0: return 0.0
    u = tuple((c[i] - a[i]) / L for i in range(3))
    t = sum((p[i] - a[i]) * u[i] for i in range(3))
    foot = tuple(a[i] + t * u[i] for i in range(3))
    d = math.dist(p, foot)
    if d < 1e-5: return 0.0
    s1 = -t / math.hypot(t, d); s2 = (L - t) / math.hypot(L - t, d)
    return MU0 * cur / (4 * math.pi * d) * (s2 - s1) * 1e6
mag = B(F['U3'].GetPosition()); imu = B(F['U1'].GetPosition())
P_MAG = (mag[0], mag[1], 0.35)                # sensing element ~0.35 mm above F.Cu
contrib = {}
for t in b.GetTracks():
    n = t.GetNetname()
    if n not in I or t.GetClass() != 'PCB_TRACK': continue
    a, c = B(t.GetStart()), B(t.GetEnd()); z = Z.get(t.GetLayer(), 0)
    cur = I[n]
    # VDD near the magnetometer corner only feeds the local sensors (U3 + U4, ~1 mA), not the MCU
    if n == 'VDD' and min(math.dist(a, mag), math.dist(c, mag)) < 8.0: cur = 0.001
    contrib[n] = contrib.get(n, 0) + seg_field(P_MAG, (a[0], a[1], z), (c[0], c[1], z), cur)
# inductors: stray field of a shielded power inductor at distance r, dipole model calibrated to ~3 % of the core field
def ind_field(ref, cur, l_uH):
    p = B(F[ref].GetPosition()); r = math.dist(p, mag) / 1000
    m = 0.03 * cur * 25e-6 * 30          # effective leakage moment (A m^2): 3 % of N*I*A, N ~ 30, A ~ 25 mm^2
    return MU0 * m / (2 * math.pi * r ** 3) * 1e6, math.dist(p, mag)
print('=== %s' % LABEL)
print('Magnetometer U3 at (%.1f, %.1f), IMU U1 at (%.1f, %.1f)' % (mag + imu))
tot = sum(contrib.values())
print('Static field at the magnetometer from board currents (upper bound, uT): total %.2f' % tot)
for n, v in sorted(contrib.items(), key=lambda x: -x[1]):
    if v > 0.005: print('   %-8s %5.2f uT  (I = %.2f A)' % (n, v, I[n]))
for ref, cur, l in (('L3', 0.5, 22), ('L1', 0.1, 2.2)):
    if ref in F:
        bf, r = ind_field(ref, cur, l); print('   %s stray field %.3f uT at %.1f mm' % (ref, bf, r))
# distances on every layer from each sensor to aggressors
AGG = ['BUCK_SW', 'SMPS_LX', 'VBAT', 'VBUS', 'USB_DP', 'USB_DM', 'PWM_M1', 'PWM_M2', 'PWM_M3', 'PWM_M4', 'PWM_M5', 'PWM_M6',
       'PWM_M7', 'PWM_M8', 'RGB_DIN', 'Net-(D1-DOUT)', 'Net-(D2-DOUT)', 'Net-(D3-DOUT)', 'VLED', 'CRSF_TX', 'CRSF_RX', 'HSE_IN', 'HSE_OUT']
def cy(f):
    f.BuildCourtyardCaches(); c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    return unary_union([Polygon([B(c.Outline(i).CPoint(j)) for j in range(c.Outline(i).PointCount())]) for i in range(c.OutlineCount())])
for sref in ('U3', 'U1'):
    body = cy(F[sref])
    near = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n not in AGG: continue
        g = Point(B(t.GetPosition())) if t.GetClass() == 'PCB_VIA' else LineString([B(t.GetStart()), B(t.GetEnd())])
        d = g.distance(body); k = (n, 'via' if t.GetClass() == 'PCB_VIA' else LN.get(t.GetLayer(), '?'))
        near[k] = min(near.get(k, 99), d)
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if n in ('BUCK_SW', 'SMPS_LX') and f.GetReference() != sref:
                d = Point(B(p.GetPosition())).distance(body); k = (n, 'pad ' + f.GetReference())
                near[k] = min(near.get(k, 99), d)
    for ref in ('L3', 'L1', 'U12'):
        d = cy(F[ref]).distance(body); near[(ref, 'part')] = d
    print('%s (%s): closest aggressors (mm, from the courtyard):' % (sref, 'magnetometer' if sref == 'U3' else 'IMU'))
    for (n, l), d in sorted(near.items(), key=lambda x: x[1])[:8]:
        print('   %-14s %-7s %5.2f' % (n, l, d))
    under = sorted({n for (n, l), d in near.items() if d == 0.0})
    print('   tracks of aggressor nets crossing the sensor footprint:', under or 'none')
# In1 GND under the sensors
gnd = [z for z in b.Zones() if z.GetLayer() == pcbnew.In1_Cu and z.GetNetname() == 'GND']
fill = unary_union([Polygon([B(z.GetFilledPolysList(pcbnew.In1_Cu).Outline(i).CPoint(j)) for j in range(z.GetFilledPolysList(pcbnew.In1_Cu).Outline(i).PointCount())]).buffer(0)
                    for z in gnd for i in range(z.GetFilledPolysList(pcbnew.In1_Cu).OutlineCount())])
holes = []
for z in gnd:
    fp_ = z.GetFilledPolysList(pcbnew.In1_Cu)
    for i in range(fp_.OutlineCount()):
        for h in range(fp_.HoleCount(i)):
            hh = fp_.Hole(i, h); holes.append(Polygon([B(hh.CPoint(j)) for j in range(hh.PointCount())]))
for sref in ('U3', 'U1'):
    area = cy(F[sref]).buffer(1.0)
    cov = fill.intersection(area).area / area.area if fill.area else 0
    big = [h for h in holes if h.intersects(area) and h.area > 0.6]
    print('In1 GND under %s (+1 mm): %.0f %% copper, holes > 0.6 mm2: %d (antipads of vias only below that)' % (sref, 100 * cov, len(big)))
