set -e
cd /home/claude/outGPS_RB
# paths: /home/claude/genGPS_RB (scripts), /home/claude/outGPS_RB (project); uses genD/kisch.py, sexp.py, silk_refs.py, step_mesh.py
set -e
bash /home/claude/genGPS_RB/run_sch.sh                                                   # schematic + netlist check
cd /home/claude/outGPS_RB
python3 /home/claude/genGPS_RB/gen_pcb_gps.py /home/claude/outGPS_RB /tmp/claude-0/ngd.xml   # outline, placement, zones, U3 escape
bash /home/claude/genGPS_RB/loop_route.sh                                                 # Freerouting, GND stitching, DRC
python3 /home/claude/genD/silk_refs.py ACwing_GPS_A.kicad_pcb ACwing_GPS_A.kicad_sch.parts.json | grep labels
python3 /home/claude/genGPS_RB/make_3d_gps.py /home/claude/outGPS_RB/3d
cp /home/claude/models_e/JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal.step 3d/
python3 /home/claude/genGPS_RB/gps_finish.py /home/claude/outGPS_RB                         # silk extras, project library, 3D links
python3 -c "
import pcbnew
b=pcbnew.LoadBoard('/home/claude/outGPS_RB/ACwing_GPS_A.kicad_pcb')
pcbnew.WriteDRCReport(b,'/home/claude/outGPS_RB/ACwing_GPS_A_DRC.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)"
grep Found ACwing_GPS_A_DRC.rpt
python3 /home/claude/genGPS_RB/gps_bom.py /home/claude/outGPS_RB
python3 /mnt/skills/public/xlsx/scripts/recalc.py ACwing_GPS_A_BoM.xlsx > /dev/null
python3 /home/claude/genGPS_RB/cpl.py ACwing_GPS_A.kicad_pcb ACwing_GPS_A.kicad_sch.parts.json ACwing_GPS_A_CPL.xlsx
bash /home/claude/genGPS_RB/gerbers.sh > /dev/null
python3 /home/claude/genD/step_mesh.py ACwing_GPS_A.step /tmp/claude-0/meshGPSD.npz > /dev/null
python3 /home/claude/genGPS_RB/render_gps.py
