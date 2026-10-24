set -e
cd /home/claude/outFCB
rm -rf gerber && mkdir gerber
kicad-cli pcb export gerbers -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --use-drill-file-origin -o gerber/ ACwing_FC_A.kicad_pcb >/dev/null
kicad-cli pcb export drill --drill-origin plot --excellon-separate-th -u mm -o gerber/ ACwing_FC_A.kicad_pcb >/dev/null
(cd gerber && rm -f ../ACwing_FC_A_gerber.zip && zip -q ../ACwing_FC_A_gerber.zip *)
kicad-cli pcb export step -f -o ACwing_FC_A.step ACwing_FC_A.kicad_pcb 2>&1 | tail -1
ls gerber | wc -l
