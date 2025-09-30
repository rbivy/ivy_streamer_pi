# OAK-D Pro Raspberry Pi Streamer with IMU - v6.0 (SLAM-Optimized)

**SLAM-ready quad H.264 video streamer + IMU data** for Raspberry Pi 5 with OAK-D Pro camera.

Streams **RGB + Left + Right cameras + Raw 16-bit Depth + High-frequency IMU data simultaneously** with synchronized timestamps for professional SLAM and visual odometry applications.

## 🎯 v6.0 SLAM Enhancements

- **Raw 16-bit depth streaming**: Metric depth data in millimeters for precise 3D reconstruction
- **H.264 HIGH profile**: Superior video quality with reduced compression artifacts
- **200Hz IMU frequency**: High-precision motion tracking for dynamic scenarios
- **Synchronized timestamps**: Common time reference across all sensor streams
- **Optimized for SLAM**: Professional-grade data streams for computer vision

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

# 4. Run the SLAM-optimized streamer
python quad_streamer_with_imu.py --fps 30
```

## Streams Available (SLAM-Optimized)

The streamer provides 5 concurrent SLAM-ready data streams:

- **Port 5000**: RGB Camera (H.264 HIGH, 1920x1080 @ 30fps, 10Mbps)
- **Port 5001**: Left Mono Camera (H.264 HIGH, 1280x720 @ 30fps, 4Mbps) 
- **Port 5002**: Right Mono Camera (H.264 HIGH, 1280x720 @ 30fps, 4Mbps)
- **Port 5003**: **Raw 16-bit Depth** (millimeter precision, 1280x720 @ 30fps)
- **Port 5004**: **IMU Data** (UDP, JSON, **200Hz**, synchronized timestamps)

## Performance (SLAM-Optimized)

- **Total bandwidth**: ~18-20 Mbps (increased for HIGH profile quality)
- **FPS stability**: Locked 30 FPS across all video streams
- **IMU frequency**: 200Hz for high-precision motion tracking
- **CPU usage**: ~40% on Raspberry Pi 5 with full stream load
- **Latency**: <50ms end-to-end with aggressive buffering
- **Timestamp sync**: Nanosecond precision for sensor fusion

## Technical Details

### Video Encoding (SLAM-Optimized)
- **RGB**: H.264 **HIGH profile**, 1920x1080 @ 30fps (10Mbps bitrate)
- **Stereo cameras**: H.264 **HIGH profile**, 1280x720 @ 30fps (4Mbps bitrate)
- **Depth**: **Raw 16-bit data** with header (width, height, itemsize, timestamp)
- **Keyframe interval**: 15 frames for optimal seeking

### Raw Depth Data Format
```
Header: [width: 4 bytes][height: 4 bytes][itemsize: 2 bytes][timestamp_ns: 8 bytes]
Data: [raw uint16 depth values in millimeters]
```

### IMU Data Format (Synchronized)
```json
{
  "timestamp": 1695123456.789123,
  "accelerometer": {"x": 0.12, "y": -9.81, "z": 0.03, "timestamp": 1695123456.789123},
  "gyroscope": {"x": 0.001, "y": -0.002, "z": 0.005, "timestamp": 1695123456.789123}
}
```

### SLAM Synchronization
- **Unified timestamps**: All streams use synchronized host timestamps
- **Temporal correlation**: Depth and IMU data share common time reference
- **High frequency**: 200Hz IMU for dynamic motion scenarios
- **Precision**: Nanosecond timestamp resolution for accurate sensor fusion

## Command Line Options

```bash
# Run with custom FPS (default: 30)
python quad_streamer_with_imu.py --fps 30

# Run with custom resolution (future feature)
python quad_streamer_with_imu.py --rgb-width 1920 --rgb-height 1080
```

## SLAM Applications

This streamer is optimized for:
- **Visual SLAM**: High-quality stereo vision with reduced artifacts
- **Visual-Inertial Odometry**: Synchronized 200Hz IMU with visual data
- **Dense 3D Reconstruction**: Raw millimeter-precision depth data
- **Real-time Mapping**: Low-latency synchronized sensor streams

## Troubleshooting

### High CPU usage or degraded FPS
- Limit concurrent client connections
- Ensure using ethernet (not WiFi) for streaming
- Check for connection flooding from monitoring tools

### Raw depth data issues
- Verify PC receiver handles 16-bit depth format
- Check header parsing (20-byte header + depth data)
- Ensure proper byte order (big-endian)

### IMU synchronization issues
- Verify timestamp format (seconds with decimal precision)
- Check 200Hz data rate in receiver
- Ensure UDP port 5004 is accessible

## PC Receiver

For the corresponding SLAM-ready PC receiver application, see: [ivy_streamer_pc](https://github.com/rbivy/ivy_streamer_pc)

## Version History

- **v6.0**: SLAM optimization release (CURRENT)
  - Raw 16-bit depth streaming for metric reconstruction
  - H.264 HIGH profile for superior video quality
  - 200Hz IMU frequency for precise motion tracking
  - Synchronized timestamps across all sensor streams
- **v5.0**: FPS optimization and connection management improvements
- **v4.0**: Added IMU data streaming
- **v3.0**: Quad stream with depth support
- **v2.0**: Stereo camera support
- **v1.0**: Initial RGB streaming
