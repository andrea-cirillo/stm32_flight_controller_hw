# ACwing FC rev A - full regeneration (KiCad 7 + pcbnew, Freerouting 1.9 with xvfb, shapely, openpyxl, cadquery)
# paths: /home/claude/genFCB (scripts), /home/claude/outFCB (project); helpers from the rev E generator (genE)
set -e
bash /home/claude/genFCB/run_sch_h.sh        # schematic, netlist check, PDF
bash /home/claude/genFCB/prep_h.sh           # outline, placement, planes, RF / LDO / MCU details, pogo stubs, GND fan-out, crystal (A*)
bash /home/claude/genFCB/routeall_h.sh       # Freerouting (20 min cap), import, cleanup, A* for leftovers, DRC
bash /home/claude/genFCB/finish_h.sh         # silkscreen, library, DRC, BoM / costing / JLC BoM / CPL, Gerber, STEP, renders
