# Hardware Monitor

Real-time system monitoring dashboard for your terminal. Beautiful, colorful, live-updating.

![screenshot](https://img.shields.io/badge/platform-windows-blue)

## Features

- **CPU** — Overall usage + per-core breakdown with color-coded bars
- **Memory** — RAM and Swap usage with live bars
- **Disks** — All drives with usage percentage
- **Network** — Real-time download/upload speed
- **Top Processes** — Sorted by CPU usage (top 8)
- **System Info** — Hostname, uptime, boot time
- **Color Codes** — Green (< 50%), Yellow (50-80%), Red (> 80%)

## Installation

```bash
pip install psutil rich
```

## Usage

```bash
python hardware_monitor.py
```

## Requirements

- Python 3.8+
- psutil
- rich

## How It Looks

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃    Hardware Monitor    DESKTOP-PC    up 2h 34m 12s    14:32:05             ┃
┃                                                                             ┃
┃  ┌─ Processor ─────────────────────┐  ┌─ Network ─────────────────────────┐ ┃
┃  │ CPU  ████████████░░░░░░  55.2%  │  │ ↓ DL  2.4 MB/s                   │ ┃
┃  │ Cores  32%  45%  78%  22%       │  │ ↑ UL  1.1 MB/s                   │ ┃
┃  └─────────────────────────────────┘  └───────────────────────────────────┘ ┃
┃  ┌─ Memory ─────────────────────────┐  ┌─ Top Processes ──────────────────┐ ┃
┃  │ RAM  ██████████████░░░░  68.4%   │  │ PID   Name              CPU% MEM%┃ ┃
┃  │      6.8/16.0 GB                 │  │ 4524  chrome.exe         12.3 8.5 ┃
┃  │ SWP  ██░░░░░░░░░░░░░░  12.0%    │  │ 1232  python.exe          5.1 2.3 ┃
┃  └─────────────────────────────────┘  │  ...                             │ ┃
┃  ┌─ Disks ──────────────────────────┐ └───────────────────────────────────┘ ┃
┃  │ C:  ████████████████████  92.3%  │                                      ┃
┃  │ D:  ██████░░░░░░░░░░░░░  30.0%  │                                      ┃
┃  └─────────────────────────────────┘                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘
```

## License

MIT
