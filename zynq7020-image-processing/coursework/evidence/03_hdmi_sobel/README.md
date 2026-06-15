# Experiment 2 HDMI Sobel Remote Evidence

## Run Information

- Date: 2026-06-15
- Branch: `exp/02-hdmi-sobel`
- Tool: Vivado/XSim 2023.2
- Device: `xc7z020clg400-2`
- Default threshold: `80`
- Status: remote simulation and build passed; physical HDMI verification pending

## Commands

```powershell
cd zynq7020-image-processing\sobel_02_hdmi_sobel
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp02_sim.tcl
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp02_bitstream.tcl
```

## Simulation

XSim printed `HDMI Sobel full-chain simulation passed` and
`EXP02_SIM=passed`.

- Grayscale samples checked: `9216`
- Sobel writes checked: `9216`, exactly once per address
- `edge_frame_done`: one pulse
- HDMI timing, active-pixel count, scaling, and threshold-80 binary RGB: passed

## Threshold Comparison

| Threshold | White source pixels |
| ---: | ---: |
| 40 | 1307 |
| 80 | 1274 |
| 120 | 1234 |

The self-check confirmed that the count is monotonic non-increasing as the
threshold rises. Each source pixel is displayed as a `10 x 10` block on the
1280 x 720 output.

## Build Results

- Synthesis, placement, routing, and bitstream generation: passed
- WNS: `1.578 ns`
- TNS: `0.000 ns`
- WHS: `0.080 ns`
- THS: `0.000 ns`
- LUT: `2842`
- FF: `2353`
- BRAM36: `14`
- DSP: `0`
- MMCM: `1`
- OSERDES: `8`
- DRC: `0` errors, `1` warning

The remaining `ZPS7-1` warning is expected because this experiment is a
pure-PL HDMI design and intentionally does not instantiate PS7. Bitstream
generation completed successfully despite that warning.

Vivado also reported sandbox-local Tcl/WebTalk settings warnings. They affect
only user settings/telemetry files and did not affect simulation, routing,
reports, or bitstream generation.

## Files

| File | Purpose |
| --- | --- |
| `exp02_edge_strength.png` | Raw 8-bit Sobel strength, scaled to 1280 x 720 |
| `exp02_threshold_40.png` | Expected binary HDMI output at threshold 40 |
| `exp02_threshold_80.png` | Default on-site comparison image |
| `exp02_threshold_120.png` | Expected binary HDMI output at threshold 120 |
| `exp02_threshold_stats.txt` | White-pixel counts and monotonic self-check |
| `exp02_simulation.txt` | Concise XSim result |
| `exp02_remote_build.txt` | Concise implementation and bitstream result |
| `exp02_utilization.txt` | Vivado utilization report |
| `exp02_timing_summary.txt` | Vivado timing report |
| `exp02_drc.txt` | Vivado DRC report |

The generated `top.bit` remains in the ignored local build directory and is
not committed.

## Pending On-Site Evidence

- Actual branch and commit tested
- Board model, Vivado version, display model, and test date
- Hardware Manager target/programming log or screenshot
- HDMI photo matching `exp02_threshold_80.png`
- Photo showing board, JTAG, and HDMI connections
- Confirmation that 1280 x 720 remained stable for at least 30 seconds
