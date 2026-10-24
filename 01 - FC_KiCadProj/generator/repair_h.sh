# Rip-up and A* repair loop for the connections Freerouting / A* left open (rev F).
cd /home/claude/outFCB
for it in 1 2 3 4 5 6; do
  python3 -c "
import pcbnew
b=pcbnew.LoadBoard('ACwing_FC_A.kicad_pcb')
pcbnew.WriteDRCReport(b,'/tmp/claude-0/rp.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)" 2>/dev/null
  python3 - > /tmp/claude-0/rp_items.txt <<'PY'
import re
t=open('/tmp/claude-0/rp.rpt').read()
for bl in re.split(r'\n(?=\[)', t):
    if bl.startswith('[unconnected_items]'):
        pts=re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): [^\[]*\[([^\]]*)\]', bl)
        if len(pts)==2:
            (x1,y1,n),(x2,y2,_)=pts
            print(n, x1, y1, x2, y2)
PY
  n=$(wc -l < /tmp/claude-0/rp_items.txt)
  echo "iteration $it: open $n"
  [ "$n" -eq 0 ] && break
  R=$(echo "1.6 + 0.6*$it" | bc)
  while read net x1 y1 x2 y2; do
    rip=""
    for xy in "$x1 $y1" "$x2 $y2"; do
      set -- $xy
      r=$(python3 /home/claude/genE/ripbox.py ACwing_FC_A.kicad_pcb $(echo "$1-$R" | bc) $(echo "$2-$R" | bc) $(echo "$1+$R" | bc) $(echo "$2+$R" | bc))
      rip="$rip $r"
    done
    others=$(echo $rip | tr ' ' '\n' | sort -u | grep -vx "$net" | tr '\n' ' ')
    echo "  $net: ripped [$others]"
    python3 /home/claude/genFCB/astar.py ACwing_FC_A.kicad_pcb "$net" $others 2>/dev/null | grep "A\*" | sed 's/^/    /'
  done < /tmp/claude-0/rp_items.txt
  python3 /home/claude/genE/cleanup.py ACwing_FC_A.kicad_pcb > /dev/null
done
python3 -c "
import pcbnew
b=pcbnew.LoadBoard('ACwing_FC_A.kicad_pcb')
pcbnew.WriteDRCReport(b,'/tmp/claude-0/hdrc2.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)" 2>/dev/null
grep -E "^\[|Found" /tmp/claude-0/hdrc2.rpt | grep -v silk | sed 's/(.*//' | sort | uniq -c
