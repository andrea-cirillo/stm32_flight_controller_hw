<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="00%20-%20Docs/05%20-%20Brand/ACwing_logo_white.png">
    <img alt="ACwing" src="00%20-%20Docs/05%20-%20Brand/ACwing_logo_black.png" width="260">
  </picture>
</p>

<h1 align="center">ACwing – open drone flight hardware</h1>

<p align="center">
  STM32WB55 flight controller, 1S power board, GNSS and optical-flow expansions<br>
  KiCad 7 · JLCPCB-ready · by Andrea Cirillo
</p>

---

ACwing is a modular set of PCBs for small multirotors. The core is a **universal flight controller** that talks to its
power stage through the common **4-in-1 ESC connector** (JST SH 8-pin): on the 1S indoor mini drone it sits on the
ACwing 1S power board; on a larger 3S–6S brushless drone the same FC runs with one or two commercial 20 × 20 4-in-1
ESCs. Two optional expansion boards plug into the FC's **Qwiic** (I2C) ports: a **GNSS + compass** board for outdoor
flight and an **optical-flow + ToF** board for indoor position and height hold.

<p align="center">
  <img src="00%20-%20Docs/00%20-%20FC_Docs/ACwing_FC_A_pcb.png" alt="ACwing FC rev A, top and bottom" width="820">
</p>

## Boards

| Board | Rev | Size | Layers | What it does | Docs | KiCad |
|---|---|---|---|---|---|---|
| **ACwing FC** | H | 40 × 40 mm, 20 × 20 holes (grommets) | 4, 1.0 mm | flight controller, 1S–6S input, up to 8 motors, BLE | [FC docs](00%20-%20Docs/00%20-%20FC_Docs/) | [project](01%20-%20FC_KiCadProj/) |
| **ACwing ESC 1S** | B | 40 × 40 mm, 20 × 20 holes | 4, 1.0 mm | 1S power board: 4 brushed motor stages, current sensor, USB-C charger | [ESC docs](00%20-%20Docs/01%20-%20ESC_1S_Docs/) | [project](02%20-%20ESC_1S_KiCadProj/) |
| **ACwing GPS** | D | 30 × 30 mm, 20 × 20 holes | 2, 1.0 mm | GNSS (u-blox SAM-M10Q) + compass, stacked above the FC | [GPS docs](00%20-%20Docs/02%20-%20GPS_Docs/) | [project](03%20-%20GPS_KiCadProj/) |
| **ACwing Flow** | A | 21 × 25 mm, 2 × M2 | 2, 1.0 mm | optical flow (PMW3901) + ToF height (VL53L1X), under the frame | [Flow docs](00%20-%20Docs/03%20-%20FLOW_Docs/) | [project](04%20-%20FLOW_KiCadProj/) |

Every board folder in `00 - Docs` holds the schematic PDF, the BoM with costing, the JLCPCB BoM and pick-and-place
files, the Gerber zip, the DRC report, the STEP model and board views.

## System

```
              ┌─────────────────────────┐   Qwiic (J3)   ┌──────────────────┐
              │      ACwing FC rev A    │───────────────▶│  ACwing GPS rev A │  optional, outdoor
  USB-C ─────▶│ STM32WB55 · IMU · baro  │                └──────────────────┘
  ELRS RX ───▶│ compass · 16 MB flash   │   Qwiic (J4)   ┌──────────────────┐
              │ BLE · 4 × RGB LED       │───────────────▶│ ACwing Flow rev A │  indoor
              └───────┬─────────┬───────┘                └──────────────────┘
          ESC link A  │         │  ESC link B (motors 5–8)
         (JST SH 8)   ▼         ▼
   ┌──────────────────────┐   ┌──────────────────────────┐
   │ ACwing ESC 1S rev A  │ or│ commercial 4-in-1 ESC(s) │
   │ 1S, brushed, charger │   │ 2S–6S, brushless         │
   └──────────────────────┘   └──────────────────────────┘
```

**Stack (1S mini drone, frame C2):** ESC 1S hard-mounted on the frame bosses → 5 mm → FC on M2 damping grommets →
6 mm → GPS board (optional). The flow board is mounted under the battery bay, sensor side down.

<p align="center">
  <img src="00%20-%20Docs/04%20-%20System_Docs/ACwing_stack_3D.png" alt="ACwing stack: ESC 1S, FC and GPS" width="640">
</p>

The interactive stack check (every part as a prism, every connector with a mated-plug envelope; 0 clashes) is in
[`04 - System_Docs/ACwing_stack_check.html`](00%20-%20Docs/04%20-%20System_Docs/) – download the folder and open the
page locally.

## Key features

**ACwing FC rev A**
- MCU **STM32WB55CGU6** (Cortex-M4 + M0+ radio core), BLE 5 with chip antenna and ST MLPF-WB55 front end.
- Sensors: **LSM6DSV16X** IMU, **LPS22HB** barometer, **IIS2MDC** compass; **W25Q128JV** 16 MB log flash.
- Input **1S–6S** (LM5166 buck, 3–65 V; 100 % duty cycle pass-through on 1S), 4.1 V system rail, 3.1 V and 3.31 V LDOs.
- **Two ESC links** (JST SH 8-pin, standard 4-in-1 pinout): 8 motor outputs (TIM2 / TIM1 / TIM16), VBAT and current
  sense from the ESC, battery pads for setups without a VBAT pin.
- Two Qwiic ports, ELRS / CRSF UART port, USB-C (data, DFU, bench supply), 4 × WS2812B, SWD pogo grid.

**ACwing ESC 1S rev A**
- 4 brushed motor stages (AON7524 N-MOSFETs) for coreless 8520 motors, 470 µF bulk capacitor.
- 2 mΩ shunt + TSC213 current sense (0.1 V/A) on the ESC link.
- USB-C 1S charger (STC4054, 455 mA) with a charge switch that keeps FC and motors off while charging.
- Battery solder pads for a JST PH 2.0 pigtail.

**ACwing GPS rev A** – u-blox **SAM-M10Q** (integrated patch antenna, I2C/DDC) and **IIS2MDC** compass away from the
motor currents; Qwiic in / out on the top side, PPS LED, backup supply.

**ACwing Flow rev A** – PixArt **PMW3901MB** flow sensor behind an **STM32C011** I2C bridge, ST **VL53L1X** ToF;
Qwiic in / out; all parts on the sensor side.

## Repository structure

```
00 - Docs/
├── 00 - FC_Docs/         FC rev A: README, pin map, schematic, BoM, JLC files, Gerber, STEP, views
├── 01 - ESC_1S_Docs/     ESC 1S rev A: same set
├── 02 - GPS_Docs/        GPS rev A: same set
├── 03 - FLOW_Docs/       Flow rev A: same set + mechanical DXF
├── 04 - System_Docs/     mechanical handoff, frame C2 answer and reply, stack check (3D page and render)
└── 05 - Brand/           ACwing logos (SVG/PNG), silkscreen logo footprints, brand and silkscreen tools
01 - FC_KiCadProj/        KiCad project, library, 3D models, generator scripts
02 - ESC_1S_KiCadProj/
03 - GPS_KiCadProj/
04 - FLOW_KiCadProj/
```

## Ordering (JLCPCB)

For each board, from its docs folder:
1. Upload `<board>_gerber.zip` (1.0 mm FR-4; 4 layers for FC and ESC, 2 layers for GPS and Flow).
2. Enable assembly and upload `<board>_BoM_JLCPCB.xlsx` and `<board>_CPL.xlsx`. Every BoM line carries its LCSC part
   number; the CPL already includes the rotation corrections. Check the pin-1 marks in the JLC preview as listed in the
   board README ("To check before ordering").

Indicative component cost per board (10 / 100 boards, components only): FC 28.2 / 22.7 USD, ESC 1S 6.4 / 5.1 USD,
GPS 27.6 / 23.4 USD, Flow 11.1 / 9.4 USD. Check LCSC stock before ordering.

## Status

**Layout update 2026-10-24 (still rev A):** FC microcontroller at the board centre, ESC link B next to the ELRS port on
the front edge, input buck moved to the left edge (no longer between the rear LEDs), LED supply kept away from the
magnetometer (EMI check in the FC README); GPS Qwiic J1 aligned with FC J3.

All four boards are routed with **0 DRC violations and 0 unconnected pads** (KiCad 7.0). They are not built and tested
yet: see each board README for the bench checks planned before the first order (ERC in KiCad 8/9, power-stage tests,
land patterns to verify). Firmware is a separate project.

## Author

**Andrea Cirillo** – ACwing hardware design.
