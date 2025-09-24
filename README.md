# OAK-D Pro Raspberry Pi Streamer with IMU

**Production-ready quad H.264 video streamer + IMU data** for Raspberry Pi 5 with OAK-D Pro camera.

Streams **RGB + Left + Right cameras + Depth map + IMU sensor data simultaneously** at full performance to PC over Ethernet.

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

# 4. Run the streamer
python quad_streamer_with_imu.py
```

## Streams Available

The streamer provides 5 concurrent data streams:

- **Port 5000**: RGB Camera (H.264, 1920x1080 @ 30fps)
- **Port 5001**: Left Mono Camera (H.264, 1280x720 @ 30fps) 
- **Port 5002**: Right Mono Camera (H.264, 1280x720 @ 30fps)
- **Port 5003**: Depth Map (JPEG, 1280x720 @ 30fps)
- **Port 5004**: IMU Data (UDP, JSON, 100Hz)

## Performance

- **Total bandwidth**: ~25-30 Mbps (4 video streams + IMU)
- **Optimized for**: Computer vision, SLAM, robotics applications
- **Latency**: <100ms end-to-end over ethernet
- **Stability**: Production-tested for continuous operation

## Technical Details

### Video Encoding
- **RGB**: H.264 baseline profile, 1920x1080 software-scaled from native 4K
- **Stereo cameras**: H.264 baseline profile, native 1280x720 
- **Depth**: JPEG compressed depth maps with color encoding

### IMU Data Format
```json
{
  "timestamp": 1695123456789,
  "accelerometer": {"x": 0.12, "y": -9.81, "z": 0.03},
  "gyroscope": {"x": 0.001, "y": -0.002, "z": 0.005},
  "magnetometer": {"x": 25.4, "y": -12.1, "z": 45.2}
}
```

## PC Receiver

For the corresponding PC receiver application, see: [ivy_streamer_pc](https://github.com/rbivy/ivy_streamer_pc)
