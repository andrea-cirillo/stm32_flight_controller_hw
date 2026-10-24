set -e
cd /home/claude/outFCB
python3 /home/claude/genFCB/gen_pcb_h.py /home/claude/outFCB /tmp/claude-0/nH.xml | tail -2
python3 /home/claude/genFCB/route_h.py ACwing_FC_A.kicad_pcb
# pre-routes with A* before Freerouting (Freerouting left these open on some runs): crystal
python3 /home/claude/genFCB/astar.py ACwing_FC_A.kicad_pcb HSE_OUT HSE_IN | grep "A\*" || true
python3 /home/claude/genE/lock_nets.py ACwing_FC_A.kicad_pcb HSE_OUT HSE_IN
cp ACwing_FC_A.kicad_pcb /tmp/claude-0/H_prerouted.kicad_pcb
