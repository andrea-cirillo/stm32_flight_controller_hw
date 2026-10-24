# Second Freerouting pass: the DSN carries the routed (unlocked) wires, Freerouting rips up and completes the rest.
set -e
cd /home/claude/outFCB
python3 /home/claude/genFCB/dsn_h.py ACwing_FC_A.kicad_pcb
rm -f ACwing_FC_A.ses; timeout 3000 xvfb-run -a java -jar /home/claude/tools/freerouting-1.9.0.jar -de ACwing_FC_A.dsn -do ACwing_FC_A.ses -mp 120 -mt 1 -oit 0.5 > /tmp/claude-0/frF2.log 2>&1 || true
test -s ACwing_FC_A.ses
python3 /home/claude/genE/finish.py ACwing_FC_A.kicad_pcb ACwing_FC_A.ses /tmp/claude-0/hdrc2.rpt | tail -2
python3 /home/claude/genE/cleanup.py ACwing_FC_A.kicad_pcb | tail -1
python3 -c "
import pcbnew
b=pcbnew.LoadBoard('/home/claude/outFCB/ACwing_FC_A.kicad_pcb')
pcbnew.WriteDRCReport(b,'/tmp/claude-0/hdrc2.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)" 2>/dev/null
grep -E "^\[|Found" /tmp/claude-0/hdrc2.rpt | grep -v silk | sed 's/(.*//' | sort | uniq -c
grep -A3 "^\[unconnected" /tmp/claude-0/hdrc2.rpt | grep "@" | head
