# Rev H silkscreen labels (top): battery pad polarity, ESC link names, board name. Placed after silk_refs.
import sys, pcbnew
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
OX, OY = 150.0, 100.0
for d in list(b.GetDrawings()):
    if d.GetClass() == 'PCB_TEXT' and d.GetText() in ('+', '-', 'ESC B', 'ESC A', 'BAT', 'DimaQuadFC H'):
        b.Remove(d)
def txt(s, u, v, h=0.8, ang=0):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(h), pcbnew.FromMM(h))); t.SetTextThickness(pcbnew.FromMM(0.15))
    t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY - v))); t.SetTextAngleDegrees(ang)
    b.Add(t)
txt('+', -16.3, 7.2, 1.0)
txt('-', -16.3, 4.1, 1.0)
pcbnew.SaveBoard(B, b)
print('labels added')
