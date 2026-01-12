# CSV OSC Player & Recorder

A Python application for playing and recording OSC (Open Sound Control) messages using CSV files.

![Screenshot](/Screenshot_OSC2CSV.png)

## Features

### Playback
- Reads CSV files with timestamp-based OSC events
- Automatic type detection (int, float, string, boolean) for OSC arguments
- Timed playback synchronized to CSV timestamps
- Supports messages with no arguments (empty messages)
- Full precision float handling (no rounding)

### Recording
- Records incoming OSC messages to CSV files
- Timestamps start at 0.0 when recording begins
- Preserves all value types (int, float, string, boolean, empty)
- Configurable recording name/prefix for filenames
- Automatic file naming with date and time

### Control
- OSC control interface for start/stop commands
- Configurable destination IP and port
- **GUI version available** for easy operation

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## CSV Format

The CSV file should have the following format:
```
timestamp, osc_address, value
```

**Columns:**
1. **timestamp** - Time in seconds (float) when the OSC message should be sent
2. **osc_address** - The OSC address path (e.g., `/test/parameter`)
3. **value** - The value to send (automatically detected as int or float)

**Example CSV:**
```csv
0.0, /test/int, 42
1.5, /test/float, 3.14
2.0, /test/int, 100
3.25, /another/param, 255
```

## Usage

### GUI Version (Recommended)

For an easy-to-use graphical interface:

```bash
python csv_osc_player_gui.py
```

The GUI allows you to:
- **Playback:**
  - Browse and select CSV files
  - Configure OSC destination IP and port
  - Start/stop playback with buttons
  - View real-time status and log messages
- **Recording:**
  - Set recording name/prefix (e.g., "agat", "test", etc.)
  - Configure listen IP and port for incoming OSC messages
  - Select output directory for recorded CSV files
  - Start/stop recording with buttons
  - View recorded messages in real-time
- **Control:**
  - Still accepts OSC control commands (see Control Commands section below)

### Command Line Version

For basic usage:

```bash
python csv_osc_player.py example.csv
```

With custom settings:

```bash
python csv_osc_player.py example.csv --osc-ip 192.168.1.100 --osc-port 9000 --control-port 8000
```

### Command Line Arguments

- `csv_file` - Path to the CSV file (required)
- `--osc-ip` - Destination IP address for OSC messages (default: 127.0.0.1)
- `--osc-port` - Destination port for OSC messages (default: 8001)
- `--control-port` - Port for OSC control server (default: 8000)

---

## 🎮 Control Commands

### Playback Control

The player listens for OSC control commands on `127.0.0.1:8000` (or your specified control port):

| Command | Address | Value | Action |
|---------|---------|-------|--------|
| **Start playback** | `/playbackcsv` | `1` | Starts CSV playback |
| **Stop playback** | `/playbackcsv` | `0` | Stops CSV playback |

#### Example: Using `oscsend` (from liblo-tools on Linux/Mac)
```bash
# Start playback
oscsend localhost 8000 /playbackcsv i 1

# Stop playback
oscsend localhost 8000 /playbackcsv i 0
```

#### Example: Using Python
```python
from pythonosc import udp_client
client = udp_client.SimpleUDPClient("127.0.0.1", 8000)
client.send_message("/playbackcsv", 1)  # Start
client.send_message("/playbackcsv", 0)  # Stop
```

### Recording Control

The recorder listens for OSC control commands on the configured listen port (default: `127.0.0.1:8002`):

| Command | Address | Value | Action |
|---------|---------|-------|--------|
| **Start recording** | `/recordcsv` | `1` | Starts OSC recording |
| **Stop recording** | `/recordcsv` | `0` | Stops OSC recording |

#### Example: Using `oscsend`
```bash
# Start recording
oscsend localhost 8002 /recordcsv i 1

# Stop recording
oscsend localhost 8002 /recordcsv i 0
```

#### Example: Using Python
```python
from pythonosc import udp_client
client = udp_client.SimpleUDPClient("127.0.0.1", 8002)
client.send_message("/recordcsv", 1)  # Start recording
client.send_message("/recordcsv", 0)  # Stop recording
```

---

## Recording Features

The OSC recorder (`osc_recorder.py`) can be used standalone or through the GUI:

### CSV File Format

Recorded CSV files follow this format:
```csv
# RECORDING_NAME OSC Recording
# Started: Thu Jan  8 19:32:59 2026
# Format: timestamp,address,value
time,address,value
0.000,/osc/address1,42
0.123,/osc/address2,3.14159
1.456,/osc/address3,hello
2.789,/osc/address4,true

# Duration: 10.5 seconds
```

**Key points:**
- First 4 rows are header information (skipped during playback)
- Timestamps are relative (start at 0.0)
- Values preserve their type (int, float, string, boolean, empty)
- Filename format: `{recording_name}_{YYMMDD}_{HHMMSS}.csv`

### Supported Value Types

The recorder and player handle these OSC value types:
- **Integers:** `42`, `-10`, `0`
- **Floats:** `3.14159`, `1.5e-10`, `0.0`
- **Strings:** `"hello"`, `"test"`, any text
- **Booleans:** `true`, `false`
- **Empty/None:** No arguments (empty value in CSV)

---

## How It Works

### Playback
1. The script loads the CSV file and parses all events
2. The first timestamp becomes time 0.0 (baseline)
3. All subsequent events are scheduled relative to the first timestamp
4. When playback starts, events are sent at the correct times
5. The script maintains an OSC server to listen for control commands

### Recording
1. Start recording (via GUI or OSC command)
2. OSC server listens for incoming messages on the specified port
3. Each message is timestamped relative to recording start (0.0)
4. Messages are immediately written to CSV file
5. Stop recording saves the file with duration information

## How It Works

1. The script loads the CSV file and parses all events
2. The first timestamp becomes time 0.0 (baseline)
3. All subsequent events are scheduled relative to the first timestamp
4. When playback starts, events are sent at the correct times
5. The script maintains an OSC server to listen for control commands

## Type Detection

The player automatically detects value types when reading CSV files:
- **Booleans:** Values matching `true` or `false` (case-insensitive)
- **Numbers:** Parsed as integers or floats based on format
  - Contains decimal point, 'e', or 'E' → float
  - Otherwise → integer
- **Strings:** Everything else is treated as a string
- **Empty:** Blank values are treated as empty arguments

The recorder preserves the exact type of incoming OSC messages:
- Type information is maintained when writing to CSV
- Float precision is preserved using `repr()` for accurate representation

## Technical Details

### Default Ports
- **Playback Control:** 8000 (for `/playbackcsv` commands)
- **OSC Playback:** 8001 (where playback sends OSC messages)
- **Recording Listen:** 8002 (where recorder listens for incoming OSC)

All ports are configurable in the GUI or via command-line arguments.

### File Format Notes
- CSV files skip the first 4 rows (header information)
- Timestamps use 6 decimal places (microsecond precision)
- All value types are preserved and correctly restored during playback

## Notes

- Timestamps are relative to the first timestamp in the file (playback) or recording start (recording)
- Playback and recording can be controlled via GUI buttons or OSC commands
- Multiple recordings can be made with different names/prefixes
- The GUI runs until closed; command-line version runs until interrupted (Ctrl+C)

