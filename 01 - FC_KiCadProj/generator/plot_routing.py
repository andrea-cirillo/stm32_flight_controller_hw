import pcbnew, sys, os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
b=pcbnew.LoadBoard(os.environ.get('PCB','/home/claude/outE/DimaQuadFC_E.kicad_pcb')); OX,OY=150,100
layers=sys.argv[1].split(',')   # e.g. F,In2
out=sys.argv[2]; hl=sys.argv[3] if len(sys.argv)>3 else ''
LM={'F':pcbnew.F_Cu,'B':pcbnew.B_Cu,'In1':pcbnew.In1_Cu,'In2':pcbnew.In2_Cu}
col={pcbnew.F_Cu:'red',pcbnew.B_Cu:'blue',pcbnew.In2_Cu:'orange',pcbnew.In1_Cu:'green'}
zc={'GND':'#2a7','VBAT':'#e60','VDD':'#c3c','M1_N':'#36f','M2_N':'#36f','M3_N':'#36f','M4_N':'#36f'}
fig,ax=plt.subplots(figsize=(11,11))
T=lambda p:(p.x/1e6-OX, OY-p.y/1e6)
ps=pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps); o=ps.Outline(0)
ax.add_patch(MP([T(o.CPoint(k)) for k in range(o.PointCount())],closed=True,fc='none',ec='k',lw=1))
for z in b.Zones():
    if z.GetIsRuleArea():
        o=z.Outline().Outline(0); ax.add_patch(MP([T(o.CPoint(k)) for k in range(o.PointCount())],closed=True,fc='none',ec='gray',ls='--',lw=0.5)); continue
    if z.GetLayer() not in [LM[l] for l in layers]: continue
    f=z.GetFilledPolysList(z.GetLayer())
    for i in range(f.OutlineCount()):
        o=f.Outline(i); ax.add_patch(MP([T(o.CPoint(k)) for k in range(o.PointCount())],closed=True,fc=zc.get(z.GetNetname(),'#888'),alpha=0.35,ec='none'))
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        p=T(t.GetPosition()); ax.add_patch(plt.Circle(p,0.225,color='k'))
    elif t.GetLayer() in [LM[l] for l in layers]:
        a,c=T(t.GetStart()),T(t.GetEnd()); ax.plot([a[0],c[0]],[a[1],c[1]],color=col[t.GetLayer()],lw=max(0.6,t.GetWidth()/1e6*20),solid_capstyle='round',alpha=1 if t.GetNetname()==hl else 0.7)
for f in b.GetFootprints():
    for p in f.Pads():
        L=pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: L=None
        sh=p.GetEffectivePolygon()
        for i in range(sh.OutlineCount()):
            o=sh.Outline(i); pts=[T(o.CPoint(k)) for k in range(o.PointCount())]
            vis = L is None or L in [LM[l] for l in layers]
            ax.add_patch(MP(pts,closed=True,fc=('yellow' if p.GetNetname()==hl else ('white' if L is None else col[L])) if vis else 'none',alpha=0.6 if vis else 0.15,ec='k',lw=0.3))
    pp=T(f.GetPosition()); ax.text(pp[0],pp[1],f.GetReference(),fontsize=6,alpha=0.8)
ax.set_xlim(-21.5,21.5); ax.set_ylim(-21.5,21.5); ax.set_aspect('equal'); ax.grid(alpha=0.25); ax.set_title('ACwing FC rev A - tracks: F.Cu red, In2 orange, B.Cu blue; zones: GND green, VDD violet')
plt.savefig(out,dpi=75,bbox_inches='tight')
