# Project symbol library "DimaQuad": parts missing from the KiCad 7 libraries.
import copy
from sexp import dump, find, find1, Sym
from kisch import flatten, rename_sym, set_prop, eff, S

LIB = 'DimaQuad'

def _pin(typ, x, y, a, name, num, length=2.54, hide=False):
    p = [S('pin'), S(typ), S('line'), [S('at'), x, y, a], [S('length'), length]]
    if hide:
        p.append(S('hide'))
    p += [[S('name'), name, eff()], [S('number'), num, eff()]]
    return p

def _props(sym, d):
    for k, v in d.items():
        set_prop(sym, k, v)

def power_sym(name):
    s = rename_sym(flatten('power', 'VCC'), 'VCC', name)
    _props(s, {'Value': name,
               'ki_description': 'Power symbol creates a global label with name "%s"' % name})
    for sub in find(s, 'symbol'):
        for e in sub:
            if isinstance(e, list) and e and e[0] == 'pin':
                find1(e, 'name')[1] = name
    return s

def lsm6dsv16x():
    s = rename_sym(flatten('Sensor_Motion', 'LSM6DSM'), 'LSM6DSM', 'LSM6DSV16X')
    _props(s, {'Value': 'LSM6DSV16X',
               'Footprint': 'Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y',
               'Datasheet': 'https://www.st.com/resource/en/datasheet/lsm6dsv16x.pdf',
               'ki_keywords': 'IMU accelerometer gyroscope 6-axis sensor hub',
               'ki_description': '6-axis IMU, I2C/I3C/SPI, sensor hub (Mode 2), LGA-14 2.5x3 mm'})
    ren = {'2': ('SDx', 'bidirectional'), '3': ('SCx', 'bidirectional'),
           '10': ('OCS_Aux', 'passive'), '11': ('SDO_Aux', 'passive')}
    for sub in find(s, 'symbol'):
        for e in sub:
            if isinstance(e, list) and e and e[0] == 'pin':
                n = find1(e, 'number')[1]
                if n in ren:
                    find1(e, 'name')[1] = ren[n][0]
                    e[1] = S(ren[n][1])
    return s

def stc4054():
    s = rename_sym(flatten('Battery_Management', 'LTC4054ES5-4.2'), 'LTC4054ES5-4.2', 'STC4054')
    _props(s, {'Value': 'STC4054',
               'Footprint': 'Package_TO_SOT_SMD:TSOT-23-5',
               'Datasheet': 'https://www.st.com/resource/en/datasheet/stc4054.pdf',
               'ki_keywords': 'li-ion charger linear 4.2V',
               'ki_description': '800 mA standalone linear Li-Ion charger, 4.2 V, TSOT23-5 (pinout LTC4054)'})
    return s

def ld39130s_adj():
    n = 'LD39130S-ADJ'
    body = [S('symbol'), n + '_0_1',
            [S('rectangle'), [S('start'), -7.62, 5.08], [S('end'), 7.62, -5.08],
             [S('stroke'), [S('width'), 0.254], [S('type'), S('default')]], [S('fill'), [S('type'), S('background')]]]]
    pins = [S('symbol'), n + '_1_1',
            _pin('power_in', -10.16, 2.54, 0, 'IN', '4'),
            _pin('input', -10.16, 0, 0, 'EN', '3'),
            _pin('input', -10.16, -2.54, 0, 'GM', '1'),
            _pin('power_out', 10.16, 2.54, 180, 'OUT', '6'),
            _pin('input', 10.16, 0, 180, 'ADJ', '5'),
            _pin('power_in', 0, -7.62, 90, 'GND', '2')]
    s = [S('symbol'), n, [S('in_bom'), S('yes')], [S('on_board'), S('yes')],
         [S('property'), 'Reference', 'U', [S('at'), -7.62, 6.35, 0], eff(justify='left')],
         [S('property'), 'Value', n, [S('at'), 0, -10.16, 0], eff()],
         [S('property'), 'Footprint', 'Package_DFN_QFN:DFN-6_1.3x1.2mm_P0.4mm', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'Datasheet', 'https://www.st.com/resource/en/datasheet/ld39130s.pdf', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_keywords', 'LDO regulator low quiescent adjustable', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_description', '300 mA LDO, 1 uA green mode, adjustable (VADJ 0.8 V), DFN6 1.2x1.3 mm', [S('at'), 0, 0, 0], eff(hide=True)],
         body, pins]
    return s

def aon7524():
    s = rename_sym(flatten('Device', 'Q_NMOS_GSD'), 'Q_NMOS_GSD', 'AON7524')
    _props(s, {'Value': 'AON7524',
               'Footprint': 'Package_SO:Vishay_PowerPAK_1212-8_Single',
               'Datasheet': 'https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf',
               'ki_keywords': 'N-MOSFET logic level 30V',
               'ki_description': '30 V N-MOSFET, 5.8 mOhm @ VGS 2.5 V, DFN 3x3 EP: 1-3 S, 4 G, 5-8 + EP D'})
    for sub in find(s, 'symbol'):
        new = []
        for e in sub:
            if isinstance(e, list) and e and e[0] == 'pin':
                num = find1(e, 'number')
                nm = find1(e, 'name')[1]
                if nm == 'G':
                    num[1] = '4'
                elif nm == 'D':
                    num[1] = '5'
                elif nm == 'S':
                    num[1] = '1'
                    for extra in ('2', '3'):
                        c = copy.deepcopy(e)
                        find1(c, 'number')[1] = extra
                        c.insert(5, S('hide'))
                        new.append(c)
            new.append(e) if e not in new else None
        sub[:] = new
    return s

def mlpf_wb55():
    n = 'MLPF-WB55-01E3'
    body = [S('symbol'), n + '_0_1',
            [S('rectangle'), [S('start'), -5.08, 2.54], [S('end'), 5.08, -2.54],
             [S('stroke'), [S('width'), 0.254], [S('type'), S('default')]], [S('fill'), [S('type'), S('background')]]]]
    pins = [S('symbol'), n + '_1_1',
            _pin('passive', -7.62, 0, 0, 'IN', 'A3'),
            _pin('passive', 7.62, 0, 180, 'OUT', 'A1'),
            _pin('power_in', 0, -5.08, 90, 'GND', 'B2'),
            _pin('passive', 0, -5.08, 90, 'GND', 'A2', hide=True),
            _pin('passive', 0, -5.08, 90, 'GND', 'B1', hide=True),
            _pin('passive', 0, -5.08, 90, 'GND', 'B3', hide=True)]
    s = [S('symbol'), n, [S('in_bom'), S('yes')], [S('on_board'), S('yes')],
         [S('property'), 'Reference', 'U', [S('at'), -5.08, 3.81, 0], eff(justify='left')],
         [S('property'), 'Value', n, [S('at'), 0, -7.62, 0], eff()],
         [S('property'), 'Footprint', 'DimaQuad:ST_MLPF-WB55-01E3_CSP-6', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'Datasheet', 'https://www.st.com/resource/en/datasheet/mlpf-wb55-01e3.pdf', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_keywords', 'RF low pass filter matching STM32WB', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_description', '2.4 GHz low-pass filter with integrated matching for STM32WB55 (IN = RF1, OUT = 50 ohm antenna), 6-bump CSP', [S('at'), 0, 0, 0], eff(hide=True)],
         body, pins]
    return s

def tsc213():
    n = 'TSC213'
    body = [S('symbol'), n + '_0_1',
            [S('rectangle'), [S('start'), -7.62, 5.08], [S('end'), 7.62, -5.08],
             [S('stroke'), [S('width'), 0.254], [S('type'), S('default')]], [S('fill'), [S('type'), S('background')]]]]
    pins = [S('symbol'), n + '_1_1',
            _pin('input', -10.16, 2.54, 0, 'VIN+', '4'),
            _pin('input', -10.16, -2.54, 0, 'VIN-', '5'),
            _pin('power_in', 0, 7.62, 270, 'VCC', '3'),
            _pin('power_in', 0, -7.62, 90, 'GND', '2'),
            _pin('input', 2.54, -7.62, 90, 'REF', '1'),
            _pin('output', 10.16, 0, 180, 'OUT', '6')]
    s = [S('symbol'), n, [S('in_bom'), S('yes')], [S('on_board'), S('yes')],
         [S('property'), 'Reference', 'U', [S('at'), -7.62, 6.35, 0], eff(justify='left')],
         [S('property'), 'Value', n, [S('at'), 0, -10.16, 0], eff()],
         [S('property'), 'Footprint', 'Package_TO_SOT_SMD:SOT-363_SC-70-6', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'Datasheet', 'https://www.st.com/resource/en/datasheet/tsc210.pdf', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_keywords', 'current sense amplifier zero drift bidirectional', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_description', 'Zero-drift current sense amplifier, gain 50 V/V, CM -0.3...26 V, SC70-6 (DS13237: 1 REF, 2 GND, 3 VCC, 4 VIN+, 5 VIN-, 6 OUT)', [S('at'), 0, 0, 0], eff(hide=True)],
         body, pins]
    return s

def tps62160():
    n = 'TPS62160'
    body = [S('symbol'), n + '_0_1',
            [S('rectangle'), [S('start'), -7.62, 7.62], [S('end'), 7.62, -7.62],
             [S('stroke'), [S('width'), 0.254], [S('type'), S('default')]], [S('fill'), [S('type'), S('background')]]]]
    pins = [S('symbol'), n + '_1_1',
            _pin('power_in', -10.16, 5.08, 0, 'VIN', '2'),
            _pin('input', -10.16, 0, 0, 'EN', '3'),
            _pin('power_out', 10.16, 5.08, 180, 'SW', '7'),
            _pin('input', 10.16, 2.54, 180, 'VOS', '6'),
            _pin('input', 10.16, -2.54, 180, 'FB', '5'),
            _pin('open_collector', 10.16, -5.08, 180, 'PG', '8'),
            _pin('power_in', -2.54, -10.16, 90, 'PGND', '1'),
            _pin('power_in', 0, -10.16, 90, 'AGND', '4'),
            _pin('passive', 2.54, -10.16, 90, 'EP', '9')]
    s = [S('symbol'), n, [S('in_bom'), S('yes')], [S('on_board'), S('yes')],
         [S('property'), 'Reference', 'U', [S('at'), -7.62, 8.89, 0], eff(justify='left')],
         [S('property'), 'Value', n, [S('at'), 0, -12.7, 0], eff()],
         [S('property'), 'Footprint', 'Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'Datasheet', 'https://www.ti.com/lit/ds/symlink/tps62160.pdf', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_keywords', 'buck converter step-down 17V 1A DCS-Control 100% mode', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_description', '3-17 V, 1 A synchronous step-down converter with 100% duty-cycle mode, adjustable (VFB 0.8 V), WSON-8 2x2 (DSG)', [S('at'), 0, 0, 0], eff(hide=True)],
         body, pins]
    return s

def lm5166():
    n = 'LM5166'
    body = [S('symbol'), n + '_0_1',
            [S('rectangle'), [S('start'), -7.62, 7.62], [S('end'), 7.62, -7.62],
             [S('stroke'), [S('width'), 0.254], [S('type'), S('default')]], [S('fill'), [S('type'), S('background')]]]]
    pins = [S('symbol'), n + '_1_1',
            _pin('power_in', -10.16, 5.08, 0, 'VIN', '2'),
            _pin('input', -10.16, 2.54, 0, 'EN', '7'),
            _pin('passive', -10.16, 0, 0, 'HYS', '9'),
            _pin('passive', -10.16, -2.54, 0, 'SS', '4'),
            _pin('passive', -10.16, -5.08, 0, 'RT', '5'),
            _pin('power_out', 10.16, 5.08, 180, 'SW', '1'),
            _pin('input', 10.16, 0, 180, 'FB', '8'),
            _pin('open_collector', 10.16, -2.54, 180, 'PGOOD', '6'),
            _pin('passive', 10.16, -5.08, 180, 'ILIM', '3'),
            _pin('power_in', -1.27, -10.16, 90, 'GND', '10'),
            _pin('passive', 1.27, -10.16, 90, 'PAD', '11')]
    s = [S('symbol'), n, [S('in_bom'), S('yes')], [S('on_board'), S('yes')],
         [S('property'), 'Reference', 'U', [S('at'), -7.62, 8.89, 0], eff(justify='left')],
         [S('property'), 'Value', n, [S('at'), 0, -12.7, 0], eff()],
         [S('property'), 'Footprint', 'Package_SON:Texas_DRC0010J', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'Datasheet', 'https://www.ti.com/lit/ds/symlink/lm5166.pdf', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_keywords', 'buck converter step-down 65V 500mA PFM COT 100% duty cycle', [S('at'), 0, 0, 0], eff(hide=True)],
         [S('property'), 'ki_description', '3-65 V, 500 mA synchronous step-down converter, 100% duty cycle (PFET high side), adjustable (VFB 1.223 V), VSON-10 3x3 (DRC)', [S('at'), 0, 0, 0], eff(hide=True)],
         body, pins]
    return s

def all_symbols():
    syms = {
        'LSM6DSV16X': lsm6dsv16x(),
        'LD39130S-ADJ': ld39130s_adj(),
        'MLPF-WB55-01E3': mlpf_wb55(),
        'LM5166': lm5166(),
    }
    for p in ('VBAT', 'VREG', 'VSYS'):
        syms[p] = power_sym(p)
    return syms

def write_lib(path):
    lib = [S('kicad_symbol_lib'), [S('version'), 20220914], [S('generator'), S('kicad_symbol_editor')]]
    lib += list(all_symbols().values())
    with open(path, 'w') as f:
        f.write(dump(lib) + '\n')
