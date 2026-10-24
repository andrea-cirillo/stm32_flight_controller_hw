# ACwing FC rev A – pin map (STM32WB55CGU6, UFQFPN-48)

**Date:** 2026-10-18. **Status:** as designed in ACwing FC rev A (schematic and PCB).

## Changes from draft G
- **Up to 8 motors.** M1–M4 stay on TIM2 CH1–CH4 (ESC link A, J2). M5–M7 go to TIM1 CH1–CH3 (PA8, PA9, PA10)
  and M8 to TIM16 CH1 (PA6), all on ESC link B (J6). Every motor timer has DMA requests on the WB55 (DMAMUX), so
  DShot and bidirectional DShot work on all eight outputs.
- **ELRS moves to the alternate USART1 pins PB6 TX / PB7 RX.** PA9/PA10 are taken by TIM1 for M6/M7.
- **RGB LEDs move to PA7** (TIM17 CH1 + DMA). PB6 is now USART1 TX.
- **ESC A serial telemetry moves to PB0** (plain GPIO with EXTI, software UART). Bidirectional DShot / EDT on the motor
  lines is the preferred telemetry path.
- **Removed:** CUR_EXT (PA6) and CHG_EN (PB2); there is no charger on the FC any more.
- **Unchanged for the add-on boards:** the expansion bus stays on I2C1 (PB8/PB9) with its own 3.3 V LDO (VEXP).
  Rev A has **two Qwiic ports in parallel (J3, J4)**, so the GPS board and the flow board each get their own cable.

All alternate functions below were checked against ST's pin data (STM32_open_pin_data, `STM32WB55CGUx.xml`).

## Pin map
| Pin | Port | Net | Peripheral / use | Package side (board) |
|---|---|---|---|---|
| 9 | PA0 | PWM_M1 | TIM2_CH1 (PWM / DShot, DMA burst) | east |
| 10 | PA1 | PWM_M2 | TIM2_CH2 | east |
| 11 | PA2 | PWM_M3 | TIM2_CH3 | east |
| 12 | PA3 | PWM_M4 | TIM2_CH4 | east |
| 17 | PA8 | PWM_M5 | TIM1_CH1 (DMA) | north |
| 18 | PA9 | PWM_M6 | TIM1_CH2 (draft G: CRSF_TX) | north |
| 36 | PA10 | PWM_M7 | TIM1_CH3 (draft G: CRSF_RX) | west |
| 15 | PA6 | PWM_M8 | TIM16_CH1 (DMA) (draft G: CUR_EXT) | north |
| 13 | PA4 | ESC_CUR | ADC1_IN9: current from ESC link A | north |
| 14 | PA5 | VBAT_SNS | ADC1_IN10: VBAT × 10/110 (100k/10k), 25.2 V (6S) → 2.29 V, full scale 34 V | north |
| 28 | PB0 | ESC_TLM_MCU | GPIO / EXTI: ESC A serial telemetry, optional (draft G: PB7) | west |
| 46 | PB6 | CRSF_TX | USART1_TX (alternate pin): ELRS receiver J5 | south |
| 47 | PB7 | CRSF_RX | USART1_RX (alternate pin) | south |
| 16 | PA7 | RGB_DIN | TIM17_CH1 + DMA: 4 × WS2812B-2020, D1 rear → D2 → D3 front → D4 (draft G: PB6) | north |
| 43 | PB3 | SPI_SCK | SPI1_SCK: IMU + log flash | south |
| 44 | PB4 | SPI_MISO | SPI1_MISO | south |
| 45 | PB5 | SPI_MOSI | SPI1_MOSI | south |
| 2 | PC14 | IMU_CS | GPIO (backup-domain pin, 2 MHz: enough for a chip select) | east |
| 30 | PE4 | FLASH_CS | GPIO | west |
| 42 | PA15 | IMU_INT1 | EXTI15 | south |
| 5 | PB8 | I2C_SCL | I2C1: expansion bus (Qwiic J3 + J4: GPS board, flow board) | east |
| 6 | PB9 | I2C_SDA | I2C1 | east |
| 29 | PB1 | VBUS_DET | GPIO (VBUS/2): USB present | west |
| 37 / 38 | PA11 / PA12 | USB_DM / USB_DP | USB FS (DFU, CDC) | south |
| 39 / 41 | PA13 / PA14 | SWDIO / SWCLK | SWD (pogo pads) | south |
| 4 | PH3-BOOT0 | BOOT0 | 10 k pull-down, pogo pad | east |
| 7 | NRST | NRST | 100 nF, pogo pad | east |
| 21 | RF1 | RF_IN | MLPF-WB55-01E3 → 50 Ω line → chip antenna at the left edge | north |
| 24 / 25 | OSC_OUT / OSC_IN | HSE | 32 MHz crystal (no LSE) | north / west |
| 31–33 | VFBSMPS / VSSSMPS / VLXSMPS | SMPS | 2.2 µH + 10 nH + 4.7 µF (8 MHz option) | west |

- **Free pins:** PB2 (pin 19). **Not connected:** PC15 (no LSE).
- **Timers:** TIM2 = M1–M4 (one DMA burst), TIM1 = M5–M7 (one DMA burst), TIM16 = M8, TIM17 = RGB LEDs.
  LPTIM1/LPTIM2 stay free (they cannot do DShot). The WB55 has no other general-purpose timer: 8 motors and the LED
  chain use all of them.
- **UARTs:** USART1 = ELRS. LPUART1 has no free pin pair (its TX/RX pins are PA2/PA3, PB5 or PA12, all taken), so a
  GPS module with a UART cannot be connected directly: use a GNSS module on I2C (our GPS board, u-blox DDC) or one
  with an I2C/Qwiic port.

## Board side of the MCU (U2 rotated 180°, board frame u right, v front)
- East (pins 1–12): motors M1–M4, I2C, BOOT0, NRST → ESC A (rear) and Qwiic (right edge).
- North (pins 13–24): ADC inputs, M5/M6/M8, RGB, RF, HSE → ESC B (left edge) through bottom-side resistors R25, R26, R28.
- West (pins 25–36): HSE_IN, SMPS, TLM, VBUS_DET, flash CS, M7 (R27) → ESC B.
- South (pins 37–48): USB, SWD, SPI, ELRS (PB6/PB7).

## ESC link A (J2, JST SH 8-pin, top side, rear edge at (u, v) = (+1.5, −16.9), mouth toward the rear)
| Pin | Signal | FC side |
|---|---|---|
| 1 | GND | GND |
| 2 | VBAT | 1S–6S: input buck U12 (LM5166) → VREG 4.1 V → Q5 → VSYS; VBAT_SNS divider; C2 4.7 µF 50 V |
| 3 | CUR | 1 k → PA4 ADC (0–3.1 V; ACwing 1S power board 0.1 V/A, commercial ESCs ≈ 12 mV/A: scale in firmware) |
| 4 | TLM | 100 Ω → PB0 (optional) |
| 5–8 | M1–M4 | 100 Ω → PA0–PA3 (TIM2 CH1–CH4) |

## ESC link B (J6, JST SH 8-pin, top side, front edge next to J5, pins at v = +14.85, mouth toward the front)
| Pin | Signal | FC side |
|---|---|---|
| 1 | GND | GND |
| 2 | VBAT | **not connected**: two ESC supplies are never tied together on the FC |
| 3 | CUR | not connected (current is measured on ESC A, or read per ESC over EDT) |
| 4 | TLM | not connected |
| 5–8 | M5–M8 | 100 Ω → PA8, PA9, PA10 (TIM1 CH1–CH3), PA6 (TIM16 CH1) |

The same 1:1 JST SH 8-pin cable fits both links. Check the pin order of any third-party ESC before plugging it in.

## Battery / power input pads (J7 VBAT+, J8 GND)
2 × 2 mm pads, top side, left edge. Same VBAT net as J2 pin 2: an alternative FC supply when the ESC has
no VBAT pin (separate ESCs with a PDB). FC current only (≤ 0.5 A at 4.1 V), no motor current. Use one supply source at
a time.

## Add-on boards (unchanged circuit, now two ports)
| Port | Position | Intended board | Bus addresses |
|---|---|---|---|
| J3 Qwiic | top, right edge, front (v = +2.8) | ACwing GPS (stacked above; its J1 sits right above J3) | GNSS 0x42, compass 0x1E |
| J4 Qwiic | top, right edge, rear (v = −5.3) | ACwing Flow (under the frame) | ToF 0x29, flow bridge 0x3B |

Both ports: 1 GND, 2 VEXP 3.3 V (LDK130, 300 mA, shared), 3 SDA, 4 SCL; 2.2 k pull-ups on the FC. The boards can still
daisy-chain through their own pass-through ports.

## Power summary
- VBAT 1S–6S (3.0–25.2 V; LM5166 abs. max 68 V, so ESC voltage spikes have margin) → U12 buck, PFM, 500 mA max →
  **VREG 4.1 V** (2S–6S). On 1S the buck runs at 100 % duty cycle: VREG ≈ VBAT − I × 1.1 Ω.
- USB-C: data, DFU and bench supply only (VBUS → D9 → VSYS; Q5 cuts VREG off while USB is present). No charger.
- VSYS → LDO U5 3.1 V (VDD), LDO U11 3.31 V (VEXP, Qwiic), VLED (LEDs, through D11), ELRS port.
