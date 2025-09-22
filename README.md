# OAK-D Pro Raspberry Pi Streamer with IMU

**Production-ready quad H.264 video streamer + IMU data** for Raspberry Pi 5 with OAK-D Pro camera.

Streams **RGB + Left + Right cameras + Depth map + IMU sensor data simultaneously** at full performance to PC over Ethernet.

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

# 5. Start quad streaming with IMU
python quad_streamer_with_imu.py
```

## Streaming Features

**Video Streams** (TCP H.264/JPEG):
- **RGB**: Port 5000, 1280x720 @ 30fps (~8 Mbps)
- **Left Mono**: Port 5001, 1280x720 @ 30fps (~3 Mbps)
- **Right Mono**: Port 5002, 1280x720 @ 30fps (~3 Mbps)
- **Depth**: Port 5003, 1280x720 @ 30fps (JPEG encoded)

**IMU Data Stream** (UDP JSON):
- **IMU**: Port 5004, Accelerometer + Gyroscope @ 100Hz
- **Low latency**: UDP protocol optimized for sensor data
- **JSON format**: Easy parsing with timestamps
- **High precision**: 3-axis acceleration and rotation data

**Total bandwidth**: ~14 Mbps + minimal IMU data

## Available Streamers

### Quad Streamer with IMU (Recommended)
```bash
python quad_streamer_with_imu.py
```
- **5 simultaneous data streams**: 4 video + 1 sensor
- **IMU integration**: Real-time accelerometer and gyroscope
- **Stereo depth**: Real-time depth map computation
- **Production-ready**: Optimized for 24/7 operation

### Legacy Quad Streamer (Video Only)
```bash
python quad_streamer.py
```
- **4 video streams**: RGB + Left + Right + Depth
- **No IMU data**: Video-only mode

## Stream Configuration

**Default settings** (optimal for most use cases):
- **Uniform resolution**: 1280x720 across all cameras
- **High detail depth**: Stereo computation with HIGH_DETAIL preset
- **Hardware acceleration**: H.264 encoding for video streams
- **Efficient depth**: JPEG compression for depth maps
- **High-rate IMU**: 100Hz sensor data streaming

**Custom configuration**:
```bash
python quad_streamer_with_imu.py --fps 15  # Lower frame rate if needed
```

## Files in this Repository

### Main Streamers
- `quad_streamer_with_imu.py` - **Complete streaming application** (4 video + IMU)
- `quad_streamer.py` - Legacy video-only quad streamer

### Configuration
- `requirements.txt` - Python dependencies (depthai, numpy, opencv)
- `README.md` - This documentation
- `venv/` - Virtual environment (created locally, never committed)

## Network Requirements

- **Ethernet connection strongly recommended** (WiFi may cause frame drops)
- **Firewall**: Allow TCP ports 5000-5003, UDP port 5004
- **Same network** as PC receiver
- **Quality of Service**: Prioritize video traffic if available
- **Bandwidth**: 15+ Mbps sustained for full quality

## IMU Data Format

The IMU stream provides JSON packets via UDP:
```json
{
  "timestamp": 123.456789,
  "accelerometer": {
    "x": 0.123, "y": -9.801, "z": 0.045,
    "timestamp": 123.456789
  },
  "gyroscope": {
    "x": 0.001, "y": -0.002, "z": 0.003,
    "timestamp": 123.456790
  }
}
```

- **Accelerometer**: m/s² (meters per second squared)
- **Gyroscope**: rad/s (radians per second)
- **Timestamps**: Device time in seconds with microsecond precision

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
pkill -f quad_streamer

# Check for any remaining processes
ps aux | grep quad_streamer

# If persistent, physically disconnect and reconnect OAK-D Pro
```

### IMU Data Issues
```bash
# Check if IMU is supported
python3 -c "import depthai as dai; print('DepthAI version:', dai.__version__)"

# Test IMU availability
python3 -c "
import depthai as dai
pipeline = dai.Pipeline()
imu = pipeline.create(dai.node.IMU)
print('IMU node created successfully')
"
```

### Performance Issues
- **Reduce resolution**: Not recommended as system is optimized for 720p
- **Lower FPS**: Use `--fps 15` or `--fps 20` if needed
- **Check CPU usage**: `htop` (should be <80% on Pi 5)
- **Monitor temperature**: `vcgencmd measure_temp`
- **Power supply**: Ensure 5V 3A+ for stable operation

### Connection Issues
```bash
# Test network connectivity to PC
ping <PC_IP_ADDRESS>

# Check if video ports are accessible from PC (run on PC):
nc -zv <PI_IP_ADDRESS> 5000 5001 5002 5003

# Check firewall settings
sudo ufw status
```

## Performance Characteristics

### Video Streaming
- **Encoding**: Hardware H.264 for RGB/mono, JPEG for depth
- **Latency**: <100ms for video streams
- **Keyframe frequency**: 30 frames (1 second) for quick recovery
- **Error recovery**: TCP ensures reliable delivery
- **Multi-threaded**: Separate threads per camera stream

### IMU Streaming
- **Update rate**: 100Hz (10ms intervals)
- **Latency**: <50ms for sensor data
- **Protocol**: UDP for minimal overhead
- **Buffering**: Configurable batch reports (1-10 readings)
- **Precision**: Full sensor resolution maintained

### System Load
- **CPU usage**: 60-80% on Raspberry Pi 5
- **Memory**: ~500MB for complete system
- **Network**: Sustained 15 Mbps outbound
- **Thermal**: Stable operation with adequate cooling

## Related Repositories

- **PC Receivers**: https://github.com/rbivy/ivy_streamer_pc
- **GStreamer-based** video receivers with IMU GUI display
- **Complete system** requires both repositories

## System Requirements

### Hardware
- **Raspberry Pi 5** (recommended) or Pi 4 (minimum)
- **OAK-D Pro camera** with USB3 connection
- **Fast SD card**: Class 10 or better (UHS-I recommended)
- **Power supply**: 5V 3A+ for stable operation
- **Cooling**: Heat sink or fan recommended for continuous operation

### Software
- **OS**: Raspberry Pi OS (64-bit recommended)
- **Python**: 3.8+ with pip
- **Network**: Ethernet connection strongly preferred
- **Dependencies**: DepthAI SDK, OpenCV, NumPy

## Version History

- **v3.1**: RGB camera optimization for SLAM applications
  - Implemented software scaling for RGB stream (1080p→720p)
  - Enhanced field-of-view consistency across camera streams
  - Added OpenCV-based scaling with full sensor utilization
- **v3.0**: Quad-stream system with IMU sensor data integration
- **v2.0**: Quad-stream system with depth support
- **v1.0**: Initial triple-stream release
- **Production-tested**: 24/7 operation capability with sensor fusion
- **Optimized architecture**: 4 video + 1 sensor stream performance

## Technical Details

### OAK-D Pro Integration
- **DepthAI SDK**: Latest version with IMU support
- **Camera configuration**: Optimal settings for 720p streaming
- **Stereo depth**: HIGH_DETAIL preset for accurate depth maps
- **IMU sensors**: BMI270 accelerometer/gyroscope at 100Hz
- **USB3 bandwidth**: Efficient utilization for all data streams

### Network Protocol
- **TCP streams**: Reliable delivery for video data (ports 5000-5003)
- **UDP stream**: Low-latency delivery for IMU data (port 5004)
- **Frame synchronization**: Timestamp-based coordination
- **Error handling**: Automatic reconnection and recovery