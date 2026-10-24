# ACwing GPS rev A: GNSS + compass expansion board for DimaQuadFC rev H (Qwiic expansion bus, 20 x 20 holes) (KiCad 7 schematic generator).
import sys, json
sys.path.insert(0, '/home/claude/genD')
import kisch
from kisch import Schematic, POWER_LIB

OUT = sys.argv[1]
PROJECT = 'ACwing_GPS_A'
POWER_LIB.update({'GND': 'power:GND'})   # rev B: +3V3 as net labels (the rail comes in from the Qwiic bus)
sch = Schematic(PROJECT, 'A4', title=dict(
    title='ACwing GPS rev A - GNSS + compass for DimaQuadFC H',
    date='2026-10-19', rev='D', company='UAV Control - A. Cirillo',
    comments=['30 x 30 mm, 2 layers, 1.0 mm; same 20 x 20 hole pattern as the flight controller rev F',
              'Expansion bus: Qwiic (JST SH 4-pin) x 2, pass-through, from FC J3; daisy-chain to the flow board',
              'u-blox SAM-M10Q (integrated patch antenna, pin compatible with SAM-M8Q)',
              'Generated automatically: run ERC before release']))

FP_R = 'Resistor_SMD:R_0402_1005Metric'
FP_C = 'Capacitor_SMD:C_0402_1005Metric'
FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'

def _fpos(x, y, rot, side='right'):
    if rot in (0, 180):
        if side == 'left':
            return {'Reference': (x - 2.54, y - 1.27), 'Value': (x - 2.54, y + 1.27), 'just': 'right'}
        return {'Reference': (x + 2.54, y - 1.27), 'Value': (x + 2.54, y + 1.27), 'just': 'left'}
    return {'Reference': (x, y - 2.54), 'Value': (x, y + 3.81)}

def R(ref, val, x, y, a, b, rot=0, fp=FP_R, side='right', **kw):
    return sch.part(ref, 'Device:R', val, x, y, rot, {'1': a, '2': b}, fp=fp, field_pos=_fpos(x, y, rot, side), **kw)

def C(ref, val, x, y, a='+3V3', b='GND', rot=0, fp=FP_C, pol=False, side='right', **kw):
    return sch.part(ref, 'Device:C_Polarized' if pol else 'Device:C', val, x, y, rot, {'1': a, '2': b},
                    fp=fp, field_pos=_fpos(x, y, rot, side), **kw)

def block(title, a, b):
    sch.rect(a, b)
    sch.text(title, (a[0] + 1.27, a[1] + 1.27), size=1.8, bold=True)

def note(s, p, size=1.27):
    sch.text(s, p, size=size)

# ================================================================ A. EXPANSION BUS (QWIIC) x 2
block('A - Expansion bus (Qwiic / STEMMA QT), 3.3 V from the FC', (10.16, 10.16), (142.24, 78.74))
QW = {'1': 'GND', '2': '+3V3', '3': 'I2C_SDA', '4': 'I2C_SCL'}
for k, (ref, val, nt) in enumerate((('J1', 'Qwiic IN', 'JST SH 1.0 mm 4-pin side entry, TOP side (rev D), right edge (mouth toward +X). From FC J3'),
                                     ('J2', 'Qwiic OUT', 'JST SH 1.0 mm 4-pin side entry, TOP side (rev D), rear edge (mouth toward -Y). Optional pass-through (the flow board has its own FC port J4)'))):
    x = 35.56 + 33.02 * k
    sch.part(ref, 'Connector_Generic:Conn_01x04', val, x, 38.1, 0, dict(QW),
             fp='Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal', fields={'Note': nt},
             field_pos={'Reference': (x - 5.08, 30.48), 'Value': (x - 5.08, 46.99), 'just': 'left'})
note('Qwiic pinout (both ports, wired in parallel):\n1 GND\n2 +3.3 V (FC expansion LDO, VEXP)\n3 SDA\n4 SCL\n'
     'Pull-ups on the FC (R15/R16 2.2 k); R3/R4 here DNP.\nStandard 1:1 Qwiic cables.', (12.7, 55.88))
C('C1', '10uF', 109.22, 39.37, '+3V3', 'GND', fp=FP_C0603, fields={'Note': 'Bus input bulk / GNSS start-up inrush (100 mA), 10 V X5R'})
C('C3', '100nF', 121.92, 39.37, '+3V3', 'GND', fields={'Note': 'SAM-M10Q VCC, at pin 17'})
C('C4', '100nF', 134.62, 39.37, '+3V3', 'GND', fields={'Note': 'SAM-M10Q V_IO, at pin 2'})
sch.pwr_flag('GND', (132.08, 60.96))
def flag_label(net, p, n):
    sch._instance('power:PWR_FLAG', '#FLG%02d' % n, 'PWR_FLAG', p[0], p[1], 0)
    sch.label(net, p, 0)
flag_label('+3V3', (104.14, 27.94), 10)
note('Rev B: no LDO. The FC rev E feeds the expansion bus from its own\n3.3 V LDO (U11, VEXP, 300 mA), shared with the flow board.', (93.98, 63.5))

# ================================================================ B. GNSS
block('B - GNSS receiver u-blox SAM-M10Q (antenna module)', (146.05, 10.16), (287.02, 110.49))
sch.part('U1', 'RF_GPS:SAM-M8Q', 'SAM-M10Q-00B', 205.74, 53.34, 0,
         {'17': ('W', '+3V3'), '2': ('W', '+3V3'), '3': 'V_BCKP', '13': 'GPS_TXD', '14': 'GPS_RXD',
          '7': 'PPS', '8': 'SAFEBOOT_N', '18': 'RESET_N', '19': None, '9': 'I2C_SDA', '12': 'I2C_SCL',
          '1': 'GND', '4': 'GND', '5': 'GND', '6': 'GND', '10': 'GND', '11': 'GND', '15': 'GND', '16': 'GND', '20': 'GND'},
         fp='RF_GPS:ublox_SAM-M8Q',
         fields={'Note': 'SAM-M10Q-00B (pin compatible with SAM-M8Q). Top side, axis-aligned (rev D; was 45 deg), antenna to the sky. DDC (I2C) 0x42 on the Qwiic bus'},
         field_pos={'Reference': (220.98, 38.1), 'Value': (220.98, 40.64), 'just': 'left'})
sch.tie('U1', ['17', '2'], '+3V3', sym_at=0)
note('Rev B: the FC reads the GNSS over DDC (I2C, address 0x42) on the Qwiic bus.\n'
     'UART (TXD/RXD) only on test pads TP4/TP5: u-center / firmware update with a USB-UART.\n'
     'EXTINT not used. RESET_N: no capacitor (u-blox).\n'
     'TIMEPULSE shares the pin with the SAFEBOOT strap: only a MOSFET gate on it.', (149.86, 83.82))
# backup supply
R('R1', '1k', 158.75, 25.4, '+3V3', ('W', 'BCKP_R'), side='left', fields={'Note': 'Limits the supercap charge current'})
sch.part('D1', 'Device:D_Schottky', 'RB521S30', 158.75, 33.02, 90, {'2': ('W', 'BCKP_R'), '1': 'V_BCKP'},
         fp='Diode_SMD:D_SOD-523', fields={'Note': 'Blocks the supercap from feeding the 3.3 V rail when off'},
         field_pos={'Reference': (161.29, 31.75), 'Value': (161.29, 34.29), 'just': 'left'})
C('C5', '11mF', 158.75, 48.26, 'V_BCKP', 'GND', fp='Capacitor_SMD:C_1210_3225Metric', pol=True, side='left',
  fields={'Note': 'Seiko CPH3225A 3.3 V EDLC: about 10 min of hardware backup (32 uA) for a hot start after a battery swap'})
flag_label('V_BCKP', (172.72, 43.18), 11)
# test points
for k, (tp, net, nt) in enumerate([('TP1', 'SAFEBOOT_N', 'SAFEBOOT_N: short to TP3 at power-up for firmware recovery'),
                                   ('TP2', 'RESET_N', 'RESET_N, active low'), ('TP3', 'GND', 'GND'),
                                   ('TP4', 'GPS_TXD', 'GNSS UART TXD (output, 3.3 V)'), ('TP5', 'GPS_RXD', 'GNSS UART RXD (input, 3.3 V)')]):
    x = 218.44 + 13.97 * k
    sch.part(tp, 'Connector:TestPoint', net, x, 27.94, 0, {'1': net}, fp='TestPoint:TestPoint_Pad_D1.0mm',
             fields={'Note': nt}, stub=2.54,
             field_pos={'Reference': (x + 1.27, 21.59), 'Value': (x + 1.27, 19.05), 'just': 'left'})

# ================================================================ C. COMPASS
block('C - Compass IIS2MDC on the Qwiic bus (address 0x1E)', (10.16, 82.55), (142.24, 160.02))
sch.part('U3', 'Sensor_Magnetic:LIS2MDL', 'IIS2MDC', 60.96, 119.38, 0,
         {'1': 'I2C_SCL', '3': '+3V3', '4': 'I2C_SDA', '5': 'MAG_C1', '6': 'GND', '7': None,
          '9': ('W', '+3V3'), '10': ('W', '+3V3')},
         fp='Package_LGA:LGA-12_2x2mm_P0.5mm',
         fields={'Note': 'IIS2MDCTR, bottom side, axes aligned with the FC axes. CS high = I2C. DRDY not used (polled)'},
         field_pos={'Reference': (66.04, 104.14), 'Value': (66.04, 134.62), 'just': 'left'})
sch.tie('U3', ['9', '10'], '+3V3', sym_at=0)
C('C6', '220nF', 88.9, 132.08, 'MAG_C1', 'GND', fields={'Note': 'IIS2MDC C1: 220 nF, ESR < 200 mOhm, close to pins 5-6'})
C('C7', '100nF', 101.6, 132.08, '+3V3', 'GND', fields={'Note': 'IIS2MDC Vdd'})
R('R3', '4.7k', 22.86, 101.6, '+3V3', 'I2C_SCL', side='left', dnp=True,
  fields={'Note': 'DNP: pull-ups are on the FC (R15/R16). Fit only for a host without pull-ups'})
R('R4', '4.7k', 33.02, 101.6, '+3V3', 'I2C_SDA', dnp=True)
note('The FC on-board IIS2MDC sits on the LSM6DSV16X sensor-hub bus;\n'
     'this one is on the Qwiic bus (FC I2C1): GNSS 0x42, ToF 0x29, flow bridge 0x3B: no address clash.\n'
     'Keep it 5 mm or more from the supercap, the LDO and the cable.', (12.7, 147.32))

# ================================================================ D. PPS LED + MOUNTING
block('D - PPS indicator, mounting', (146.05, 114.3), (287.02, 160.02))
R('R2', '220R', 167.64, 127.0, '+3V3', ('W', 'LED_A'), side='left')
sch.part('D2', 'Device:LED', 'green', 167.64, 134.62, 90, {'2': ('W', 'LED_A'), '1': ('W', 'LED_K')},
         fp='LED_SMD:LED_0402_1005Metric', fields={'Note': 'PPS LED, top side: blinks once per second with a 3D fix'},
         field_pos={'Reference': (170.18, 133.35), 'Value': (170.18, 135.89), 'just': 'left'})
sch.part('Q1', 'Transistor_FET:2N7002', '2N7002', 165.1, 143.51, 0, {'3': ('W', 'LED_K'), '1': 'PPS', '2': 'GND'},
         fp='Package_TO_SOT_SMD:SOT-23',
         fields={'Note': 'Gate only on TIMEPULSE (no pull-down: it would pull the SAFEBOOT strap low)'},
         field_pos={'Reference': (171.45, 143.51), 'Value': (171.45, 146.05), 'just': 'left'})
for k in range(4):
    x = 213.36 + 10.16 * k
    sch.part('H%d' % (k + 1), 'Mechanical:MountingHole', 'M2', x, 132.08, 0, {},
             fp='MountingHole:MountingHole_2.2mm_M2',
             fields={'Note': 'M2 hole, 20 x 20 pattern (same as the FC rev F). Nylon standoff to the FC stack'},
             field_pos={'Reference': (x, 125.73), 'Value': (x, 128.27)}, in_bom=False)
note('Stack: FC on its grommets, M2 nylon standoffs (6 mm), GNSS board on top.\nKeep-out r 2.6 mm around each hole on both sides.', (205.74, 143.51))

sch.write(OUT)
json.dump({'%s.%s' % k: v for k, v in sch.expected.items()}, open(OUT + '.expected.json', 'w'), indent=0)
json.dump(sorted('%s.%s' % k for k in sch.nc), open(OUT + '.nc.json', 'w'))
parts = {}
for ref, P in sch.parts.items():
    parts[ref] = dict(lib_id=P['lib_id'], value=P['value'], fp=P['fp'], fields=P['fields'], dnp=P['dnp'])
json.dump(parts, open(OUT + '.parts.json', 'w'), indent=1)
print('ok', len(sch.parts), 'parts')
