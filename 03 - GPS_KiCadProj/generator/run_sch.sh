set -e
cd /home/claude/outGPS_RB
python3 /home/claude/genGPS_RB/gen_sch_gps.py ACwing_GPS_A.kicad_sch
kicad-cli sch export netlist -o /tmp/claude-0/ngd.xml --format kicadxml ACwing_GPS_A.kicad_sch >/dev/null
python3 /home/claude/genGPS_RB/check_net.py /tmp/claude-0/ngd.xml ACwing_GPS_A.kicad_sch.expected.json ACwing_GPS_A.kicad_sch.nc.json
kicad-cli sch export pdf -o ACwing_GPS_A_schematic.pdf ACwing_GPS_A.kicad_sch >/dev/null
pdftoppm -r 90 -png ACwing_GPS_A_schematic.pdf /tmp/claude-0/gsch
