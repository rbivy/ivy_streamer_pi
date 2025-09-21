# OAK-D Pro Raspberry Pi Streamer

Triple H.264 video streamer for Raspberry Pi - RGB + Left + Right cameras simultaneously.

## Quick Setup

```bash
# Clone this repository
git clone https://github.com/rbivy/ivy_streamer_pi.git
cd ivy_streamer_pi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the streamer
python triple_streamer.py
```

## Quick Start Script

For convenience, use the automated script:
```bash
./start_triple.sh
```

## Configuration

Default settings:
- RGB: Port 5000, 1920x1080 @ 30fps
- Left: Port 5001, 1280x720 @ 30fps
- Right: Port 5002, 1280x720 @ 30fps

Customize with command line arguments:
```bash
python triple_streamer.py --rgb-width 1280 --rgb-height 720 --fps 15
```

## Files

- `triple_streamer.py` - Main streaming application
- `start_triple.sh` - Automated startup script
- `requirements.txt` - Python dependencies
- `ssh_pi_robust.sh` - SSH helper script
- `venv/` - Virtual environment (created locally)

## Network Requirements

- TCP ports 5000, 5001, 5002
- ~14 Mbps total bandwidth for full resolution
- Connected to same network as PC receiver

## Troubleshooting

- **"No available devices"**: Check USB connection and udev rules
- **"X_LINK_DEVICE_ALREADY_IN_USE"**: Kill existing processes, unplug/replug camera
- **Poor performance**: Reduce resolution or FPS