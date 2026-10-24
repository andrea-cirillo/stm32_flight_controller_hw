# Generates DimaQuadFC.kicad_sch (KiCad 7 format) for the DimaMiniQuad flight controller.
import sys, json
import kisch
from kisch import Schematic, POWER_LIB, vec, g
from custom_syms import all_symbols, LIB

OUT = sys.argv[1] if len(sys.argv) > 1 else 'DimaQuadFC.kicad_sch'
PROJECT = 'ACwing_FC_A'

POWER_LIB.update({'GND': 'power:GND', 'VDD': 'power:VDD', 'VBUS': 'power:VBUS',
                  'VBAT': LIB + ':VBAT', 'VREG': LIB + ':VREG', 'VSYS': LIB + ':VSYS'})

sch = Schematic(PROJECT, 'A3', title=dict(
    title='ACwing FC rev A - 1S-6S flight controller (STM32WB55CGU6), 4-in-1 ESC links, up to 8 motors',
    date='2026-10-18', rev='H',
    company='UAV Control - A. Cirillo',
    comments=['Outline: frame C (40 x 40, as rev E); holes 20 x 20 (mechanical handoff, update 2026-10-18)',
              'Power and motors from a 4-in-1 ESC (JST SH 8-pin ESC A J2, ESC B J6) or the DimaQuad 1S power board',
              'Pin map: ACwing_FC_A_pinmap.md',
              'Generated automatically: run ERC before release']))

for name, node in all_symbols().items():
    sch.add_lib(LIB + ':' + name, node)

# ---------------------------------------------------------------- helpers
FP_R = 'Resistor_SMD:R_0402_1005Metric'
FP_C = 'Capacitor_SMD:C_0402_1005Metric'
FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
FP_C1206 = 'Capacitor_SMD:C_1206_3216Metric'
FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'
FP_LED = 'LED_SMD:LED_0402_1005Metric'

def R(ref, val, x, y, a, b, rot=0, fp=FP_R, side='right', **kw):
    """Vertical (rot 0: pin1 top) or horizontal (rot 90: pin1 left) resistor."""
    fpos = _fpos(x, y, rot, side)
    return sch.part(ref, 'Device:R', val, x, y, rot, {'1': a, '2': b}, fp=fp, field_pos=fpos, **kw)

def C(ref, val, x, y, a='VDD', b='GND', rot=0, fp=FP_C, pol=False, side='right', **kw):
    fpos = _fpos(x, y, rot, side)
    return sch.part(ref, 'Device:C_Polarized' if pol else 'Device:C', val, x, y, rot, {'1': a, '2': b},
                    fp=fp, field_pos=fpos, **kw)

def _fpos(x, y, rot, side='right'):
    if rot in (0, 180):
        if side == 'left':
            return {'Reference': (x - 2.54, y - 1.27), 'Value': (x - 2.54, y + 1.27), 'just': 'right'}
        return {'Reference': (x + 2.54, y - 1.27), 'Value': (x + 2.54, y + 1.27), 'just': 'left'}
    return {'Reference': (x, y - 2.54), 'Value': (x, y + 3.81)}

def block(title, a, b):
    sch.rect(a, b)
    sch.text(title, (a[0] + 1.27, a[1] + 1.27), size=2.0, bold=True)

def note(s, p, size=1.27):
    sch.text(s, p, size=size)

# ================================================================ A. POWER
block('A - Input buck U12 (1S-6S -> VREG 4.1 V), USB/battery power path, LDO', (12, 12), (178, 118))
Y0 = 35.56

def node(net, p, j=True):
    sch.power(net, p, 90 if net != 'GND' else 270)
    if j:
        sch.junction(p)

def divider(ra, rb, va, vb, x, y, top, mid, bot, cref=None, cval='100nF', note_=None, label_dx=7.62):
    """Vertical divider: ra top (pin1 at y), rb directly below; mid node wired to the right with a label."""
    R(ra, va, x, y + 3.81, top, ('W', mid))
    R(rb, vb, x, y + 11.43, ('W', mid), bot)
    m = (x, y + 7.62)
    sch.junction(m)
    sch.wire(m, (x + label_dx, m[1]))
    sch.label(mid, (x + label_dx, m[1]), 0)
    if cref:
        cx = x + 10.16
        C(cref, cval, cx, m[1] + 3.81, ('W', mid), 'GND')
        sch.junction((cx, m[1]))

# VREG: output of the input buck U12 (lower part of this block): 4.1 V from 2S-6S, about VBAT on 1S (100% duty cycle)
sch.wire((25.4, Y0), (55.88, Y0))
sch.label('VREG', (25.4, Y0), 180)
node('VREG', (35.56, Y0))
C('C6', '100uF 6.3V', 45.72, Y0 + 3.81, ('W', 'VREG'), 'GND', fp=FP_C1206,
  fields={'Note': 'Buck output (LM5166 PFM, ILIM 1.25 A: COUT >= 50 L Ipk^2 / VOUT^2 ~ 100 uF), with C46'})
sch.junction((45.72, Y0))

# power path: battery through P-MOSFET (body diode toward VSYS), USB through Schottky
sch.part('Q5', 'Transistor_FET:AO3401A', 'AO3401A', 60.96, Y0 + 2.54, 90,
         {'3': ('W', 'VREG'), '2': ('W', 'VSYS'), '1': ('W', 'VBUS')},
         fields={'Note': 'Load sharing: ON on battery only, OFF with USB (gate = VBUS)'},
         field_pos={'Reference': (58.42, Y0 - 6.35), 'Value': (58.42, Y0 - 3.81)})
gq = sch.pin_end('Q5', '1')[0]                      # (60.96, Y0+7.62)
yb = gq[1] + 5.08
sch.wire(gq, (gq[0], yb))
sch.junction((gq[0], yb))
R('R2', '100k', gq[0], yb + 3.81, ('W', 'VBUS'), 'GND', fields={'Note': 'Gate pull-down: Q5 on when VBUS is absent'})
sch.wire((66.04, Y0), (109.22, Y0))
node('VSYS', (71.12, Y0))
sch.part('D9', 'Device:D_Schottky', 'PMEG2010AEH', 76.2, Y0 + 3.81, 270,
         {'1': ('W', 'VSYS'), '2': ('W', 'VBUS')}, fp='Diode_SMD:D_SOD-123F',
         fields={'Note': 'VBUS -> VSYS, 1 A, Vf ~0.35 V'},
         field_pos={'Reference': (78.74, Y0 + 2.54), 'Value': (78.74, Y0 + 5.08), 'just': 'left'})
sch.junction((76.2, Y0))
sch.wire((76.2, Y0 + 7.62), (76.2, yb))
sch.wire((gq[0], yb), (83.82, yb))
sch.junction((76.2, yb))
sch.power('VBUS', (83.82, yb), 0)
C('C7', '4.7uF', 93.98, Y0 + 3.81, ('W', 'VSYS'), 'GND', fp=FP_C0603)
sch.junction((93.98, Y0))

# LDO LD39130S adjustable (DFN6): VOUT = 0.8 V * (1 + R3/R4)
sch.part('U5', LIB + ':LD39130S-ADJ', 'LD39130SPUR', 119.38, Y0 + 2.54, 0,
         {'4': ('W', 'VSYS'), '3': ('W', 'VSYS'), '1': ('W', 'VSYS'), '6': ('W', 'VDD'),
          '5': ('W', 'LDO_ADJ'), '2': 'GND'},
         fp='Package_DFN_QFN:DFN-6_1.3x1.2mm_P0.4mm',
         fields={'Note': 'BoM: LD39130S 3.0 V. The fixed 3.0 V part exists only as a 0.69 mm flip chip (LD39130SJ30R): '
                         'ADJ version in DFN6 used here, set to 3.1 V to keep VDDUSB >= 3.0 V'},
         field_pos={'Reference': (111.76, Y0 - 3.81), 'Value': (124.46, Y0 + 11.43), 'just': 'left'})
en = sch.pin_end('U5', '3')[0]; gm = sch.pin_end('U5', '1')[0]
sch.wire(en, (106.68, en[1])); sch.wire(gm, (106.68, gm[1]), (106.68, Y0))
sch.junction((106.68, Y0)); sch.junction((106.68, en[1]))
out_ = sch.pin_end('U5', '6')[0]; adj = sch.pin_end('U5', '5')[0]
sch.wire(out_, (152.4, Y0))
node('VDD', (134.62, Y0))
R('R3', '287k 1%', 139.7, Y0 + 3.81, ('W', 'VDD'), ('W', 'LDO_ADJ'))
R('R4', '100k 1%', 139.7, Y0 + 11.43, ('W', 'LDO_ADJ'), 'GND')
sch.junction((139.7, Y0))
sch.wire(adj, (132.08, adj[1]), (132.08, Y0 + 7.62), (139.7, Y0 + 7.62))
sch.junction((139.7, Y0 + 7.62))
C('C8', '1uF', 149.86, Y0 + 3.81, ('W', 'VDD'), 'GND')
sch.junction((149.86, Y0))
note('VOUT = 0.8 V x (1 + R3/R4) = 3.10 V\nGM high: green mode off\nEN = VSYS: always on', (109.22, 54.61))

sch.pwr_flag('VBUS', (154.94, 58.42)); sch.pwr_flag('VSYS', (165.1, 58.42)); sch.pwr_flag('GND', (172.72, 50.8))
note('VREG: buck U12 output (below).\nQ5 off with USB: USB never back-feeds\nVREG, the buck or the battery', (15.24, 48.26))

# Input buck U12: LM5166 (3-65 V in, 500 mA, PFET high side -> 100% duty cycle on 1S), PFM mode, adjustable
sch.text('Input buck 1S-6S (LM5166, VREG 4.1 V)', (15.24, 66.04), size=1.5, bold=True)
sch.part('U12', LIB + ':LM5166', 'LM5166DRCT', 50.8, 86.36, 0,
         {'2': 'VBAT', '7': 'VBAT', '9': None, '4': None, '5': 'GND', '1': ('W', 'BUCK_SW'), '8': ('W', 'BUCK_FB'),
          '6': None, '3': 'GND', '10': 'GND', '11': 'GND'},
         fp='Package_SON:Texas_DRC0010J',
         fields={'Note': 'TI LM5166DRCT: VIN 3-65 V (abs max 68 V), UVLO 2.75 V rising / 2.45 V falling, 500 mA. RT = GND: PFM; ILIM = GND: 1.25 A peak; '
                         'EN = VIN: always on; SS open: 0.9 ms; HYS, PGOOD not used. 1S: 100% duty cycle, VREG = VBAT - I x (0.93 ohm + DCR)'},
         field_pos={'Reference': (40.64, 74.93), 'Value': (50.8, 74.93), 'just': 'left'})
sw = sch.pin_end('U12', '1')[0]
sch.part('L3', 'Device:L', '22uH', sw[0] + 8.89, sw[1], 90, {'1': ('W', 'BUCK_SW'), '2': ('W', 'VREG')},
         fp='Inductor_SMD:L_Sunlord_SWPA5040S',
         fields={'Note': 'Sunlord SWPA5040S220MT, 22 uH, Isat 1.9 A, 168 mOhm, 5 x 5 x 4 mm (PFM: L >= (VIN - VOUT) x 260 ns / 0.35 A at 25 V)'},
         field_pos={'Reference': (sw[0] + 8.89, sw[1] - 3.81), 'Value': (sw[0] + 8.89, sw[1] + 3.81)})
sch.wire(sw, sch.pin_end('L3', '1')[0])
sch.label('BUCK_SW', (sw[0] + 2.54, sw[1]), 0)
lo = sch.pin_end('L3', '2')[0]
sch.wire(lo, (lo[0] + 27.94, lo[1]))
sch.label('VREG', (lo[0] + 27.94, lo[1]), 0)
C('C46', '22uF 25V', lo[0] + 20.32, lo[1] + 3.81, ('W', 'VREG'), 'GND', fp='Capacitor_SMD:C_0805_2012Metric',
  fields={'Note': 'Buck output, X5R 0805, next to L3 / U12 (with C6)'})
sch.junction((lo[0] + 20.32, lo[1]))
fb = sch.pin_end('U12', '8')[0]
R('R47', '470k 1%', lo[0] + 5.08, fb[1] - 3.81, ('W', 'VREG'), ('W', 'BUCK_FB'), fields={'Note': 'VREG = 1.223 V x (1 + 470k/200k) = 4.10 V'})
R('R48', '200k 1%', lo[0] + 5.08, fb[1] + 3.81, ('W', 'BUCK_FB'), 'GND')
sch.wire(fb, (lo[0] + 5.08, fb[1])); sch.junction((lo[0] + 5.08, fb[1]))
sch.label('BUCK_FB', (fb[0] + 2.54, fb[1]), 0)
sch.wire((lo[0] + 5.08, lo[1]), (lo[0] + 5.08, fb[1] - 7.62)); sch.junction((lo[0] + 5.08, lo[1]))
C('C47', '4.7uF 50V', 20.32, 90.17, 'VBAT', 'GND', fp=FP_C1206, side='left',
  fields={'Note': 'Buck input, X7R 50 V 1206, at the VIN / GND pins (6S: 25.2 V)'})
C('C49', '10nF', 30.48, 90.17, 'VBAT', 'GND', side='left', fields={'Note': 'Buck input HF bypass, X7R 50 V, closest to VIN'})
note('VBAT 1S-6S (3.0-25.2 V), from ESC A J2\nor the battery pads J7/J8.\nVREG 4.1 V (2S-6S), VBAT - drop (1S).\nLoad on VREG <= 0.5 A', (66.04, 100.33))

# Sense: battery voltage and USB presence
sch.text('Sensing', (124.46, 66.04), size=1.5, bold=True)
divider('R8', 'R9', '100k 1%', '10k', 127.0, 76.2, 'VBAT', 'VBAT_SNS', 'GND', cref='C12', label_dx=15.24)
divider('R10', 'R11', '100k', '100k', 154.94, 76.2, 'VBUS', 'VBUS_DET', 'GND', label_dx=5.08)
note('VBAT_SNS = VBAT x 10/110 (ADC PA5, IN10):\n25.2 V (6S) -> 2.29 V, full scale 34 V\nVBUS_DET = VBUS/2 (GPIO PB1):\nmotors inhibited with USB plugged in', (124.46, 101.6))

# ================================================================ B. USB-C
block('B - USB-C (DFU/CDC, bench supply; no charger), ESD protection', (12, 122), (178, 188))
sch.part('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C (HRO TYPE-C-31-M-12)', 30.48, 152.4, 0,
         {'A4': 'VBUS', 'A5': 'USB_CC1', 'B5': 'USB_CC2', 'A6': 'USB_DP', 'B6': 'USB_DP',
          'A7': 'USB_DM', 'B7': 'USB_DM', 'A8': None, 'B8': None, 'A1': 'GND', 'S1': 'GND'},
         fp='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
         fields={'Note': 'Right-corner chamfer, plug from the frame side'},
         field_pos={'Reference': (20.32, 129.54), 'Value': (20.32, 132.08), 'just': 'left'})
R('R12', '5.1k', 63.5, 154.94, 'USB_CC1', 'GND')
R('R13', '5.1k', 76.2, 154.94, 'USB_CC2', 'GND')
sch.part('U7', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6', 101.6, 152.4, 0,
         {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DM', '4': 'USB_DM', '5': 'VBUS', '2': 'GND'},
         field_pos={'Reference': (106.68, 144.78), 'Value': (106.68, 162.56), 'just': 'left'})
note('CC1/CC2 5.1k: USB 2.0 sink\n(5 V, 500 mA / 1.5 A with Type-C chargers)\n'
     'D+/D- straight to PA12/PA11,\nUSBLC6 close to the connector\n'
     'Shield tied directly to GND\n(no metal frame)', (119.38, 140.97))

# ================================================================ C. MCU (rev C2: STM32WB55CGU6 QFN48 + RF front end)
block('C - STM32WB55CGU6 (QFN48), RF front end, clocks', (182, 12), (282, 188))
MX, MY = 240.03, 86.36
mcu = {
    '1': ('W', 'VDD'), '8': ('W', 'VDD'), '20': ('W', 'VDD'), '23': ('W', 'VDD'), '34': ('W', 'VDD'),
    '35': ('W', 'VDD'), '40': ('W', 'VDD'), '48': ('W', 'VDD'),
    '22': ('W', 'GND'), '32': ('W', 'GND'), '49': ('W', 'GND'),
    '21': 'RF_IN',                                     # RF1 -> MLPF-WB55 IN (62 ohm line)
    '24': 'HSE_OUT', '25': 'HSE_IN',                   # 32 MHz crystal, internal trimming caps
    '33': 'SMPS_LX', '31': 'VFBSMPS',                  # SMPS network (bypass at reset)
    '4': 'BOOT0', '7': 'NRST',
    # rev F pin map (ACwing_FC_A_pinmap.md): the MCU sits at the board centre, no pin row faces an edge.
    # All four motor outputs on TIM2 CH1-CH4 (one DMA burst: PWM for brushed, DShot / bidirectional DShot for brushless)
    '9': 'PWM_M1', '10': 'PWM_M2', '11': 'PWM_M3', '12': 'PWM_M4',   # PA0-PA3 TIM2_CH1-CH4
    '13': 'ESC_CUR',                                   # PA4 ADC1_IN9: current from the ESC link (0.1 V/A on DimaQuadESC)
    '14': 'VBAT_SNS',                                  # PA5 ADC1_IN10: VBAT/2
    '29': 'VBUS_DET',                                  # PB1 GPIO: VBUS/2 reads high with USB plugged in
    '43': 'SPI_SCK', '44': 'SPI_MISO', '45': 'SPI_MOSI',   # PB3/PB4/PB5 SPI1: IMU + log flash
    '2': 'IMU_CS', '30': 'FLASH_CS',                   # PC14 (east side, next to the IMU; GPIO, 2 MHz is plenty for a CS), PE4
    '17': 'PWM_M5', '18': 'PWM_M6', '36': 'PWM_M7',    # PA8/PA9/PA10 TIM1_CH1-CH3 (DMA): motors M5-M7 -> ESC link B J6 (rev H)
    '15': 'PWM_M8',                                    # PA6 TIM16_CH1 (DMA): motor M8 -> J6 (rev H)
    '16': 'RGB_DIN',                                   # PA7 TIM17_CH1 (DMA): 4 x WS2812B (rev H, was PB6)
    '46': 'CRSF_TX', '47': 'CRSF_RX',                  # PB6/PB7 USART1 (alternate pins) -> ELRS receiver J5 (rev H, was PA9/PA10)
    '28': 'ESC_TLM_MCU',                               # PB0 GPIO/EXTI: ESC A serial telemetry, optional (rev H, was PB7)
    '5': 'I2C_SCL', '6': 'I2C_SDA',                    # PB8/PB9 I2C1: expansion bus (Qwiic J3) only
    '37': 'USB_DM', '38': 'USB_DP',                    # PA11/PA12 USB FS
    '39': 'SWDIO', '41': 'SWCLK',                      # PA13/PA14
    '42': 'IMU_INT1',                                  # PA15
    '3': None, '19': None,                             # PC15 (no LSE), PB2 free
}
sch.part('U2', 'MCU_ST_STM32WB:STM32WB55CGUx', 'STM32WB55CGU6', MX, MY, 0, mcu,
         fp='Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm',
         fields={'Note': 'Top side, board centre. Exposed pad to GND with a via array (RF ground); RF line to the chip antenna at the left edge'},
         field_pos={'Reference': (MX + 22.86, MY - 43.18), 'Value': (MX + 22.86, MY + 41.91)})
sch.tie('U2', ['1', '20', '35', '48', '8', '23', '34', '40'], 'VDD')
sch.tie('U2', ['22', '49', '32'], 'GND', sym_at=1)
note('Pin map (IEKF firmware), rev H:\n'
     'Motors M1-M4 PA0-PA3 TIM2_CH1-CH4 -> ESC A J2; M5-M7 PA8-PA10 TIM1_CH1-CH3, M8 PA6 TIM16_CH1 -> ESC B J6\n'
     '(PWM 32 kHz brushed / DShot, bidirectional DShot: every motor timer has DMA)\n'
     'ADC: PA4 ESC_CUR (IN9), PA5 VBAT_SNS (IN10, x10/110); ESC A serial telemetry PB0 (optional)\n'
     'SPI1 PB3 SCK / PB4 MISO / PB5 MOSI: IMU (CS PC14) + log flash (CS PE4), IMU_INT1 PA15\n'
     'USART1 PB6 TX / PB7 RX -> ELRS (CRSF 420 kbaud), J5\n'
     'I2C1 PB8/PB9 -> expansion bus (Qwiic J3 + J4: GPS board, flow board, sensors)\n'
     'RGB LEDs PA7 (TIM17_CH1 + DMA, 4 x WS2812B); VBUS_DET PB1; PB2 free\n'
     'No LSE: RF wake-up HSE/1024, RTC HSE/32. USB PA11/PA12 (DFU, CDC)\n'
     'SWD PA13/PA14, BOOT0 = PH3 (pull-down 10k)', (186.69, 17.78))

# decoupling (one 100 nF per supply pin, VDDA 1 uF, VDDRF 100 nF + 100 pF), row under the MCU
DEC = [('C23', '100nF', FP_C, 'VDD pin 20'), ('C24', '100nF', FP_C, 'VDD pin 35'), ('C25', '100nF', FP_C, 'VDD pin 48 / VBAT pin 1'),
       ('C14', '100nF', FP_C, 'VDDA pin 8'), ('C22', '1uF', FP_C, 'VDDA pin 8'),
       ('C26', '100nF', FP_C, 'VDDRF pin 23 (DS: 100 nF // 100 pF)'), ('C27', '100pF', FP_C, 'VDDRF pin 23, C0G'),
       ('C28', '100nF', FP_C, 'VDDUSB pin 40'), ('C9', '4.7uF', FP_C0603, 'VDD bulk')]
for k, (ref, val, fp_, nt) in enumerate(DEC):
    C(ref, val, 187.96 + 11.43 * (k % 2), 48.26 + 17.78 * (k // 2), 'VDD', 'GND', fp=fp_, fields={'Note': nt})
C('C15', '100nF', 199.39, 119.38, 'NRST', 'GND', fields={'Note': 'DS13252: 100 nF on NRST'})
R('R14', '10k', 187.96, 137.16, 'BOOT0', 'GND', fields={'Note': 'Boot from flash; TP3 to VDD for the USB DFU bootloader'})

# SMPS network (DS13252 table 6): VLXSMPS - 10 uH - 10 nH - VFBSMPS, 4.7 uF; works in bypass (reset default) and SMPS mode
sch.part('L1', 'Device:L', '2.2uH', 196.85, 172.72, 90, {'1': 'SMPS_LX', '2': ('W', 'SMPS_L2')},
         fp='Inductor_SMD:L_0805_2012Metric', fields={'Note': 'SMPS inductor, 8 MHz mode (Wurth 74479774222, DS13252 table 6): set the SMPS clock to 8 MHz in firmware'},
         field_pos={'Reference': (196.85, 168.91), 'Value': (196.85, 176.53)})
sch.part('L2', 'Device:L', '10nH', 207.01, 172.72, 90, {'1': ('W', 'SMPS_L2'), '2': 'VFBSMPS'},
         fp='Inductor_SMD:L_0402_1005Metric', fields={'Note': 'Series 10 nH for receiver performance (DS13252 table 6)'},
         field_pos={'Reference': (207.01, 168.91), 'Value': (207.01, 176.53)})
sch.wire(sch.pin_end('L1', '2')[0], sch.pin_end('L2', '1')[0])
C('C29', '4.7uF', 219.71, 176.53, 'VFBSMPS', 'GND', fields={'Note': 'SMPS output (DS13252 table 6)'})

# HSE 32 MHz (internal trimming caps, no external load caps)
sch.part('Y1', 'Device:Crystal_GND24', '32MHz', 240.03, 175.26, 0,
         {'1': 'HSE_IN', '3': 'HSE_OUT', '2': 'GND', '4': 'GND'}, fp='Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm',
         fields={'Note': 'NDK NX2016SA 32 MHz (DS13252 table 5); load caps integrated in the MCU (trimmed in firmware)'},
         field_pos={'Reference': (243.84, 168.91), 'Value': (243.84, 171.45), 'just': 'left'})
# no LSE crystal: BLE RF wake-up clock = HSE/1024, RTC = HSE/32 (pins 2/3 PC14/PC15 not connected)

# RF: RF1 -> MLPF-WB55-01E3 -> pi network (tuning) -> chip antenna
sch.part('U8', LIB + ':MLPF-WB55-01E3', 'MLPF-WB55-01E3', 207.01, 152.4, 0, {'A3': 'RF_IN', 'A1': ('W', 'RF_ANT'), 'B2': 'GND'},
         fields={'Note': 'Directly at RF1: 62 ohm line from the MCU, 50 ohm to the antenna'},
         field_pos={'Reference': (205.74, 147.32), 'Value': (203.2, 160.02), 'just': 'right'})
ra = sch.pin_end('U8', 'A1')[0]
sch.wire(ra, (ra[0] + 10.16, ra[1]))
R('R34', '0R', ra[0] + 13.97, ra[1], ('W', 'RF_ANT'), ('W', 'RF_ANT2'), rot=90, fields={'Note': 'Antenna tuning: series position, 0 ohm until tuned'})
rb = sch.pin_end('R34', '2')[0]
sch.wire(rb, (rb[0] + 10.16, rb[1]))
C('C36', 'DNP', rb[0] + 5.08, rb[1] + 3.81, ('W', 'RF_ANT2'), 'GND', dnp=True, side='left', fields={'Note': 'Antenna tuning: shunt position at the antenna side (C0G or inductor), DNP until tuned'})
sch.junction((rb[0] + 5.08, rb[1]))
sch.part('AE1', 'Device:Antenna_Chip', '2450AT18A0100001E', rb[0] + 12.7, rb[1] - 2.54, 0, {'1': ('W', 'RF_ANT2'), '2': None},
         fp='RF_Antenna:Johanson_2450AT18x100',
         fields={'Note': 'Johanson 2.4 GHz chip antenna at the left board edge; pad 2 NC; copper-free area around it'},
         field_pos={'Reference': (rb[0] + 15.24, rb[1] - 8.89), 'Value': (rb[0] + 15.24, rb[1] - 6.35), 'just': 'left'})
sch.wire(sch.pin_end('AE1', '1')[0], (rb[0] + 10.16, rb[1]))


# ================================================================ D. SENSORS
block('D - Sensors: LSM6DSV16X (SPI1) + sensor hub -> IIS2MDC, LPS22HB; log flash', (286, 12), (408, 150))
sch.part('U1', LIB + ':LSM6DSV16X', 'LSM6DSV16X', 335.28, 50.8, 0,
         {'1': 'SPI_MISO', '2': 'SHUB_SDA', '3': 'SHUB_SCL', '4': 'IMU_INT1', '5': ('W', 'VDD'), '6': 'GND',
          '8': ('W', 'VDD'), '9': None, '10': None, '11': None, '12': 'IMU_CS', '13': 'SPI_SCK', '14': 'SPI_MOSI'},
         fields={'Note': 'Board centre (frame CG), axes 45 deg to the airframe. Rev E: 4-wire SPI (mode 3, <= 10 MHz) on SPI1 with the log flash; sensor hub (SDx/SCx) unchanged'},
         field_pos={'Reference': (340.36, 33.02), 'Value': (340.36, 68.58), 'just': 'left'})
sch.tie('U1', ['5', '8'], 'VDD', sym_at=0)
C('C16', '100nF', 360.68, 30.48, 'VDD', 'GND', fields={'Note': 'Vdd (pin 8)'})
C('C17', '100nF', 370.84, 30.48, 'VDD', 'GND', fields={'Note': 'Vdd_IO (pin 5)'})
R('R15', '2.2k', 297.18, 25.4, 'VEXP', 'I2C_SCL', fields={'Note': 'Expansion bus (I2C1) pull-up to the Qwiic 3.3 V rail; add-on boards have their pull-ups DNP'})
R('R16', '2.2k', 309.88, 25.4, 'VEXP', 'I2C_SDA')
R('R38', '10k', 322.58, 25.4, 'VDD', 'IMU_CS', fields={'Note': 'IMU CS pull-up: deselected during boot'})
R('R17', '4.7k', 381, 25.4, 'VDD', 'SHUB_SCL', fields={'Note': 'Sensor hub bus pull-up (or the internal SHUB_PU_EN)'})
R('R18', '4.7k', 393.7, 25.4, 'VDD', 'SHUB_SDA')

sch.part('U3', 'Sensor_Magnetic:LIS2MDL', 'IIS2MDC', 327.66, 109.22, 0,
         {'1': 'SHUB_SCL', '3': 'VDD', '4': 'SHUB_SDA', '5': 'MAG_C1', '6': 'GND', '7': None,
          '9': ('W', 'VDD'), '10': ('W', 'VDD')},
         fields={'Note': 'IIS2MDCTR (industrial grade of the LIS2MDL: same LGA-12 pinout and registers). Front corner, farthest from battery and motor currents. No motor current under it'},
         field_pos={'Reference': (332.74, 93.98), 'Value': (332.74, 124.46), 'just': 'left'})
sch.tie('U3', ['9', '10'], 'VDD', sym_at=0)
C('C18', '220nF', 350.52, 121.92, 'MAG_C1', 'GND', fields={'Note': 'IIS2MDC C1: 220 nF, ESR < 200 mOhm, close to pins 5-6'})
C('C19', '100nF', 297.18, 88.9, 'VDD', 'GND')
C('C20', '10uF 6.3V', 309.88, 88.9, 'VDD', 'GND', fp=FP_C0603, fields={'Note': 'IIS2MDC DS: 100 nF + 10 uF on Vdd'})

sch.part('U4', 'Sensor_Pressure:LPS22DF', 'LPS22HB', 377.19, 109.22, 0,
         {'1': ('W', 'VDD'), '10': ('W', 'VDD'), '2': 'SHUB_SCL', '4': 'SHUB_SDA', '5': 'VDD', '6': 'VDD',
          '7': None, '8': ('W', 'GND'), '9': ('W', 'GND')},
         fields={'Note': 'LPS22HBTR on the LPS22DF symbol/footprint (same HLGA-10 pinout, pin 3 to GND). Optional. SA0 = 1 -> 0x5D'},
         stub=7.62,
         field_pos={'Reference': (382.27, 93.98), 'Value': (382.27, 124.46), 'just': 'left'})
sch.tie('U4', ['1', '10'], 'VDD', sym_at=1)
sch.tie('U4', ['8', '9'], 'GND', sym_at=1)
C('C21', '100nF', 355.6, 88.9, 'VDD', 'GND')
note('Topology = IKS4A1 Mode 3: the IEKF firmware\n'
     'reads the IIS2MDC through the LSM6DSV16X\n'
     'sensor hub (samples aligned in the FIFO).\n'
     'Rev E: the IMU host interface is SPI; DRDY/INT2/baro INT not used (FIFO + timestamps)\n'
     'Addresses on the hub bus: IIS2MDC 0x1E, LPS22HB 0x5D', (289.56, 134.62))

# log flash on SPI1 (rev E)
sch.part('U10', 'Memory_Flash:W25Q32JVSS', 'W25Q128JV', 388.62, 66.04, 0,
         {'1': 'FLASH_CS', '2': 'SPI_MISO', '3': 'VDD', '4': 'GND', '5': 'SPI_MOSI', '6': 'SPI_SCK', '7': 'VDD', '8': 'VDD'},
         fp='Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4mm',
         fields={'Note': 'Winbond W25Q128JVPIQ, 16 MB SPI NOR (WSON-8 6x5, bottom side): flight logs (blackbox). /WP and /HOLD tied high'},
         field_pos={'Reference': (396.24, 53.34), 'Value': (396.24, 55.88), 'just': 'left'})
C('C39', '100nF', 373.38, 66.04, 'VDD', 'GND', side='left', fields={'Note': 'Flash VCC'})
R('R37', '10k', 373.38, 50.8, 'VDD', 'FLASH_CS', side='left', fields={'Note': 'Flash CS pull-up: deselected during boot'})

# ================================================================ E. ESC LINK (rev F)
block('', (12, 192), (148, 285))
sch.text('E - ESC link: JST SH 8-pin, common 4-in-1 ESC pinout', (13.27, 193.27), size=2.0, bold=True)
EY = 213.36
sch.part('J2', 'Connector_Generic:Conn_01x08', 'ESC link', 40.64, EY, 0,
         {'1': ('W', 'GND'), '2': ('W', 'VBAT'), '3': ('W', 'ESC_CUR_IN'), '4': ('W', 'ESC_TLM'),
          '5': ('W', 'ESC_M1'), '6': ('W', 'ESC_M2'), '7': ('W', 'ESC_M3'), '8': ('W', 'ESC_M4')},
         fp='Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal', mirror=True,
         fields={'Note': 'ESC link A, JST SH 8-pin side entry, top side, rear edge: 1 GND, 2 VBAT (1S-6S, FC supply), 3 CUR, 4 TLM, 5-8 M1-M4. 1:1 cable. Check the pinout of a third-party ESC'},
         field_pos={'Reference': (36.83, EY + 1.27), 'Value': (36.83, EY + 3.81), 'just': 'right'})
pins = {n: sch.pin_end('J2', n)[0] for n in '12345678'}
# fan-out: the 2.54 mm pin rows open up to 7.62 mm rows (jog x decreases with the pin number: no crossings)
ytop = pins['1'][1]
row = {}
for k, n in enumerate('12345678'):
    p = pins[n]; xj = 48.26 + 2.54 * (7 - k); yt = ytop + 7.62 * k
    pts = [p, (xj, p[1])] + ([(xj, yt)] if abs(yt - p[1]) > 1e-6 else [])
    sch.wire(*pts)
    row[n] = (xj, yt)
sch.wire(row['1'], (71.12, row['1'][1])); sch.power('GND', (71.12, row['1'][1]), 270)
sch.wire(row['2'], (76.2, row['2'][1])); sch.power('VBAT', (76.2, row['2'][1]), 90)
for n in '345678':
    y = row[n][1]
    net = {'3': 'ESC_CUR_IN', '4': 'ESC_TLM'}.get(n, 'ESC_M%d' % (int(n) - 4))
    mcu_net = {'3': 'ESC_CUR', '4': 'ESC_TLM_MCU'}.get(n, 'PWM_M%d' % (int(n) - 4))
    ref = {'3': 'R42', '4': 'R24'}.get(n, 'R%d' % (19 + int(n) - 4))
    sch.wire(row[n], (72.39, y))
    sch.label(net, (66.04, y), 0)
    sch.part(ref, 'Device:R', '1k' if n == '3' else '100R', 76.2, y, 90, {'1': ('W', net), '2': ('W', mcu_net)}, fp=FP_R,
             fields={'Note': {'3': 'ADC input protection: limits the injected current if an ESC drives CUR above 3.3 V; RC with C1',
                              '4': 'Series resistor, ESC serial telemetry input to PB0 (optional; EDT on the motor lines preferred)'}.get(n, 'Series resistor on the cable line (edge rate, ESD, a fault on the ESC side)')},
             field_pos={'Reference': (76.2, y - 2.54), 'Value': (76.2, y + 2.54)})
    sch.wire(sch.pin_end(ref, '2')[0], (88.9, y))
    sch.label(mcu_net, (88.9, y), 0)
C('C1', '100nF', 106.68, 241.3, 'ESC_CUR', 'GND', fields={'Note': 'ADC input cap for ESC_CUR (RC 1k / 100 nF with R42)'})
C('C2', '4.7uF 50V', 121.92, 241.3, 'VBAT', 'GND', fp=FP_C1206, fields={'Note': 'VBAT at the ESC link (up to 6S): local bulk for the cable inductance, X7R 50 V'})
sch.pwr_flag('VBAT', (134.62, 236.22))
note('ESC link A (rev H):\n'
     '- DimaQuad 1S power board (brushed): CUR = 0.1 V/A.\n'
     '- Brushless 4-in-1 ESC, 2S-6S: CUR scale set in firmware\n'
     '  (about 12 mV/A); telemetry via bidirectional DShot / EDT.\n'
     '- VBAT 1S-6S feeds the FC (buck U12, block A).\n'
     '- No charging through the cable (charger on the 1S board).', (12.7, 262.89))

# ================================================================ H. ESC LINK B (M5-M8) AND BATTERY PADS (rev H)
block('H - ESC link B (motors M5-M8), battery pads, second Qwiic port', (152, 221), (282, 285))
HY = 236.22
sch.part('J6', 'Connector_Generic:Conn_01x08', 'ESC link B', 170.18, HY, 0,
         {'1': 'GND', '2': None, '3': None, '4': None,
          '5': 'ESC_M5', '6': 'ESC_M6', '7': 'ESC_M7', '8': 'ESC_M8'},
         fp='Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal', mirror=True,
         fields={'Note': 'ESC link B, JST SH 8-pin side entry, top side, left edge: second 4-in-1 ESC for hexa / octo frames. Same pinout as J2; motors M5-M8 on pins 5-8; VBAT, CUR and TLM not connected (the FC is supplied and measures current through ESC A)'},
         field_pos={'Reference': (166.37, HY - 3.81), 'Value': (166.37, HY - 1.27), 'just': 'right'})
for k in range(4):
    y = HY - 2.54 + 5.08 * k
    ref = 'R%d' % (25 + k)
    sch.part(ref, 'Device:R', '100R', 213.36, y, 90,
             {'1': 'ESC_M%d' % (5 + k), '2': 'PWM_M%d' % (5 + k)}, fp=FP_R,
             fields={'Note': 'Series resistor on the cable line (edge rate, ESD, a fault on the ESC side)'},
             field_pos={'Reference': (213.36, y - 1.9), 'Value': (213.36, y + 1.9)})
for k, (ref, net, nt) in enumerate([('J7', 'VBAT', 'Battery / power input pad VBAT+ (1S-6S), 2 x 2 mm solder pad, top side, left edge. FC supply only, no motor current: '
                                     'use it when the ESC has no VBAT pin (separate ESCs, PDB); otherwise the FC is supplied through ESC A J2'),
                                    ('J8', 'GND', 'Battery / power input pad GND, 2 x 2 mm solder pad, next to J7')]):
    x = 238.76 + 12.7 * k
    sch.part(ref, 'Connector:TestPoint', 'VBAT+' if net == 'VBAT' else 'GND', x, 241.3, 0, {'1': net}, fp='TestPoint:TestPoint_Pad_2.0x2.0mm',
             fields={'Note': nt}, stub=2.54, in_bom=False,
             field_pos={'Reference': (x + 1.27, 236.22), 'Value': (x + 1.27, 233.68), 'just': 'left'})
sch.part('J4', 'Connector_Generic:Conn_01x04', 'Qwiic', 180.34, 271.78, 0,
         {'1': 'GND', '2': 'VEXP', '3': 'I2C_SDA', '4': 'I2C_SCL'},
         fp='Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
         fields={'Note': 'Second Qwiic port, in parallel with J3. Right edge, rear: flow board (under the frame). Each add-on board gets its own cable, no daisy chain needed'},
         field_pos={'Reference': (184.15, 266.7), 'Value': (184.15, 269.24), 'just': 'left'})
note('ESC link B: second 4-in-1 ESC (motors M5-M8).\nPins 2-4 (VBAT, CUR, TLM) open: two ESC supplies\nare never tied together on the FC.\n'
     'Battery pads J7/J8: alternative FC supply input,\nsame VBAT net as J2 pin 2 (one source at a time).\nJ4: second Qwiic port (flow board), parallel to J3.', (213.36, 260.35))

# ================================================================ F. LEDS, PROGRAMMING, HOLES
block('F - RGB LEDs (4 x WS2812B), programming pads, mounting', (286, 154), (408, 250))
# RGB LEDs (front + rear), WS2812B-2020 chained, supplied from VSYS through a Schottky
sch.part('D11', 'Device:D_Schottky', 'RB521S30', 358.14, 162.56, 180, {'2': 'VSYS', '1': ('W', 'VLED')},
         fp='Diode_SMD:D_SOD-523', fields={'Note': 'VLED = VSYS - 0.3 V: the LED data threshold (0.7 VLED) stays below the 3.1 V GPIO level on USB too'},
         field_pos={'Reference': (358.14, 158.75), 'Value': (358.14, 166.37)})
vl = sch.pin_end('D11', '1')[0]
sch.wire(vl, (vl[0] + 7.62, vl[1]))
sch.label('VLED', (vl[0] + 2.54, vl[1]), 0)
sch._instance('power:PWR_FLAG', '#FLG10', 'PWR_FLAG', vl[0] + 7.62, vl[1], 0)   # VLED is driven by D11
R('R39', '33R', 297.18, 203.2, 'RGB_DIN', ('W', 'RGB_D1'), rot=90, fields={'Note': 'Series resistor at the first LED input (data from PA7)'})
LEDS = [('D1', 'rear-right'), ('D2', 'rear-left'), ('D3', 'front-left'), ('D4', 'front-right')]   # chain starts at the rear pair
for k, (ref, where) in enumerate(LEDS):
    x = 312.42 + 22.86 * k
    din = 'RGB_D%d' % (k + 1); dout = ('W', 'RGB_D%d' % (k + 2)) if k < 3 else None
    sch.part(ref, 'LED:WS2812B-2020', 'WS2812B-2020', x, 203.2, 0, {'3': ('W', din), '1': dout, '4': 'VLED', '2': 'GND'},
             fields={'Note': 'RGB LED %d of 4, %s corner (pairs mirrored about the front-rear diagonal). %s' % (k + 1, where,
                     'Rear LED' if k < 2 else 'Front LED, >= 5 mm from the compass; use full on/off colours (PWM ripple near the magnetometer)')},
             field_pos={'Reference': (x - 7.62, 196.85), 'Value': (x - 7.62, 217.17), 'just': 'left'})
    C('C%d' % (40, 41, 42, 45)[k], '100nF', x + 7.62, 184.15, 'VLED', 'GND', fields={'Note': '%s supply' % ref})
for k in range(3):
    sch.wire(sch.pin_end(LEDS[k][0], '1')[0], sch.pin_end(LEDS[k + 1][0], '3')[0])
sch.wire(sch.pin_end('R39', '2')[0], sch.pin_end('D1', '3')[0])
# no buzzer: a magnetic transducer has a permanent magnet (hard iron next to the compasses) and there is no free
# 6 x 6 mm spot on the top side. Beeps (lost model, low battery) are made with the motors (audio-rate PWM, props off
# or at low duty), as on the Crazyflie.
note('No buzzer: beeps through the motors (audio PWM).\nA magnetic buzzer would put a magnet under the compasses.', (290.83, 161.29))

for k, (tp, net, nt) in enumerate([('TP6', 'SWDIO', 'SWDIO (PA13)'), ('TP7', 'SWCLK', 'SWCLK (PA14)'),
                                   ('TP8', 'NRST', 'NRST')]):
    x = 378.46 + 10.16 * k
    sch.part(tp, 'Connector:TestPoint', net, x, 167.64, 0, {'1': net}, fp='TestPoint:TestPoint_Pad_D1.0mm',
             fields={'Note': nt + ' - pogo pad, 2x4 grid at 2.54 mm pitch on the bottom'}, stub=2.54,
             field_pos={'Reference': (x - 1.27, 161.29), 'Value': (x - 1.27, 158.75), 'just': 'left'})
for k, (tp, net, nt) in enumerate([('TP1', 'CRSF_TX', 'USART1 TX (PB6), ELRS port J5 (factory test / monitor)'), ('TP2', 'CRSF_RX', 'USART1 RX (PB7), ELRS port J5 (factory test / monitor)'),
                                   ('TP3', 'BOOT0', 'BOOT0: bridge to TP4 for DFU'),
                                   ('TP4', 'VDD', 'VDD 3.1 V'), ('TP5', 'GND', 'GND')]):
    x = 330.2 + 10.16 * k
    sch.part(tp, 'Connector:TestPoint', net, x, 233.68, 0, {'1': net}, fp='TestPoint:TestPoint_Pad_D1.0mm',
             fields={'Note': nt + ' - pogo pad, 2x4 grid at 2.54 mm pitch on the bottom'}, stub=2.54,
             field_pos={'Reference': (x - 1.27, 227.33), 'Value': (x - 1.27, 224.79), 'just': 'left'})
for k in range(4):
    sch.part('H%d' % (k + 1), 'Mechanical:MountingHole_Pad', 'D3.2', 378.46 + 7.62 * k, 228.6, 0, {'1': 'GND'},
             fp='DimaQuad:Grommet_PTH_3.2mm_Pad5.0mm',
             fields={'Note': 'Plated 3.2 hole for an M2 anti-vibration grommet, 20x20 pattern (rev F). Exposed 5.0 mm copper ring on both sides, GND'},
             field_pos={'Reference': (378.46 + 7.62 * k, 220.98), 'Value': (378.46 + 7.62 * k, 223.52)},
             in_bom=False)
note('Grommet holes 3.2 PTH, 20x20\n(above the ESC / power board)', (375.92, 240.03))

# ================================================================ G. EXPANSION (Qwiic) AND ELRS PORTS (rev E)
block('G - Expansion bus (Qwiic J3, J4) and ELRS port', (186.69, 192), (282, 217.17))
sch.part('J3', 'Connector_Generic:Conn_01x04', 'Qwiic', 201.93, 203.2, 0,
         {'1': 'GND', '2': 'VEXP', '3': 'I2C_SDA', '4': 'I2C_SCL'},
         fp='Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
         fields={'Note': 'Qwiic / STEMMA QT (JST SH 4P): 1 GND, 2 3.3 V, 3 SDA, 4 SCL. Right edge, front: GPS board (stacked above, its J1)'},
         field_pos={'Reference': (205.74, 198.12), 'Value': (205.74, 200.66), 'just': 'left'})
sch.part('U11', 'Regulator_Linear:LDK130-ADJ_DFN6', 'LDK130PU-R', 233.68, 203.2, 0,
         {'6': 'VSYS', '4': 'VSYS', '2': 'GND', '1': ('W', 'VEXP'), '3': ('W', 'VEXP_ADJ'), '5': None},
         fp='Package_DFN_QFN:DFN-6_1.3x1.2mm_P0.4mm',
         fields={'Note': 'Adjustable LDK130 (LCSC C157446, same part as the flow board), 3.3 V 300 mA for the expansion bus only (GPS board up to 100 mA + flow board 35 mA): a short or a hot-plug on a Qwiic cable cannot pull down the MCU rail'},
         field_pos={'Reference': (226.06, 198.12), 'Value': (232.41, 198.12), 'just': 'left'})
oo = sch.pin_end('U11', '1')[0]
sch.wire(oo, (oo[0] + 5.08, oo[1]))
sch.label('VEXP', (oo[0] + 5.08, oo[1]), 0)
bp = sch.pin_end('U11', '3')[0]
R('R41', '15k 1%', bp[0] + 5.08, bp[1] + 3.81, ('W', 'VEXP_ADJ'), 'GND', fields={'Note': 'VEXP divider, bottom'})
R('R40', '47k 1%', bp[0] + 15.24, bp[1] + 3.81, ('W', 'VEXP_ADJ'), 'VEXP',
  fields={'Note': 'VEXP divider, top: VOUT = 0.8 V x (1 + 47k/15k) = 3.31 V'})
sch.wire(bp, (bp[0] + 15.24, bp[1])); sch.junction((bp[0] + 5.08, bp[1]))
C('C43', '1uF', 214.63, 205.74, 'VSYS', 'GND', side='left', fields={'Note': 'U11 input'})
C('C44', '2.2uF', 276.86, 207.01, 'VEXP', 'GND', fields={'Note': 'U11 output / Qwiic'})
sch.part('J5', 'Connector_Generic:Conn_01x04', 'ELRS', 309.88, 226.06, 0,
         {'1': 'GND', '2': 'VSYS', '3': 'CRSF_RX', '4': 'CRSF_TX'},
         fp='Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
         fields={'Note': 'ELRS receiver (CRSF): 1 GND, 2 VSYS (4.1 V), 3 <- RX module TX, 4 -> RX module RX. Not Qwiic: do not plug sensors here'},
         field_pos={'Reference': (313.69, 220.98), 'Value': (313.69, 223.52), 'just': 'left'})
note('J5: ELRS receiver port,\nJST SH 4P', (293.37, 236.22), size=1.0)
note('Qwiic addresses:\nGPS 0x42, compass 0x1E,\nToF 0x29, flow bridge 0x3B', (252.73, 198.12), size=1.0)

sch.write(OUT)
json.dump({'%s.%s' % k: v for k, v in sch.expected.items()}, open(OUT + '.expected.json', 'w'), indent=0)
json.dump(sorted('%s.%s' % k for k in sch.nc), open(OUT + '.nc.json', 'w'))
parts = {}
for ref, P in sch.parts.items():
    parts[ref] = dict(lib_id=P['lib_id'], value=P['value'], fp=P['fp'], fields=P['fields'], dnp=P['dnp'])
json.dump(parts, open(OUT + '.parts.json', 'w'), indent=1)
print('ok', len(sch.parts), 'parts')
