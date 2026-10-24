# DimaQuadGPS rev A: STEP models missing from the KiCad 7 library (same frame convention as genD/make_3d.py).
import sys
sys.argv = sys.argv[:2]
exec(open('/home/claude/genD/make_3d.py').read().split('# ---- PowerPAK')[0])

# ---- u-blox SAM-M10Q: 15.5 x 15.5 x 6.3 mm, module PCB + shield, 15 x 15 x 4 ceramic patch on top
parts = [(box(15.5, 15.5, 0.9, 0, 0, 0.0), C(.10, .30, .15), 'pcb'),
         (box(14.6, 14.6, 1.3, 0, 0, 0.9), METAL, 'shield'),
         (box(15.0, 15.0, 4.0, 0, 0, 2.2).edges('|Z').fillet(0.4), C(.80, .78, .70), 'patch'),
         (box(11.6, 11.6, 0.1, 0, 0, 6.2), C(.85, .85, .87), 'electrode'),
         (cq.Workplane('XY').circle(0.5).extrude(0.12).translate((0, -1.6, 6.2)), METAL, 'feed')]
for n, (x, y) in enumerate([(-6.6, -3.8 + 1.9 * k) for k in range(5)] + [(-3.8 + 1.9 * k, 6.6) for k in range(5)] +
                           [(6.6, 3.8 - 1.9 * k) for k in range(5)] + [(3.8 - 1.9 * k, -6.6) for k in range(5)]):
    parts.append((box(1.0 if abs(x) > 6 else 0.8, 0.8 if abs(x) > 6 else 1.0, 0.05, x, -y, -0.02), GOLD, 'p%d' % n))
save('ublox_SAM-M10Q', parts)
