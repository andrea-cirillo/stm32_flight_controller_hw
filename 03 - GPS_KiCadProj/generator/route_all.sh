set -e
cd /home/claude/outGPS_RB
python3 /home/claude/genGPS_RB/route_gps.py ACwing_GPS_A.kicad_pcb /home/claude/outGPS_RB 2>&1 | grep -v "^$" | tail -3
python3 /home/claude/genD/cleanup.py ACwing_GPS_A.kicad_pcb | tail -1
python3 /home/claude/genFlow/gnd_bridge.py ACwing_GPS_A.kicad_pcb | tail -2
python3 -c "
import pcbnew
b=pcbnew.LoadBoard('/home/claude/outGPS_RB/ACwing_GPS_A.kicad_pcb')
pcbnew.WriteDRCReport(b,'/tmp/claude-0/gdrc.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)"
grep -E "^\[|Found" /tmp/claude-0/gdrc.rpt | sed 's/(.*//' | sort | uniq -c
python3 - <<'PY'
import re
t=open('/tmp/claude-0/gdrc.rpt').read()
for bl in re.split(r'\n(?=\[)', t):
    if bl.startswith(('[unconnected','[clearance','[copper_edge','[starved','[hole','[items_not','[track_dang','[via_dang')):
        items=[re.sub(r'\s+',' ',l.strip()) for l in bl.splitlines() if '@(' in l]
        print(bl.split(']')[0][1:],':',' <-> '.join(items)[:230])
PY
