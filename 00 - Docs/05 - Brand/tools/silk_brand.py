# ACwing silkscreen pass for one board: logo(s), board name, author, connector labels. Places everything in free
# space (no pads, courtyards, other silk), then saves. python3 silk_brand.py <board> <config name>
import sys, os, math, shutil, tempfile, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from silk_free import free_area, best_box, B, bbox_poly, polyset
from shapely.geometry import box, Point
OX, OY = 150.0, 100.0
LOGO_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ACwing_Logo.pretty')
BOARD, CFG = sys.argv[1], sys.argv[2]
REV = sys.argv[3] if len(sys.argv) > 3 else 'A'      # board revision letter printed on the silkscreen
PRJ = os.path.dirname(os.path.abspath(BOARD))
LIBNICK = {'fc': 'ACwing', 'esc': 'ACwing', 'gps': 'ACwing_GPS', 'flow': 'ACwing_Flow'}[CFG]
b = pcbnew.LoadBoard(BOARD)
_KEEP = []  # removed items stay referenced (SWIG proxy bug in KiCad 7)
def P(u, v): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY - v))
# ---- remove the old branding texts / logos of a previous run
OLD = ('ACwing', 'UAV Control', '1S power board', 'rev ', 'Andrea Cirillo', 'FC rev', 'ESC A', 'ESC B', 'QWIIC', 'ELRS', 'USB', 'CHARGE', 'TO FC', 'BAT', 'GPS', 'FLOW', 'QWIIC', 'ESC 1S')
for d in list(b.GetDrawings()):
    if d.GetClass() == 'PCB_TEXT' and d.GetText().startswith(OLD):
        _KEEP.append(d); b.Remove(d)
for f in list(b.GetFootprints()):
    if f.GetReference().startswith('LOGO'):
        _KEEP.append(f); b.Remove(f)
def add_text(s, u, v, h, bottom=False, bold=False, rot=0):
    t = pcbnew.PCB_TEXT(b); t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T)); t.SetText(s); t.SetLayer(pcbnew.B_SilkS if bottom else pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(h), pcbnew.FromMM(h)))
    t.SetTextThickness(pcbnew.FromMM(max(0.15, h * (0.2 if bold else 0.15))))
    t.SetPosition(P(u, v)); t.SetMirrored(bottom); b.Add(t); return t
def text_box(s, h, bold=False):
    t = add_text(s, 0, 0, h, bold=bold); g = bbox_poly(t.GetBoundingBox()); _KEEP.append(t); b.Remove(t)
    x0, y0, x1, y1 = g.bounds; return x1 - x0, y1 - y0
def place_text(s, h, bottom, prefer, maxr=8.0, bold=False, quiet=False, rot=0):
    w, hh = text_box(s, h, bold)
    if rot: w, hh = hh, w
    fr = free_area(b, bottom)
    best = None
    for r in [0.25 * k for k in range(int(maxr / 0.25) + 1)]:
        n = max(1, int(2 * math.pi * r / 0.25))
        for k in range(n):
            a = 2 * math.pi * k / n; q = (prefer[0] + r * math.cos(a), prefer[1] + r * math.sin(a))
            if fr.contains(box(q[0] - w / 2 - 0.1, q[1] - hh / 2 - 0.1, q[0] + w / 2 + 0.1, q[1] + hh / 2 + 0.1)):
                best = q; break
        if best: break
    if best is None:
        if not quiet: print('  NO SPOT for text', repr(s))
        return None
    add_text(s, best[0], best[1], h, bottom, bold, rot)
    print('  text %-22s at (%6.2f, %6.2f) %s h %.1f rot %d' % (repr(s), best[0], best[1], 'bottom' if bottom else 'top', h, rot))
    return best
def place_logo(kind, bottom, prefer, hmax, hmin=4.0, reserve_below=0.0):
    asp = {'Full': 1.154, 'Mark': 1.535}[kind]
    fr = free_area(b, bottom)
    # leave room for a text line under the logo when asked (logo box extended downward)
    res = best_box(fr, asp * (1.0 / (1.0 + reserve_below)), hmin * (1 + reserve_below), hmax * (1 + reserve_below), prefer=prefer) if reserve_below else best_box(fr, asp, hmin, hmax, prefer=prefer)
    if res is None:
        print('  NO SPOT for logo'); return None
    H, u, v = res
    h = H / (1 + reserve_below) if reserve_below else H
    h = math.floor(h)                                   # footprints exist for whole mm sizes
    h = max(4, min(12, h)) if h not in (11,) else 10
    v_logo = v + (H - h) / 2 if reserve_below else v
    name = 'ACwing_Logo_%s_%dmm' % (kind, h)
    dst = os.path.join(PRJ, LIBNICK + '.pretty')
    shutil.copy(os.path.join(LOGO_LIB, name + '.kicad_mod'), dst)
    fp = pcbnew.FootprintLoad(dst, name)
    fp.SetReference('LOGO%d' % (1 + sum(1 for f in b.GetFootprints() if f.GetReference().startswith('LOGO'))))
    fp.Reference().SetVisible(False); fp.SetFPID(pcbnew.LIB_ID(LIBNICK, name))
    fp.SetPosition(P(u, v_logo)); b.Add(fp)
    if bottom:
        fp.Flip(fp.GetPosition(), True)   # left-right: reads correctly seen from below
    fp.SetLocked(True)
    print('  logo %s %d mm at (%.2f, %.2f) %s' % (kind, h, u, v_logo, 'bottom' if bottom else 'top'))
    return (u, v_logo, h, asp * h)
def logo_block(kind, bottom, prefer, hmax, lines, hmin=None, th=0.8, gap=0.35):
    hmin = hmin or {'Full': 5, 'Mark': 4}[kind]   # Full logo >= 5 mm keeps every stroke >= 0.15 mm (JLC silk minimum)
    """logo with its text lines under it, as one block in the largest free box near 'prefer'."""
    asp = {'Full': 1.154, 'Mark': 1.535}[kind]
    tw = [text_box(l, th)[0] for l in lines]
    fr = free_area(b, bottom)
    x0, y0, x1, y1 = fr.bounds
    for h in range(int(hmax), int(hmin) - 1, -1):
        W = max([asp * h] + tw) + 0.2; Hh = h + len(lines) * (th + gap) + 0.2
        best = None
        y = y0 + Hh / 2
        while y <= y1 - Hh / 2:
            x = x0 + W / 2
            while x <= x1 - W / 2:
                if fr.contains(box(x - W / 2, y - Hh / 2, x + W / 2, y + Hh / 2)):
                    d = math.dist((x, y), prefer)
                    if best is None or d < best[0]:
                        best = (d, x, y)
                x += 0.25
            y += 0.25
        if best:
            _, x, y = best
            top = y + Hh / 2 - 0.1
            name = 'ACwing_Logo_%s_%dmm' % (kind, h)
            dst = os.path.join(PRJ, LIBNICK + '.pretty')
            shutil.copy(os.path.join(LOGO_LIB, name + '.kicad_mod'), dst)
            fp = pcbnew.FootprintLoad(dst, name)
            fp.SetReference('LOGO%d' % (1 + sum(1 for f in b.GetFootprints() if f.GetReference().startswith('LOGO'))))
            fp.Reference().SetVisible(False); fp.SetFPID(pcbnew.LIB_ID(LIBNICK, name))
            fp.SetPosition(P(x, top - h / 2)); b.Add(fp)
            if bottom:
                fp.Flip(fp.GetPosition(), True)   # left-right: reads correctly seen from below
            fp.SetLocked(True)
            yy = top - h - gap - th / 2
            for l in lines:
                add_text(l, x, yy, th, bottom); yy -= th + gap
            print('  block %s logo %d mm + %d lines at (%.2f, %.2f) %s' % (kind, h, len(lines), x, y, 'bottom' if bottom else 'top'))
            return x, y, h
    print('  NO SPOT for logo block'); return None
def label(ref, s, h=0.8, maxr=6.0):
    f = b.FindFootprintByReference(ref); c = B(f.GetPosition())
    return text_any(s, f.IsFlipped(), c, h, maxr)
def text_any(s, bottom, c, h=0.8, maxr=6.0, alts=()):
    # fallbacks (text height stays at the 0.8 mm DRC minimum): rotated 90 deg, a bit farther, shorter wording
    for side, radii in ((bottom, (maxr,)), (not bottom, (maxr,)), (bottom, (maxr * 1.5,))):
        for txt in (s,) + tuple(alts):
            for rot in (0, 90):
                for r in radii:
                    if place_text(txt, h, side, c, r, quiet=True, rot=rot): return True
    print('  NO SPOT for text', repr(s)); return None

if CFG == 'fc':
    logo_block('Full', False, (5.0, 3.0), 8, ['FC rev %s' % REV])
    (logo_block('Full', True, (14.0, -3.0), 8, ['ACwing FC rev %s' % REV])
     or logo_block('Mark', True, (14.0, -3.0), 6, ['ACwing FC rev %s' % REV]))
    for ref, s_ in (('J2', 'ESC A'), ('J6', 'ESC B'), ('J3', 'GPS'), ('J4', 'FLOW'), ('J5', 'ELRS'), ('J1', 'USB')):
        label(ref, s_)
    text_any('BAT', False, (-16.3, 9.2), 0.8, 3)
elif CFG == 'esc':
    for d in list(b.GetDrawings()):
        pass
    text_any('ACwing ESC 1S rev %s' % REV, False, (0.0, 0.5), 0.8, 6.0, ('ESC 1S rev %s' % REV,))
    logo_block('Full', False, (10.0, 15.0), 7, [])
    logo_block('Full', True, (0.0, 1.5), 10, ['ACwing ESC 1S rev %s' % REV])
    for ref, s_ in (('J1', 'TO FC'), ('J4', 'CHARGE')):
        label(ref, s_)

elif CFG == 'gps':
    text_any('ACwing GPS rev %s' % REV, False, (2.6, 13.4), 0.8, 8.0, ('GPS rev %s' % REV,))
    logo_block('Full', False, (-11.3, 0.0), 6, [])
    (logo_block('Full', True, (-3.8, 8.0), 8, ['ACwing GPS rev %s' % REV])
     or logo_block('Full', True, (-3.8, 8.0), 8, ['GPS rev %s' % REV]) or logo_block('Mark', True, (-3.8, 8.0), 6, []))
    for ref, s_ in (('J1', 'QWIIC IN'), ('J2', 'QWIIC OUT')):
        label(ref, s_)
elif CFG == 'flow':
    logo_block('Full', True, (0.0, 1.5), 9, ['ACwing Flow rev A'])
pcbnew.SaveBoard(BOARD, b)
b = pcbnew.LoadBoard(BOARD)
pcbnew.WriteDRCReport(b, os.path.join(tempfile.gettempdir(), 'brand_drc.rpt'), pcbnew.EDA_UNITS_MILLIMETRES, True)
import re
t = open(os.path.join(tempfile.gettempdir(), 'brand_drc.rpt')).read()
print('  ' + ' | '.join(re.findall(r'Found [^*]*', t)))
for bl in re.split(r'\n(?=\[)', t):
    if bl.startswith('['):
        print('   ', bl.split(']')[0][1:], ' / '.join(re.sub(r'\s+', ' ', l.strip()) for l in bl.splitlines() if '@(' in l)[:200])
