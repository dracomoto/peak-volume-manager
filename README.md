# Peak Volume Manager

A real-time system audio compressor/limiter for Windows. Monitors your audio output and automatically reduces volume during spikes — like those annoyingly loud commercials — while keeping normal content at a comfortable level.

## How It Works

1. **Captures** system audio output via Windows WASAPI loopback (read-only, non-destructive)
2. **Analyzes** audio levels in real-time (RMS and peak detection)
3. **Compresses** by lowering system volume when levels spike above your threshold
4. **Recovers** smoothly when levels return to normal, based on your release time setting

The processing chain is: **Audio Capture → Compressor (threshold/ratio/knee) → Hard Limiter (ceiling) → Volume Adjustment**

## Requirements

- Windows 10 or 11
- Python 3.10 or later
- A WASAPI loopback audio source (see Audio Setup below)

## Installation

```bash
# Clone or download this folder, then:
cd peak-volume-manager
pip install -r requirements.txt
```

## Audio Setup (Important)

The app needs to "hear" your system audio output. There are three ways to enable this:

### Option 1: Enable Stereo Mix (Easiest)
1. Right-click the speaker icon in your taskbar → **Sound settings**
2. Scroll to **More sound settings** → **Recording** tab
3. Right-click in empty space → **Show Disabled Devices**
4. If **Stereo Mix** appears, right-click it → **Enable**

### Option 2: WASAPI Loopback (Automatic)
Many modern sound cards expose loopback devices automatically through WASAPI. The app will detect these.

### Option 3: VB-Audio Virtual Cable (Guaranteed)
1. Download and install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) (free)
2. Set your Windows default playback device to the Virtual Cable
3. The app will capture from the Virtual Cable input

### Simulation Mode
If no capture device is found, the app runs in **simulation mode** with synthetic audio data. This lets you explore the UI and configure settings before setting up audio capture.

## Usage

```bash
python main.py
```

### Controls

| Control | What It Does |
|---------|-------------|
| **Enable/Disable** | Master toggle — bypasses all processing |
| **Threshold** | dB level where compression kicks in. Lower = catches more. |
| **Ratio** | How aggressively volume is reduced above threshold. 4:1 means a 4 dB spike becomes 1 dB. |
| **Attack** | How fast compression kicks in (milliseconds). Lower = faster response. |
| **Release** | How fast volume recovers when levels drop (milliseconds). |
| **Knee** | Smooth (high) vs. hard (low) transition into compression. |
| **Ceiling** | Absolute maximum output level — hard limiter. Nothing gets louder than this. |
| **Output Gain** | Offset to raise or lower overall volume after processing. |

### Presets

- **Light** — Gentle smoothing. Good for minor volume differences.
- **Moderate** — Balanced compression. Good starting point for most use.
- **Aggressive** — Heavy compression. Flattens commercials hard.

### Tips for Tuning

1. Start with the **Moderate** preset
2. Watch the level history graph — you'll see input (blue) and output (green)
3. When a commercial hits, the blue line spikes; the green line should stay flat
4. If commercials are still too loud: lower the **threshold** or raise the **ratio**
5. If normal content sounds "pumpy" or unnatural: raise the **threshold** or increase **release** time
6. The **ceiling** is your safety net — set it to the loudest you ever want your audio to be

## System Tray

- Click **Minimize to Tray** or close the window to send it to the system tray
- Double-click the tray icon to restore the window
- Right-click the tray icon for quick enable/disable/quit

## Settings

Settings are saved automatically to `settings.json` in the app directory and persist between sessions.

## File Structure

```
peak-volume-manager/
├── main.py              — Entry point
├── audio_monitor.py     — WASAPI capture and level analysis
├── volume_controller.py — Windows system volume control (pycaw)
├── compressor.py        — DSP: threshold/ratio/attack/release/limiter logic
├── presets.py           — Preset definitions and control ranges
├── settings.py          — JSON config load/save
├── requirements.txt     — Python dependencies
├── gui/
│   ├── main_window.py   — Main application window
│   ├── meters.py        — Level meter widgets
│   ├── graph.py         — Real-time scrolling level history
│   ├── controls.py      — Parameter sliders and preset selector
│   └── tray.py          — System tray icon and menu
└── settings.json        — Auto-generated user config
```

## Known Limitations (Beta)

- **Reaction time**: There's a small inherent delay (capture + analysis + volume adjustment). With a 3ms attack, it catches spikes within the first moment, but the very first transient may pass through.
- **System-wide**: Affects all audio, not per-application. Per-app control is planned for v2.
- **Windows only**: Uses Windows-specific APIs (WASAPI, Core Audio).
- **No per-site profiles**: One global configuration. Per-site/per-app profiles planned for v2.
