# OAK-D Pro Raspberry Pi Streamer

**Production-ready triple H.264 video streamer** for Raspberry Pi 5 with OAK-D Pro camera.

Streams **RGB + Left + Right cameras simultaneously** at full 30fps to PC over Ethernet.

## Quick Setup

```bash
# 1. Clone this repository (Pi only)
git clone https://github.com/rbivy/ivy_streamer_pi.git
cd ivy_streamer_pi

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Connect OAK-D Pro via USB3

# 5. Start streaming
python triple_streamer.py
```

## One-Command Start

Use the convenience script for automated startup:
```bash
./start_triple.sh
```

This script:
- Activates virtual environment automatically
- Kills any existing streamers
- Starts triple streamer in background
- Shows status and connection info

## Stream Configuration

**Default settings** (optimal for most use cases):
- **RGB**: Port 5000, 1920x1080 @ 30fps (~8 Mbps)
- **Left**: Port 5001, 1280x720 @ 30fps (~3 Mbps)
- **Right**: Port 5002, 1280x720 @ 30fps (~3 Mbps)
- **Total bandwidth**: ~14 Mbps

**Custom resolution/FPS** for bandwidth optimization:
```bash
python triple_streamer.py --rgb-width 1280 --rgb-height 720 --mono-width 640 --mono-height 480 --fps 15
```

## Files in this Repository

- `triple_streamer.py` - Main streaming application
- `start_triple.sh` - One-command startup script
- `requirements.txt` - Python dependencies (depthai, numpy)
- `README.md` - This documentation
- `venv/` - Virtual environment (created locally, never committed)

## Network Requirements

- **Ethernet connection recommended** (WiFi works but may have latency)
- **Firewall**: Allow TCP ports 5000, 5001, 5002
- **Same network** as PC receiver
- **Router QoS**: Prioritize video traffic if possible

## Troubleshooting

### "No available devices" Error
```bash
# Check USB connection
lsusb | grep Movidius

# Fix udev rules (if needed)
sudo usermod -a -G plugdev $USER
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' | sudo tee /etc/udev/rules.d/80-movidius.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### "X_LINK_DEVICE_ALREADY_IN_USE" Error
```bash
# Kill existing processes
pkill -f triple_streamer

# If persistent, physically disconnect and reconnect OAK-D Pro
```

### Performance Issues
- Reduce resolution: `--rgb-width 1280 --rgb-height 720`
- Lower FPS: `--fps 15`
- Check CPU usage: `htop`
- Ensure adequate power supply (5V 3A+ recommended)

### Connection Issues
```bash
# Test network connectivity
ping <PC_IP_ADDRESS>

# Check if ports are accessible from PC
# (Run this on PC):
nc -zv <PI_IP_ADDRESS> 5000 5001 5002
```

## Performance Notes

- **DepthAI v3.0**: Optimized for device management
- **H.264 hardware encoding**: Efficient bandwidth usage
- **Keyframe frequency**: 30 frames (1 second) for quick recovery
- **TCP streaming**: Reliable delivery with error correction
- **Multi-threaded**: Separate threads per camera stream

## Related Repositories

- **PC Receivers**: https://github.com/rbivy/ivy_streamer_pc
- **GStreamer-based** receivers with real-time overlays and telemetry

## System Requirements

- Raspberry Pi 5 (recommended) or Pi 4
- OAK-D Pro camera (USB3 connection)
- Python 3.8+
- 4GB+ RAM recommended
- Fast SD card (Class 10 or better)

## Version History

- **v1.0**: Initial release with triple stream support
- Uses proven DepthAI patterns for stability
- Production-tested with 24/7 operation capability