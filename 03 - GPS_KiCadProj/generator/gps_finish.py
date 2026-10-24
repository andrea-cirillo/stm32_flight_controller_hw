# ACwing GPS rev A: silkscreen extras, project footprint library (ACwing_GPS.pretty) with project 3D models.
#   python3 gps_finish.py <out dir>
import sys, os, re, json, shutil
import pcbnew

OUT = sys.argv[1]
PROJECT = 'ACwing_GPS_A'
BOARD = os.path.join(OUT, PROJECT + '.kicad_pcb')
SCH = os.path.join(OUT, PROJECT + '.kicad_sch')
OX, OY = 150.0, 100.0
LIB = 'ACwing_GPS'
LIB3D = '/usr/share/kicad/3dmodels'
D3 = os.path.join(OUT, '3d')
MODEL_FOR = {'ublox_SAM-M8Q': 'ublox_SAM-M10Q'}          # footprint -> project model (made by make_3d_gps.py)
def P(u, v): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY - v))

b = pcbnew.LoadBoard(BOARD)
# ---------------------------------------------------------------- 1. silkscreen: front arrow, board name (top)
TAG = 'gps_finish'
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.F_SilkS and (d.GetClass() == 'PCB_TEXT' and d.GetText().startswith(('FRONT', 'ACwing_GPS'))
                                           or d.GetClass() == 'PCB_SHAPE' and abs(pcbnew.ToMM(d.GetWidth()) - 0.151) < 1e-6):
        b.Delete(d)
def text(s, u, v, size=0.8, just=None):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(P(u, v))
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size))); t.SetTextThickness(pcbnew.FromMM(0.15))
    if just == 'left':
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    elif just == 'right':
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    b.Add(t)
def line(a, c):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.F_SilkS)
    s.SetStart(P(*a)); s.SetEnd(P(*c)); s.SetWidth(pcbnew.FromMM(0.151)); b.Add(s)
# arrow toward the FC front: the FC is mounted at 45 deg and its front is the top-right corner (white LEDs D1/D2),
# so the arrow points along +u +v, left of the module tip on the top edge
ax, ay = -4.6, 12.4
line((ax - 0.85, ay - 0.85), (ax + 0.85, ay + 0.85))
line((ax + 0.85, ay + 0.85), (ax + 0.85, ay + 0.1)); line((ax + 0.85, ay + 0.85), (ax + 0.1, ay + 0.85))
text('FRONT', ax - 1.2, ay + 0.3, just='right')
text('ACwing GPS rev A', 2.6, 13.4, just='left')
pcbnew.SaveBoard(BOARD, b)

# ---------------------------------------------------------------- 2. project library + 3D models
os.makedirs(os.path.join(OUT, LIB + '.pretty'), exist_ok=True)
os.makedirs(D3, exist_ok=True)
b = pcbnew.LoadBoard(BOARD)
names = {}
for f in b.GetFootprints():
    fpid = f.GetFPID()
    lib, name = str(fpid.GetLibNickname()), str(fpid.GetLibItemName())
    names[name] = lib if lib != LIB else names.get(name, lib)
for name, lib in names.items():
    if lib == LIB:
        continue
    src = pcbnew.FootprintLoad('/usr/share/kicad/footprints/%s.pretty' % lib, name)
    pcbnew.FootprintSave(os.path.join(OUT, LIB + '.pretty'), src)
for f in b.GetFootprints():
    f.SetFPID(pcbnew.LIB_ID(LIB, str(f.GetFPID().GetLibItemName())))
pcbnew.SaveBoard(BOARD, b)

def fix_models(text_):
    def sub(m):
        base = m.group(2)
        dst = MODEL_FOR.get(base, base)
        if not os.path.exists(os.path.join(D3, dst + '.step')):
            src = os.path.join(LIB3D, m.group(1) + '.3dshapes', base + '.step')
            if os.path.exists(src):
                shutil.copy(src, os.path.join(D3, dst + '.step'))
            else:
                print('NO MODEL', base)
        return '(model "${KIPRJMOD}/3d/%s.step"' % dst
    return re.subn(r'\(model "?\$\{KICAD\d_3DMODEL_DIR\}/([^/"]+)\.3dshapes/([^/" ]+)\.(?:wrl|step)"?', sub, text_)
s, n = fix_models(open(BOARD).read()); open(BOARD, 'w').write(s)
nl = 0
for fn in os.listdir(os.path.join(OUT, LIB + '.pretty')):
    p = os.path.join(OUT, LIB + '.pretty', fn)
    t, k = fix_models(open(p).read()); open(p, 'w').write(t); nl += k
print('model paths: board %d, library %d; models in 3d/: %s' % (n, nl, ' '.join(sorted(os.listdir(D3)))))

# schematic + parts.json links
s = open(SCH).read()
s2, k = re.subn(r'\(property "Footprint" "(?!%s:)[^":]+:([^"]+)"' % LIB, r'(property "Footprint" "%s:\1"' % LIB, s)
open(SCH, 'w').write(s2)
pj = SCH + '.parts.json'
pp = json.load(open(pj))
for v in pp.values():
    if v.get('fp') and ':' in v['fp']:
        v['fp'] = LIB + ':' + v['fp'].split(':', 1)[1]
json.dump(pp, open(pj, 'w'), indent=0)
open(os.path.join(OUT, 'fp-lib-table'), 'w').write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.pretty")(options "")'
    '(descr "ACwing GPS project footprints (3D models in ${KIPRJMOD}/3d)"))\n)\n' % (LIB, LIB))
if os.path.exists(os.path.join(OUT, 'sym-lib-table')):
    os.remove(os.path.join(OUT, 'sym-lib-table'))
print('library', LIB, 'footprints', len(os.listdir(os.path.join(OUT, LIB + '.pretty'))), '| schematic links', k)
