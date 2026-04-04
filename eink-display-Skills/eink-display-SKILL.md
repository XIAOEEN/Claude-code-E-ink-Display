---
name: eink-display
description: "E-Ink BLE Display integration for Claude Code. Send notifications, task completions, and heartbeat messages to a tri-color e-ink display (black/white/red). Use when user says \"墨水屏\", \"eink\", \"display\", or when sending notifications to physical display. Includes heartbeat (heartbit) feature for idle love messages."
argument-hint: [message-text]
allowed-tools: Bash(python3 *), Bash(grep *), Read, Glob
---
# E-Ink Display Integration

Send notifications to a tri-color E-Ink BLE display (400x300 pixels, black/white/red).

## Overview

This skill enables Claude Code to communicate with E-Ink displays via Bluetooth Low Energy (BLE). It supports:

- **Task notifications**: Send completion messages after tasks finish
- **Heartbeat (heartbit)**: When idle for 1 hour, display rotating love messages in English
- **Tri-color display**: Black text, white background, red accents
- **Auto text wrapping**: Long messages are automatically wrapped to fit the display
- **Dynamic font sizing**: Font size adjusts based on content length (20-32px)
- **Centered alignment**: All text is centered for optimal display

## Hardware Setup

### Supported Models

-  (4.2" tri-color e-ink, 400x300 pixels) - Verified working

- Other EPD-nRF5 based displays with similar BLE protocol

### Connection Steps

1. **Enable Bluetooth** on your Mac
2. **Power on the E-Ink display** and put it in BLE advertising mode
3. **Find the device address**:
   ```bash
   python3 -c "import asyncio; from bleak import BleakScanner; asyncio.run(BleakScanner.discover())"
   ```

   Look for device name like "NRF_EPD_EEA2" or similar
4. **Note the BLE address** (format: `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`)

## Installation

### 1. Install Dependencies

```bash
pip install bleak pillow numpy
```

### 2. Install Chinese Fonts (Optional, for Chinese text display)

```bash
brew install --cask font-noto-sans-cjk-sc
```

### 3. Configure Device Address

Edit the `eink_final.py` file to set your device address:

```python
DEVICE_ADDRESS = "YOUR_DEVICE_ADDRESS_HERE"
```

Or create a config file at `~/.claude/eink-config.json`:

```json
{
  "device_address": "YOUR_DEVICE_ADDRESS_HERE",
  "write_char_uuid": "62750002-d828-918d-fb46-b6c11c675aec",
  "enabled": true,
  "heartbit_enabled": true,
  "heartbit_interval_minutes": 60
}
```

## File Structure

```
~/.claude/skills/eink-display/
├── SKILL.md           # This file
└── eink_final.py      # Main display driver script
```

## Usage

### Quick Start

```bash
cd ~/.claude/skills/eink-display
python3 eink_final.py
```

### Send a Notification

```python
import asyncio
from eink_final import notify

async def main():
    await notify(message="Your message here", task_name="Task Name")

asyncio.run(main())
```

### Send Heartbit (Love Message)

```python
import asyncio
from eink_final import heartbit

async def main():
    await heartbit()

asyncio.run(main())
```

### Direct Display Control

```python
import asyncio
from eink_final import EInkDisplay, draw_message

async def main():
    display = EInkDisplay()
    await display.connect()
    await display.clear()

    bg, red = draw_message(
        message="Hello World!\nLine 2",
        task_name="My Task"
    )
    await display.show(bg, red)
    await display.disconnect()

asyncio.run(main())
```

## Display Layout

```
┌──────────────────────────────────────┐
│ 10:30          Claude Code      ●     │  ← Header (time left, task right)
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│  ← Red line (width 4px, 20px margin)
│                                      │
│         Centered Message Content      │  ← Content Area (auto-wrap, auto font size)
│                                      │
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│  ← Red line
│ April 4, 2026          MiniMax-M2.7 │  ← Footer (date left, model right)
└──────────────────────────────────────┘
```

### Layout Specifications


| Element      | Position      | Font              | Color           |
| ------------ | ------------- | ----------------- | --------------- |
| Time (HH:MM) | Top-left      | Bold Italic 16px  | Black           |
| Task name    | Top-right     | Bold Italic 16px  | Black           |
| Red lines    | Header/Footer | -                 | Red (width 4px) |
| Content      | Center        | Auto size 20-32px | Black           |
| Date         | Bottom-left   | Bold Italic 16px  | Black           |
| Model name   | Bottom-right  | Bold Italic 16px  | Red             |

## Heartbit (Heartbeat Love Messages)

When `heartbit_enabled` is true and no tasks have run for 1 hour, the display automatically shows a love message from a rotating list.

### Features

- **Auto text wrapping**: Long messages are automatically wrapped to fit the display
- **Dynamic font sizing**: Font size adjusts based on content length (20-32px)
- **Centered alignment**: All text is centered for optimal display

### Sample Love Messages

```
"You are my today, and all of my tomorrows. I love you more than words can ever say."
"Every moment with you is precious. You make my heart skip a beat every single time."
"I am thinking of you right now, and my love for you grows stronger each day."
"You are the sunshine in my life, the reason I believe in true love."
"My heart is perfect because you are inside. I fall in love with you every day."
"You are my favorite hello and my hardest goodbye. Forever isn't long enough with you."
"In all the world, you are my everything. You are my greatest adventure."
"Being with you is the best thing that ever happened to me. I cherish you always."
"Your smile lights up my world. Every day with you is a gift I treasure."
"I didn't know love could be this perfect until I met you, my darling."
```

## API Reference

### Functions

#### `notify(message, task_name="Claude Code")`

Send a notification to the display.

```python
await notify(message="Task completed!", task_name="Training")
```

#### `heartbit()`

Send a random love message to the display.

```python
await heartbit()
```

#### `EInkDisplay`

Class for direct display control.

```python
display = EInkDisplay(address="DEVICE_ADDRESS")
await display.connect()
await display.clear()
await display.show(bg_img, red_img=None)
await display.disconnect()
```

#### `draw_message(message, task_name, model_name)`

Draw a message layout and return bg/red image layers.

```python
bg, red = draw_message(
    message="Your message",
    task_name="Task Name",
    model_name="gpt-4o"
)
```

## Troubleshooting

### Device Not Found

- Ensure the E-Ink display is powered on and in pairing mode
- Check if Bluetooth is enabled on your Mac
- Try running: `python3 -c "import asyncio; from bleak import BleakScanner; asyncio.run(BleakScanner.discover())"`

### Connection Timeout

- Move closer to the display
- Ensure no other device is connected to the display
- Try disconnecting and reconnecting

### Chinese Font Not Displaying

- Install Noto Sans CJK: `brew install --cask font-noto-sans-cjk-sc`
- Restart the script

## Example Workflows

### 1. Task Completion Notification

```
User: Run the training script
Assistant: [runs training]
Assistant: Training complete! Now sending notification to e-ink display...
await notify(message="Training Complete\nAccuracy: 97.8%", task_name="ResNet18 Training")
[Screen shows the completion message]
```

### 2. Manual Display Update

```
User: Show "Hello World" on the display
Assistant: [calls notify with the message]
```

### 3. Send Heartbit

```
Assistant: Sending a love message to your e-ink display...
await heartbit()
[Screen shows a random love message]
```

### 4. Check Display Connection

```
Assistant: Let me verify the display connection...
python3 ~/.claude/skills/eink-display/eink_final.py
[Screen shows test message]
```
