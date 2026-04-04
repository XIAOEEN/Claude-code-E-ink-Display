# Claude-code-E-ink-Display

![](./e-ink.jpg)

E-Ink BLE Display integration for Claude Code - Send notifications and heartbeat messages to a tri-color e-ink display.

## Overview

This skill enables Claude Code to communicate with E-Ink displays via Bluetooth Low Energy (BLE). It supports:

- **Task notifications**: Send completion messages after tasks finish
- **Heartbeat (heartbit)**: When idle, display rotating love messages in English
- **Tri-color display**: Black text, white background, red accents
- **Auto text wrapping**: Long messages are automatically wrapped
- **Dynamic font sizing**: Font size adjusts based on content length

## Hardware

- **Model**: NRF_EPD_EEA2 (4.2" tri-color e-ink)
- **Resolution**: 400x300 pixels
- **Colors**: Black, White, Red

## Installation

```bash
# Install dependencies
pip install bleak pillow numpy

# Install Chinese fonts (optional)
brew install --cask font-noto-sans-cjk-sc
```

## Usage

```python
from eink_final import notify, heartbit

# Send notification
await notify(message="Task completed!", task_name="Claude Code")

# Send heartbit (love message)
await heartbit()
```

## Display Layout

```
┌──────────────────────────────────────┐
│ 10:30          Claude Code           │  ← Header
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│  ← Red line
│                                      │
│         Centered Message Content     │  ← Content
│                                      │
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│  ← Red line
│ April 4, 2026          MiniMax-M2.7 │  ← Footer
└──────────────────────────────────────┘
```

## Configuration

Create `~/.claude/eink-config.json`:

```json
{
  "device_address": "YOUR_DEVICE_ADDRESS",
  "write_char_uuid": "62750002-d828-918d-fb46-b6c11c675aec",
  "enabled": true,
  "heartbit_enabled": true,
  "heartbit_interval_minutes": 60
}
```

## Heartbit Messages

Sample love messages:

- "You are my today, and all of my tomorrows. I love you more than words can ever say."
- "Every moment with you is precious. You make my heart skip a beat every single time."
- "You are the sunshine in my life, the reason I believe in true love."
