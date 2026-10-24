# DimaQuadESC rev B: silkscreen clean-up after silk_refs (USB-C outline lines at the chamfer edge, overlapped references)
# and project-library refresh (footprints stored as placed, so the library check matches).
import sys, re, pcbnew, subprocess
B_ = sys.argv[1]
b = pcbnew.LoadBoard(B_)
pcbnew.WriteDRCReport(b, '/tmp/claude-0/sfb.rpt', pcbnew.EDA_UNITS_MILLIMETRES, True)
t = open('/tmp/claude-0/sfb.rpt').read()
pts = [pcbnew.VECTOR2I(pcbnew.FromMM(float(m.group(1))), pcbnew.FromMM(float(m.group(2))))
       for m in re.finditer(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): Line on F.Silkscreen', t)]
kill = []
fps = list(b.GetFootprints())
for f in fps:
    for g in f.GraphicalItems():
        if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != 'PCB_TEXT' and any(g.HitTest(P, pcbnew.FromMM(0.02)) for P in pts):
            kill.append((f, g))
for f, g in kill:
    f.Remove(g)
n = len(kill)
k = 0
for ref in re.findall(r"\[silk_overlap\][^\n]*\n[^\n]*\n(?:[^\n]*\n)?\s*@\([^)]*\): Reference '([^']+)'", t):
    f = b.FindFootprintByReference(ref)
    if f is not None and f.Reference().IsVisible():
        f.Reference().SetVisible(False); k += 1
pcbnew.SaveBoard(B_, b)
print('silk lines removed:', n, '| references to Fab only:', k)
