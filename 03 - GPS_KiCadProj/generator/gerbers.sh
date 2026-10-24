set -e
cd /home/claude/outGPS_RB
rm -rf gerber && mkdir gerber
kicad-cli pcb export gerbers -l F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --use-drill-file-origin -o gerber/ ACwing_GPS_A.kicad_pcb >/dev/null
kicad-cli pcb export drill --drill-origin plot --excellon-separate-th -u mm -o gerber/ ACwing_GPS_A.kicad_pcb >/dev/null
(cd gerber && rm -f ../ACwing_GPS_A_gerber.zip && zip -q ../ACwing_GPS_A_gerber.zip *)
kicad-cli pcb export step -f -o ACwing_GPS_A.step ACwing_GPS_A.kicad_pcb 2>&1 | tail -1
kicad-cli sch export pdf -o ACwing_GPS_A_schematic.pdf ACwing_GPS_A.kicad_sch >/dev/null
ls gerber
