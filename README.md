# OAK-D Pro Raspberry Pi Streamer with IMU - v5.0

**Production-ready quad H.264 video streamer + IMU data** for Raspberry Pi 5 with OAK-D Pro camera.

Streams **RGB + Left + Right cameras + Depth map + IMU sensor data simultaneously** at full performance to PC over Ethernet.

## 🎯 v5.0 Enhancements

- **Stable 30 FPS**: Hard-limited frame rates for consistent performance
- **Optimized connection handling**: Prevents client connection overload
- **Improved resource management**: Better handling of multiple simultaneous clients
- **Enhanced telemetry**: Real-time FPS reporting for all streams

## 🌐 Ethernet Configuration (IMPORTANT)

For optimal streaming performance, configure ethernet interface:

```bash
# Set static IP for ethernet streaming
sudo ip addr add 192.168.1.201/24 dev eth0
```

**Network Setup:**
- **eth0**: 192.168.1.201 (streaming interface - optimal bandwidth)  
- **wlan0**: 192.168.1.202 (SSH/control access)

Streamer binds to 0.0.0.0 (all interfaces) but ethernet provides superior performance.

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

# 4. Run the streamer with explicit FPS limit
python quad_streamer_with_imu.py --fps 30
```

## Streams Available

The streamer provides 5 concurrent data streams:

- **Port 5000**: RGB Camera (H.264, 1920x1080 @ 30fps)
- **Port 5001**: Left Mono Camera (H.264, 1280x720 @ 30fps) 
- **Port 5002**: Right Mono Camera (H.264, 1280x720 @ 30fps)
- **Port 5003**: Depth Map (JPEG, 1280x720 @ 30fps)
- **Port 5004**: IMU Data (UDP, JSON, 100Hz)

## Performance

- **Total bandwidth**: ~14-15 Mbps (optimized from 25-30 Mbps)
- **FPS stability**: Locked 30 FPS across all video streams
- **CPU usage**: <35% on Raspberry Pi 5 with full stream load
- **Latency**: <50ms end-to-end with aggressive buffering
- **Connection limit**: Handles multiple clients per stream efficiently

## Technical Details

### Video Encoding
- **RGB**: H.264 baseline profile, 1920x1080 @ 30fps (8Mbps bitrate)
- **Stereo cameras**: H.264 baseline profile, 1280x720 @ 30fps (3Mbps bitrate)
- **Depth**: JPEG compressed depth maps with color encoding
- **Keyframe interval**: 15 frames for optimal seeking

### IMU Data Format
```json
{
  "timestamp": 1695123456789,
  "accelerometer": {"x": 0.12, "y": -9.81, "z": 0.03},
  "gyroscope": {"x": 0.001, "y": -0.002, "z": 0.005},
  "magnetometer": {"x": 25.4, "y": -12.1, "z": 45.2}
}
```

### Connection Management
The streamer now includes improved connection handling:
- Per-stream client tracking
- Automatic cleanup of disconnected clients
- Real-time FPS telemetry reporting
- Protection against connection flooding

## Command Line Options

```bash
# Run with custom FPS (default: 30)
python quad_streamer_with_imu.py --fps 30

# Run with custom resolution (future feature)
python quad_streamer_with_imu.py --rgb-width 1920 --rgb-height 1080
```

## Troubleshooting

### High CPU usage or degraded FPS
- Limit concurrent client connections
- Ensure using ethernet (not WiFi) for streaming
- Check for connection flooding from monitoring tools

### Connection refused errors
- Verify firewall settings allow ports 5000-5004
- Ensure Pi has correct IP configuration
- Check OAK-D Pro USB connection

## PC Receiver

For the corresponding PC receiver application with real-time FPS monitoring, see: [ivy_streamer_pc](https://github.com/rbivy/ivy_streamer_pc)

## Version History

- **v5.0**: FPS optimization and connection management improvements
- **v4.0**: Added IMU data streaming
- **v3.0**: Quad stream with depth support
- **v2.0**: Stereo camera support
- **v1.0**: Initial RGB streaming
EOF'
