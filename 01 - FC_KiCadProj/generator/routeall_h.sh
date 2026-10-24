set -e
cd /home/claude/outFCB
python3 /home/claude/genFCB/dsn_h.py ACwing_FC_A.kicad_pcb
rm -f ACwing_FC_A.ses; timeout 3000 xvfb-run -a java -jar /home/claude/tools/freerouting-1.9.0.jar -de ACwing_FC_A.dsn -do ACwing_FC_A.ses -mp 40 -mt 1 -oit 0.5 > /tmp/claude-0/frH.log 2>&1 || true
grep -c completed /tmp/claude-0/frH.log || true
python3 /home/claude/genE/finish.py ACwing_FC_A.kicad_pcb ACwing_FC_A.ses /tmp/claude-0/hdrc2.rpt | tail -2
python3 /home/claude/genE/cleanup.py ACwing_FC_A.kicad_pcb | tail -1
python3 -c "
import pcbnew
b=pcbnew.LoadBoard('/home/claude/outFCB/ACwing_FC_A.kicad_pcb')
pcbnew.WriteDRCReport(b,'/tmp/claude-0/hdrc2.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)"
grep -E "^\[" /tmp/claude-0/hdrc2.rpt | grep -v "lib_footprint\|silk" | sed 's/(.*//' | sort | uniq -c
python3 - <<'PY'
import re
t=open('/tmp/claude-0/hdrc2.rpt').read()
for bl in re.split(r'\n(?=\[)', t):
    if bl.startswith(('[unconnected_items]','[clearance]','[via_dangling]','[track_dangling]','[shorting','[tracks_crossing','[hole_clearance]','[copper_edge','[items_not_allowed]','[starved','[isolated')):
        items=[re.sub(r'\s+',' ',l.strip()) for l in bl.splitlines() if '@(' in l]
        print(bl.split(']')[0][1:],':',' <-> '.join(i.replace(' mm','') for i in items)[:240])
PY
python3 /home/claude/genFCB/astar.py ACwing_FC_A.kicad_pcb | grep "A\*" || true
python3 /home/claude/genE/cleanup.py ACwing_FC_A.kicad_pcb | tail -1
python3 -c "
import pcbnew
b=pcbnew.LoadBoard('/home/claude/outFCB/ACwing_FC_A.kicad_pcb')
pcbnew.WriteDRCReport(b,'/tmp/claude-0/hdrc2.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)"
echo '--- after A*'
grep -E "^\[" /tmp/claude-0/hdrc2.rpt | grep -v "lib_footprint\|silk" | sed 's/(.*//' | sort | uniq -c
python3 - <<'PY'
import re
t=open('/tmp/claude-0/hdrc2.rpt').read()
for bl in re.split(r'\n(?=\[)', t):
    if bl.startswith(('[unconnected_items]','[clearance]','[via_dangling]','[track_dangling]','[shorting','[tracks_crossing','[hole_clearance]','[copper_edge','[items_not_allowed]','[starved','[isolated')):
        items=[re.sub(r'\s+',' ',l.strip()) for l in bl.splitlines() if '@(' in l]
        print(bl.split(']')[0][1:],':',' <-> '.join(i.replace(' mm','') for i in items)[:240])
PY
