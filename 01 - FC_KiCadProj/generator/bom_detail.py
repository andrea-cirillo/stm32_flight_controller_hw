# Detailed (assembly) BoM for ACwing FC rev A (from rev E): quantity, references, MPN, manufacturer, package, description,
# side, notes. Groups come from the schematic (parts.json); the assembly side comes from the routed PCB.
import sys, json, re, os, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlc_parts import LCSC   # parts as assembled by JLCPCB (equivalents where the original MPN is not stocked)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PARTS, BOARD, OUT = sys.argv[1:4]
parts = json.load(open(PARTS))
side = {f.GetReference(): ('Bottom' if f.IsFlipped() else 'Top') for f in pcbnew.LoadBoard(BOARD).GetFootprints()}

# (value, footprint name) -> (MPN, manufacturer, package, description, notes)
Y = lambda v: 'RC0402FR-07%sL' % v
MPN = {
 ('LM5166DRCT', 'Texas_DRC0010J'): ('LM5166DRCT', 'Texas Instruments', 'VSON-10 (DRC), 3 x 3 mm',
     'Step-down converter, 3-65 V in, 500 mA, 100% duty cycle, PFM', '1S-6S input buck: VREG = 4.1 V (about VBAT on 1S)'),
 ('22uH', 'L_Sunlord_SWPA5040S'): ('SWPA5040S220MT', 'Sunlord', 'SMD 5 x 5 x 4 mm, shielded', 'Inductor, power, 22 uH, Isat 1.9 A, DCR 168 mOhm', 'Input buck inductor (top, left edge, ~41 mm from the magnetometer)'),
 ('4.7uF 50V', 'C_1206_3216Metric'): ('1206B475K500NT', 'FH (Guangdong Fenghua)', '1206 (3216 metric), h 1.6 mm', 'Capacitor, MLCC, 4.7 uF, 50 V, X7R', 'VBAT (up to 6S): buck input (C47), ESC link A (C2)'),
 ('470k 1%', 'R_0402_1005Metric'): (Y('470K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 470 kOhm, 1%, 1/16 W', 'Buck feedback, top'),
 ('200k 1%', 'R_0402_1005Metric'): (Y('200K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 200 kOhm, 1%, 1/16 W', 'Buck feedback, bottom'),
 ('22uF 25V', 'C_0805_2012Metric'): ('CL21A226MAQNNNE', 'Samsung Electro-Mechanics', '0805 (2012 metric), h 1.25 mm', 'Capacitor, MLCC, 22 uF, 25 V, X5R', 'Buck output (with C6)'),
 ('10uF 25V', 'C_0805_2012Metric'): ('CL21A106KAYNNNE', 'Samsung Electro-Mechanics', '0805 (2012 metric), h 1.25 mm', 'Capacitor, MLCC, 10 uF, 25 V, X5R', 'Buck input / VBAT at the ESC link'),
 ('402k 1%', 'R_0402_1005Metric'): (Y('402K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 402 kOhm, 1%, 1/16 W', 'Buck feedback, top'),
 ('100R', 'R_0402_1005Metric'): (Y('100R'), 'Yageo', '0402 (1005 metric)', 'Resistor, 100 Ohm, 1%, 1/16 W', 'ESC link series resistors (M1-M8, TLM)'),
 ('ESC link', 'JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal'): ('SM08B-SRSS-TB(LF)(SN)', 'JST', 'JST SH 8P side entry, h 2.9 mm',
     'Connector, JST SH, 8 positions, 1.0 mm pitch, side entry', 'ESC links (top side): J2 ESC A rear edge (power, CUR, M1-M4); J6 ESC B front edge next to J5 (M5-M8)'),
 ('ESC link B', 'JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal'): ('SM08B-SRSS-TB(LF)(SN)', 'JST', 'JST SH 8P side entry, h 2.9 mm',
     'Connector, JST SH, 8 positions, 1.0 mm pitch, side entry', 'ESC link B (M5-M8), top side, front edge next to the ELRS port J5, mouth toward the front'),
 ('470uF 6.3V polymer', 'CP_EIA-7343-31_Kemet-D'): ('T520D477M006ATE015', 'KEMET', '7343-31 (EIA D), h 2.8 mm',
     'Capacitor, tantalum polymer, 470 uF, 6.3 V, 20%, ESR 15 mOhm', 'Bulk at the battery input. Alternative: Panasonic 6TPE470MI'),
 ('10uF 10V', 'C_0603_1608Metric'): ('GRM188R61A106KE69D', 'Murata', '0603 (1608 metric)',
     'Capacitor, MLCC, 10 uF, 10 V, X5R, 10%', 'Motor-stage local decoupling, next to each MOSFET'),
 ('100uF 6.3V', 'C_1206_3216Metric'): ('GRM31CR60J107ME39L', 'Murata', '1206 (3216 metric), h 1.6 mm',
     'Capacitor, MLCC, 100 uF, 6.3 V, X5R, 20%', 'Buck output (VREG)'),
 ('4.7uF', 'C_0603_1608Metric'): ('GRM188R61A475KE15D', 'Murata', '0603 (1608 metric), h 0.8 mm',
     'Capacitor, MLCC, 4.7 uF, 10 V, X5R, 10%', 'VSYS (C7) and MCU VDD bulk (C9)'),
 ('4.7uF 10V', 'C_0603_1608Metric'): ('GRM188R61A475KE15D', 'Murata', '0603 (1608 metric), h 0.8 mm',
     'Capacitor, MLCC, 4.7 uF, 10 V, X5R, 10%', 'Charger RC (with R7), bottom side'),
 ('1uF', 'C_0402_1005Metric'): ('GRM155R61A105KE15D', 'Murata', '0402 (1005 metric)',
     'Capacitor, MLCC, 1 uF, 10 V, X5R, 10%', 'LDO output (C8), VDDA (C22)'),
 ('1uF 10V', 'C_0402_1005Metric'): ('GRM155R61A105KE15D', 'Murata', '0402 (1005 metric)',
     'Capacitor, MLCC, 1 uF, 10 V, X5R, 10%', 'Charger input'),
 ('100nF', 'C_0402_1005Metric'): ('GRM155R71C104KA88D', 'Murata', '0402 (1005 metric)',
     'Capacitor, MLCC, 100 nF, 16 V, X7R, 10%', 'Decoupling (MCU, sensors, NRST)'),
 ('220nF', 'C_0402_1005Metric'): ('GRM155R71C224KA12D', 'Murata', '0402 (1005 metric)',
     'Capacitor, MLCC, 220 nF, 16 V, X7R, 10%', 'IIS2MDC C1 (ESR < 200 mOhm)'),
 ('10uF 6.3V', 'C_0603_1608Metric'): ('GRM188R60J106ME47D', 'Murata', '0603 (1608 metric), h 0.8 mm',
     'Capacitor, MLCC, 10 uF, 6.3 V, X5R, 20%', 'VDD bulk, bottom side'),
 ('white', 'LED_0402_1005Metric'): ('IN-S42ATUW', 'Inolux', '0402 (1005 metric)',
     'LED, white, 0402, Vf 3.1 V typ', 'Front navigation LEDs (supplied from VSYS)'),
 ('red', 'LED_0402_1005Metric'): ('IN-S42ATR', 'Inolux', '0402 (1005 metric)',
     'LED, red 631 nm, 0402, Vf 2.1 V typ', 'Rear navigation LEDs'),
 ('green', 'LED_0402_1005Metric'): ('IN-S42ATG', 'Inolux', '0402 (1005 metric)',
     'LED, green, 0402', 'Charge indicator (on = charging)'),
 ('STPS3L45AF', 'D_SMAflat'): ('STPS3L45AF', 'STMicroelectronics', 'SMAflat (DO-221AC)',
     'Diode, Schottky, 45 V, 3 A, low Vf', 'Motor freewheeling diode'),
 ('PMEG2010AEH', 'D_SOD-123F'): ('PMEG2010AEH,115', 'Nexperia', 'SOD-123F',
     'Diode, Schottky, 20 V, 1 A, Vf ~0.35 V', 'USB VBUS -> VSYS'),
 ('USB-C (HRO TYPE-C-31-M-12)', 'USB_C_Receptacle_HRO_TYPE-C-31-M-12'): ('TYPE-C-31-M-12', 'HRO (Korea Hroparts)', 'USB-C receptacle, 16 pin, SMD + THT shell',
     'Connector, USB Type-C receptacle, USB 2.0, top mount', 'Mouth 0.35 mm past the right-corner chamfer'),
 ('GPS port', 'JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal'): ('SM06B-SRSS-TB(LF)(SN)', 'JST', 'JST SH 6P side entry, SMD, h 2.9 mm',
     'Connector, JST SH, 6 positions, 1.0 mm pitch, side entry', 'Rev D GPS port at the right edge; 1:1 6-pin JST SH cable to the GPS board'),
 ('AON7524', 'Vishay_PowerPAK_1212-8_Single'): ('AON7524', 'Alpha & Omega Semiconductor', 'DFN 3x3 EP (DFN3x3A_8L_EP1)',
     'MOSFET, N-channel, 30 V, logic level, 5.8 mOhm @ VGS 2.5 V', 'Footprint is a PowerPAK 1212-8 approximation: check the AOS land pattern before ordering'),
 ('AO3401A', 'SOT-23'): ('AO3401A', 'Alpha & Omega Semiconductor', 'SOT-23',
     'MOSFET, P-channel, 30 V, 4 A', 'Battery/USB load sharing'),
 ('2N7002DW', 'SOT-363_SC-70-6'): ('2N7002DW-7-F', 'Diodes Inc.', 'SOT-363 (SC-70-6)',
     'MOSFET, dual N-channel, 60 V, 115 mA', 'LED drivers'),
 ('1R', 'R_0603_1608Metric'): ('RC0603FR-071RL', 'Yageo', '0603 (1608 metric)',
     'Resistor, 1 Ohm, 1%, 0.1 W', 'RC filter (VBAT -> VBAT_F)'),
 ('100k', 'R_0402_1005Metric'): (Y('100K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 100 kOhm, 1%, 1/16 W', 'Pull-downs and VBUS divider'),
 ('287k 1%', 'R_0402_1005Metric'): (Y('287K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 287 kOhm, 1%, 1/16 W', 'LDO feedback (VOUT = 3.10 V)'),
 ('100k 1%', 'R_0402_1005Metric'): (Y('100K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 100 kOhm, 1%, 1/16 W', 'LDO feedback'),
 ('3.3k 1%', 'R_0402_1005Metric'): (Y('3K3'), 'Yageo', '0402 (1005 metric)', 'Resistor, 3.3 kOhm, 1%, 1/16 W', 'Charger PROG: I_BAT ~300 mA'),
 ('1k', 'R_0402_1005Metric'): (Y('1K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 1 kOhm, 1%, 1/16 W', 'Charge LED'),
 ('1R', 'R_0402_1005Metric'): (Y('1R'), 'Yageo', '0402 (1005 metric)', 'Resistor, 1 Ohm, 1%, 1/16 W', 'Charger RC (STC4054 DS sec. 6.13)'),
 ('470k 1%', 'R_0402_1005Metric'): (Y('470K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 470 kOhm, 1%, 1/16 W', 'VBAT sense divider'),
 ('5.1k', 'R_0402_1005Metric'): (Y('5K1'), 'Yageo', '0402 (1005 metric)', 'Resistor, 5.1 kOhm, 1%, 1/16 W', 'USB-C CC pull-downs'),
 ('10k', 'R_0402_1005Metric'): (Y('10K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 10 kOhm, 1%, 1/16 W', 'BOOT0 pull-down (PH3-BOOT0)'),
 ('2.2k', 'R_0402_1005Metric'): (Y('2K2'), 'Yageo', '0402 (1005 metric)', 'Resistor, 2.2 kOhm, 1%, 1/16 W', 'I2C1 pull-ups'),
 ('4.7k', 'R_0402_1005Metric'): (Y('4K7'), 'Yageo', '0402 (1005 metric)', 'Resistor, 4.7 kOhm, 1%, 1/16 W', 'Sensor hub pull-ups'),
 ('22R', 'R_0402_1005Metric'): (Y('22R'), 'Yageo', '0402 (1005 metric)', 'Resistor, 22 Ohm, 1%, 1/16 W', 'MOSFET gate resistors'),
 ('220R', 'R_0402_1005Metric'): (Y('220R'), 'Yageo', '0402 (1005 metric)', 'Resistor, 220 Ohm, 1%, 1/16 W', 'White LED current'),
 ('470R', 'R_0402_1005Metric'): (Y('470R'), 'Yageo', '0402 (1005 metric)', 'Resistor, 470 Ohm, 1%, 1/16 W', 'Red LED current'),
 ('LSM6DSV16X', 'LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y'): ('LSM6DSV16XTR', 'STMicroelectronics', 'LGA-14, 2.5 x 3 x 0.83 mm',
     'IMU, 6-axis (accelerometer + gyroscope), I2C/I3C/SPI, sensor hub', 'Top, just south of the centred MCU (0, -7.6), rotated 270 deg (remap the axes in firmware); SPI1, shared with the log flash'),
 ('STM32WB55CGU6', 'QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm'): ('STM32WB55CGU6', 'STMicroelectronics', 'UFQFPN-48, 7 x 7 x 0.55 mm, EP 5.6 mm',
     'MCU, Cortex-M4 + M0+ radio core, BLE 5 / 802.15.4, 1 MB flash, 256 KB RAM, SMPS', 'EP to GND through a 3x3 via array'),
 ('MLPF-WB55-01E3', 'ST_MLPF-WB55-01E3_CSP-6'): ('MLPF-WB55-01E3', 'STMicroelectronics', 'CSP-6 (bumps), 1.0 x 1.6 mm approx., pitch 0.5 mm',
     '2.4 GHz low-pass filter with integrated impedance matching for STM32WB55 RF1', 'Between U2 RF1 and the antenna feed (AN5290 IPD BoM)'),
 ('2450AT18A0100001E', 'Johanson_2450AT18x100'): ('2450AT18A0100001E', 'Johanson Technology', '1206 (3.2 x 1.6 x 1.3 mm)',
     'Chip antenna, 2.4 GHz, 0.5 dBi, 50 Ohm', 'Johanson global P/N of the legacy 2450AT18A100E (same part). Left board edge, in the copper keep-out; R34 = 0R, C36 not fitted'),
 ('32MHz', 'Crystal_SMD_2016-4Pin_2.0x1.6mm'): ('NX2016SA-32M-EXS00A-CS06654', 'NDK', 'SMD 2016, 4 pad, 2.0 x 1.6 mm',
     'Crystal, 32 MHz, HSE for the STM32WB radio', 'No load capacitors: internal HSE trimming (AN5042). Also the RF wake-up (HSE/1024) and RTC (HSE/32) clock: no LSE'),
 ('2.2uH', 'L_0805_2012Metric'): ('74479774222', 'Wurth Elektronik', '0805 (2012 metric), h 1.0 mm',
     'Inductor, multilayer (WE-PMI), 2.2 uH, 20%, Isat 250 mA, DCR 0.34 Ohm', 'SMPS inductor for the 8 MHz SMPS clock (DS13252 table 6)'),
 ('10nH', 'L_0402_1005Metric'): ('LQG15WZ10NJ02D', 'Murata', '0402 (1005 metric)',
     'Inductor, multilayer, 10 nH, 5%', 'SMPS output filter, AN5290'),
 ('4.7uF', 'C_0402_1005Metric'): ('GRM155R61A475MEAAD', 'Murata', '0402 (1005 metric)',
     'Capacitor, MLCC, 4.7 uF, 10 V, X5R, 20%', 'SMPS output (VFBSMPS)'),
 ('100pF', 'C_0402_1005Metric'): ('GRM1555C1H101JA01D', 'Murata', '0402 (1005 metric)',
     'Capacitor, MLCC, 100 pF, 50 V, C0G, 5%', 'VDDRF high-frequency decoupling'),
 ('0R', 'R_0402_1005Metric'): ('RC0402JR-070RL', 'Yageo', '0402 (1005 metric)',
     'Resistor, 0 Ohm jumper, 1/16 W', 'Antenna tuning, series position (replace with L/C after tuning)'),
 ('DNP', 'C_0402_1005Metric'): ('-', '-', '0402 (1005 metric)',
     'Not populated: antenna tuning, shunt position', 'Leave empty; fit only after VNA tuning'),
 ('IIS2MDC', 'LGA-12_2x2mm_P0.5mm'): ('IIS2MDCTR', 'STMicroelectronics', 'LGA-12, 2 x 2 x 0.7 mm',
     'Magnetometer, 3-axis, +-50 gauss, 16 bit, I2C/SPI, industrial grade (LIS2MDL-compatible)', 'Front corner; read through the LSM6DSV16X sensor hub, address 0x1E'),
 ('LPS22HB', 'ST_HLGA-10_2x2mm_P0.5mm_LayoutBorder3x2y'): ('LPS22HBTR', 'STMicroelectronics', 'HLGA-10, 2 x 2 x 0.76 mm',
     'Pressure sensor (barometer), 260-1260 hPa, I2C/SPI', 'Altitude hold; address 0x5D. Keep the vent hole clear'),
 ('LD39130SPUR', 'DFN-6_1.3x1.2mm_P0.4mm'): ('LD39130SPUR', 'STMicroelectronics', 'DFN-6, 1.2 x 1.3 mm',
     'LDO regulator, adjustable, 300 mA, 1 uA quiescent', 'Set to 3.10 V by R3/R4'),
 ('STC4054GR', 'TSOT-23-5'): ('STC4054GR', 'STMicroelectronics', 'TSOT-23-5',
     'Battery charger, linear, single-cell Li-ion/LiPo, 4.2 V, up to 800 mA', 'Charge current set to ~300 mA by R5'),
 ('USBLC6-2SC6', 'SOT-23-6'): ('USBLC6-2SC6', 'STMicroelectronics', 'SOT-23-6',
     'ESD protection, 2-line, low capacitance, for USB 2.0', 'Next to the USB-C connector'),
 # ---- rev E
 ('2.2uF', 'C_0402_1005Metric'): ('CL05A225MQ5NSNC', 'Samsung Electro-Mechanics', '0402 (1005 metric)',
     'Capacitor, MLCC, 2.2 uF, 6.3 V, X5R, 20%', 'Expansion LDO output (VEXP)'),
 ('10nF', 'C_0402_1005Metric'): ('CL05B103KB5NNNC', 'Samsung Electro-Mechanics', '0402 (1005 metric)',
     'Capacitor, MLCC, 10 nF, 50 V, X7R, 10%', '-'),
 ('WS2812B-2020', 'LED_WS2812B-2020_PLCC4_2.0x2.0mm'): ('WS2812B-2020', 'Worldsemi', '2.0 x 2.0 x 0.84 mm, 4 pad',
     'LED, RGB, addressable, integrated driver (WS2812 protocol)', 'Status LEDs D1 rear, D2 left, D3 front, D4 right: one chain from PA7 (TIM17_CH1 + DMA); D3 / D4 supply pins face away from the magnetometer'),
 ('RB521S30', 'D_SOD-523'): ('RB521S30T1G', 'onsemi', 'SOD-523',
     'Diode, Schottky, 30 V, 200 mA', 'VSYS -> VLED (keeps the LEDs below their VDD max with USB 5 V)'),
 ('Qwiic', 'JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal'): ('SM04B-SRSS-TB(LF)(SN)', 'JST', 'JST SH 4P side entry, SMD, h 2.9 mm',
     'Connector, JST SH, 4 positions, 1.0 mm pitch, side entry', 'Qwiic / STEMMA QT expansion port (GPS, flow): 1 GND, 2 3.3 V, 3 SDA, 4 SCL'),
 ('ELRS', 'JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal'): ('SM04B-SRSS-TB(LF)(SN)', 'JST', 'JST SH 4P side entry, SMD, h 2.9 mm',
     'Connector, JST SH, 4 positions, 1.0 mm pitch, side entry', 'ELRS receiver port (CRSF, USART1): 1 GND, 2 VSYS, 3 RX, 4 TX'),
 ('TSC213', 'SOT-363_SC-70-6'): ('TSC213ICT', 'STMicroelectronics', 'SC70-6 (SOT-363)',
     'Current-sense amplifier, high-side/low-side, gain 50 V/V, zero drift', 'Battery current: 0.1 V/A on ISNS (PA7)'),
 ('W25Q128JV', 'WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4mm'): ('W25Q128JVPIQ', 'Winbond', 'WSON-8, 6 x 5 x 0.75 mm',
     'NOR flash, 128 Mbit (16 MB), SPI/QSPI', 'Flight log (blackbox); SPI1, CS PE4; bottom side'),
 ('LDK130PU-R', 'DFN-6_1.3x1.2mm_P0.4mm'): ('LDK130PU-R', 'STMicroelectronics', 'DFN-6, 1.2 x 1.3 mm',
     'LDO regulator, adjustable, 300 mA, low noise', 'Expansion bus 3.3 V (VEXP), set to 3.31 V by R40/R41'),
 ('2m', 'R_1206_3216Metric'): ('RLM12FTCMR002', 'TA-I Tech', '1206 (3216 metric)',
     'Resistor, current sense, 2 mOhm, 1%, 1 W', 'Battery shunt, Kelvin-connected to U9'),
 ('33R', 'R_0402_1005Metric'): (Y('33R'), 'Yageo', '0402 (1005 metric)', 'Resistor, 33 Ohm, 1%, 1/16 W', 'RGB data line series resistor'),
 ('47k 1%', 'R_0402_1005Metric'): (Y('47K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 47 kOhm, 1%, 1/16 W', 'VEXP divider, top'),
 ('15k 1%', 'R_0402_1005Metric'): (Y('15K'), 'Yageo', '0402 (1005 metric)', 'Resistor, 15 kOhm, 1%, 1/16 W', 'VEXP divider, bottom'),
}
# not-assembled items: (value, MPN, manufacturer, package, description, notes)
NOT_ASSEMBLED = {
 'TP': ('pogo pad', 'N/A (PCB feature)', 'N/A', 'TestPoint_Pad_D1.0mm: 1.0 mm round SMD pad',
        'Programming / debug pads, 2 x 4 grid at 2.54 mm pitch',
        'Row 1: SWDIO, SWCLK, NRST, BOOT0; row 2: VDD, GND, CRSF_TX, CRSF_RX (USART1, PB6/PB7). Use a 2.54 mm pogo-pin fixture'),
 'J': ('solder pad', 'N/A (PCB feature)', 'N/A', 'TestPoint_Pad_2.0x2.0mm: 2 x 2 mm SMD pad',
       'Battery / power input pads: J7 VBAT+ (1S-6S), J8 GND',
       'Top side, left edge. FC supply only (no motor current): for ESCs without a VBAT pin or a separate PDB. Same VBAT net as ESC link A pin 2'),
 'H': ('D3.2 PTH', 'N/A (PCB feature)', 'N/A', 'Grommet_PTH_3.2mm_Pad5.0mm: plated 3.2 mm hole, 5.0 mm ring',
       'Mounting holes for M2 anti-vibration grommets, 20 x 20 mm pattern',
       'Exposed 5.0 mm GND copper ring on both sides (grommet seat). Grommets supplied with the frame'),
}
DNP_INFO = ('Not populated (tuning)', 'TBD after VNA tuning (C0G capacitor or chip inductor)', 'Murata (GRM1555C1H C0G or LQG15HS series)',
            '0402 (1005 metric)', 'Antenna tuning, shunt position at the antenna side',
            'Do not populate. Fit only if the VNA measurement asks for it; R34 (series) is the other tuning spot')

key = lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0))
groups = {}
skipped = []
dnp = []
for ref, v in parts.items():
    fpn = v['fp'].split(':')[1]
    if ref.startswith(('TP', 'H')) or fpn == 'TestPoint_Pad_2.0x2.0mm':
        skipped.append(ref); continue
    if v.get('dnp'):
        dnp.append(ref); continue
    k = (v['value'], fpn)
    if k not in MPN:
        raise SystemExit('no MPN for %s %s' % (ref, k))
    # split groups that are mounted on both sides
    groups.setdefault((MPN[k][0], v['value'], fpn, side[ref]), []).append(ref)

FONT = 'Arial'
wb = Workbook(); ws = wb.active; ws.title = 'BoM'
hdr = ['Item', 'Quantity', 'Part Reference', 'Value', 'MPN', 'Manufacturer', 'LCSC / JLCPCB #', 'Package', 'Description', 'Side', 'Notes']
ws.append(['ACwing FC rev A - assembly BoM (1 board)'])
ws.append(['Source: ACwing_FC_A.kicad_sch / ACwing_FC_A.kicad_pcb. MPNs = parts as assembled by JLCPCB (LCSC part numbers checked on 2026-10-16/18); equivalents are noted where they replace the originally specified part.'])
ws.append([])
ws.append(hdr)
H = 4
thin = Side(style='thin', color='BFBFBF')
rows = sorted(groups.items(), key=lambda kv: key(sorted(kv[1], key=key)[0]))
for i, ((mpn, val, fpn, sd), refs) in enumerate(rows, 1):
    m = MPN[(val, fpn)]
    refs = sorted(refs, key=key)
    note = m[4]
    if val == '100k':
        note = 'Q5 gate pull-down (R2), VBUS sense divider (R10, R11)'
    if val == '1k':
        note = 'ADC RC on ESC_CUR (R42)'
    if val == '100k 1%':
        note = 'LDO feedback (R4), VBAT sense divider top (R8)'
    if val == '10k':
        note = 'BOOT0 pull-down (R14), FLASH_CS / IMU_CS pull-ups (R37, R38), VBAT sense divider bottom (R9)'
    if sd == 'Bottom' and 'h ' not in m[2] and fpn.startswith(('C_0603', 'C_1206')):
        note += '; bottom side, height <= 1.2 mm'
    o = LCSC[(val, fpn)]
    if o[5]:
        note = note + '. ' + o[5] if note else o[5]
    ws.append([i, len(refs), ', '.join(refs), val, o[0], o[1], o[2], m[2], o[4] or m[3], sd, note])
last = ws.max_row
ws.append([])
ws.append(['Total', '=SUM(B%d:B%d)' % (H + 1, last), 'Total placements (assembled parts)', '-', '=COUNTA(E%d:E%d)' % (H + 1, last), 'line items (unique MPN / side)', '-', '-', '-', '-', 'Not-assembled items listed below'])
tot = ws.max_row

ws.append([])
ws.append(['Not assembled (PCB features / off-board)'])
na0 = ws.max_row
ws.append(hdr)
NA_H = ws.max_row
k = 0
for pref, (val, mpn, man, pkg, desc, note) in NOT_ASSEMBLED.items():
    refs = sorted([r for r in skipped if r.startswith(pref)], key=key)
    k += 1
    ws.append(['NA%d' % k, len(refs), ', '.join(refs), val, mpn, man, 'N/A', pkg, desc, ('Both (plated through)' if pref == 'H' else ', '.join(sorted({side[r] for r in refs}))), note])
for r in sorted(dnp, key=key):
    k += 1
    ws.append(['NA%d' % k, 1, r, parts[r]['value']] + list(DNP_INFO[1:3]) + ['-'] + list(DNP_INFO[3:5]) + [side[r], DNP_INFO[5]])
end = ws.max_row

# formatting
for row in ws.iter_rows(min_row=1, max_row=end):
    for c in row:
        c.font = Font(name=FONT, size=10)
        c.alignment = Alignment(wrap_text=True, vertical='top')
ws['A1'].font = Font(name=FONT, size=13, bold=True)
ws['A2'].font = Font(name=FONT, size=9, italic=True, color='595959')
for c in ws[H]:
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='305496')
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
for r in range(H + 1, last + 1):
    for c in ws[r]:
        c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
        if r % 2 == 0:
            c.fill = PatternFill('solid', fgColor='F2F2F2')
    ws.cell(r, 1).alignment = Alignment(horizontal='center', vertical='top')
    ws.cell(r, 2).alignment = Alignment(horizontal='center', vertical='top')
for c in ws[tot]:
    c.font = Font(name=FONT, size=10, bold=True)
ws.cell(tot, 2).alignment = Alignment(horizontal='center')
ws.cell(tot, 5).alignment = Alignment(horizontal='right')
ws.cell(na0, 1).font = Font(name=FONT, size=11, bold=True)
ws.cell(na0, 1).alignment = Alignment(wrap_text=False, vertical='top')
ws.merge_cells(start_row=na0, start_column=1, end_row=na0, end_column=11)
for c in ws[NA_H]:
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='7F7F7F')
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
for r in range(NA_H + 1, end + 1):
    for c in ws[r]:
        c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
    ws.cell(r, 1).alignment = Alignment(horizontal='center', vertical='top')
    ws.cell(r, 2).alignment = Alignment(horizontal='center', vertical='top')
for col, w in zip(range(1, 12), (6, 9, 30, 20, 24, 22, 14, 28, 48, 8, 50)):
    ws.column_dimensions[get_column_letter(col)].width = w
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=11)
ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=11)
ws.freeze_panes = 'A%d' % (H + 1)
ws.auto_filter.ref = 'A%d:K%d' % (H, last)
ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToHeight = 0
wb.save(OUT)
print('line items', len(rows), 'placements', sum(len(v) for v in groups.values()), 'not assembled', len(skipped)+len(dnp))
