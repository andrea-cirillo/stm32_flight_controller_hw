# Makes the project self-contained: every footprint used on the board is stored in the project library
# ACwing.pretty exactly as placed (3D models in ${KIPRJMOD}/3d, project-specific edits such as the pogo-pad
# clearance), and the board/schematic link to DimaQuad:<name>. KiCad's "footprint does not match library" check
# then compares against these copies (the stock KiCad library copies differ by version and by 3D model path).
import sys, os, re, json, collections, pcbnew
OUT = sys.argv[1]
BOARD = os.path.join(OUT, 'ACwing_FC_A.kicad_pcb')
LIB = os.path.join(OUT, 'ACwing.pretty')
b = pcbnew.LoadBoard(BOARD)
groups = collections.defaultdict(list)
for fp in b.GetFootprints():
    groups[str(fp.GetFPID().GetLibItemName())].append(fp)
def norm(fp):
    c = pcbnew.FOOTPRINT(fp)
    if c.IsFlipped():
        c.Flip(c.GetPosition(), False)
    c.SetOrientationDegrees(0); c.SetPosition(pcbnew.VECTOR2I(0, 0))
    c.SetReference('REF**'); c.SetValue(str(fp.GetFPID().GetLibItemName()))
    c.Reference().SetPosition(pcbnew.VECTOR2I(0, pcbnew.FromMM(-1.5))); c.Reference().SetTextAngleDegrees(0)
    c.SetFPID(pcbnew.LIB_ID('ACwing', str(fp.GetFPID().GetLibItemName())))
    c.SetLocked(False)
    c.SetAttributes(c.GetAttributes() & ~(pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM))   # no DNP flags in the library
    return c
def sig(fp):   # graphics + pads, to pick the most common variant of a footprint
    n = norm(fp)
    g = sorted((it.GetClass(), it.GetLayer(), str(it.GetStart()), str(it.GetEnd())) for it in n.GraphicalItems() if it.GetClass() != 'FP_TEXT')
    return repr(g)
for name, fps in groups.items():
    by = collections.Counter(sig(f) for f in fps)
    ref_fp = [f for f in fps if sig(f) == by.most_common(1)[0][0]][0]
    pcbnew.FootprintSave(LIB, norm(ref_fp))
    for f in fps:
        f.SetFPID(pcbnew.LIB_ID('ACwing', name))
pcbnew.SaveBoard(BOARD, b)
print('footprints stored in ACwing.pretty:', len(groups))
