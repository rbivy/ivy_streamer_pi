#!/usr/bin/env python3
import depthai as dai
import socket
import threading
import time
import argparse
import sys
import json
import cv2
import numpy as np
import struct

class QuadOakStreamerWithIMU:
    def __init__(self, host="192.168.1.201", rgb_port=5000, left_port=5001, right_port=5002, depth_port=5003, imu_port=5004,
                 rgb_width=1280, rgb_height=720, mono_width=1280, mono_height=720, fps=30):
        self.host = host
        self.rgb_port = rgb_port
        self.left_port = left_port
        self.right_port = right_port
        self.depth_port = depth_port
        self.imu_port = imu_port
        self.rgb_width = rgb_width
        self.rgb_height = rgb_height
        self.mono_width = mono_width
        self.mono_height = mono_height
        self.fps = fps
        self.running = False

        # Separate client lists for each stream
        self.rgb_clients = []
        self.left_clients = []
        self.right_clients = []
        self.depth_clients = []

        # Separate server sockets
        self.rgb_server_socket = None
        self.left_server_socket = None
        self.right_server_socket = None
        self.depth_server_socket = None

        # UDP socket for IMU data
        self.imu_socket = None
        self.imu_client_address = None

        # Telemetry tracking
        self.rgb_stats = {'frames_sent': 0, 'frames_dropped': 0, 'last_fps': 0}
        self.left_stats = {'frames_sent': 0, 'frames_dropped': 0, 'last_fps': 0}
        self.right_stats = {'frames_sent': 0, 'frames_dropped': 0, 'last_fps': 0}
        self.depth_stats = {'frames_sent': 0, 'frames_dropped': 0, 'last_fps': 0}
        self.imu_stats = {'packets_sent': 0, 'last_rate': 0}

    def start_rgb_server(self):
        self.rgb_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rgb_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rgb_server_socket.bind((self.host, self.rgb_port))
        self.rgb_server_socket.listen(5)
        print(f"RGB server listening on {self.host}:{self.rgb_port}")
        threading.Thread(target=self.accept_rgb_clients, daemon=True).start()

    def start_left_server(self):
        self.left_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.left_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.left_server_socket.bind((self.host, self.left_port))
        self.left_server_socket.listen(5)
        print(f"Left camera server listening on {self.host}:{self.left_port}")
        threading.Thread(target=self.accept_left_clients, daemon=True).start()

    def start_right_server(self):
        self.right_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.right_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.right_server_socket.bind((self.host, self.right_port))
        self.right_server_socket.listen(5)
        print(f"Right camera server listening on {self.host}:{self.right_port}")
        threading.Thread(target=self.accept_right_clients, daemon=True).start()

    def start_depth_server(self):
        self.depth_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.depth_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.depth_server_socket.bind((self.host, self.depth_port))
        self.depth_server_socket.listen(5)
        print(f"Depth server listening on {self.host}:{self.depth_port}")
        threading.Thread(target=self.accept_depth_clients, daemon=True).start()

    def start_imu_server(self):
        self.imu_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.imu_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.imu_socket.bind((self.host, self.imu_port))
        print(f"IMU UDP server listening on {self.host}:{self.imu_port}")
        # Start thread to listen for IMU client registration
        threading.Thread(target=self.listen_for_imu_client, daemon=True).start()

    def listen_for_imu_client(self):
        while self.running:
            try:
                self.imu_socket.settimeout(1.0)
                data, addr = self.imu_socket.recvfrom(1024)
                if data == b'REGISTER_IMU':
                    self.imu_client_address = addr
                    print(f"IMU client registered from {addr}")
                    # Send acknowledgment
                    self.imu_socket.sendto(b'IMU_ACK', addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error in IMU listener: {e}")

    def accept_rgb_clients(self):
        while self.running:
            try:
                self.rgb_server_socket.settimeout(1.0)
                client_socket, addr = self.rgb_server_socket.accept()
                print(f"RGB client connected from {addr}")
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                self.rgb_clients.append(client_socket)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting RGB client: {e}")

    def accept_left_clients(self):
        while self.running:
            try:
                self.left_server_socket.settimeout(1.0)
                client_socket, addr = self.left_server_socket.accept()
                print(f"Left camera client connected from {addr}")
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                self.left_clients.append(client_socket)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting Left client: {e}")

    def accept_right_clients(self):
        while self.running:
            try:
                self.right_server_socket.settimeout(1.0)
                client_socket, addr = self.right_server_socket.accept()
                print(f"Right camera client connected from {addr}")
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                self.right_clients.append(client_socket)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting Right client: {e}")

    def accept_depth_clients(self):
        while self.running:
            try:
                self.depth_server_socket.settimeout(1.0)
                client_socket, addr = self.depth_server_socket.accept()
                print(f"Depth client connected from {addr}")
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                self.depth_clients.append(client_socket)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting Depth client: {e}")

    def broadcast_frame(self, data, clients, stream_name, stats):
        disconnected = []
        for client in clients:
            try:
                frame_size_bytes = len(data).to_bytes(4, byteorder='big')
                client.sendall(frame_size_bytes)
                client.sendall(data)
                stats['frames_sent'] += 1
            except (socket.error, BrokenPipeError):
                disconnected.append(client)
                stats['frames_dropped'] += 1
        for client in disconnected:
            print(f"{stream_name} client disconnected")
            clients.remove(client)
            try:
                client.close()
            except:
                pass

    def broadcast_depth_frame(self, depth_frame, clients, stats):
        disconnected = []
        # Send raw 16-bit depth data for SLAM
        depth_raw = depth_frame.astype(np.uint16)
        
        # Create header with dimensions for SLAM
        height, width = depth_raw.shape
        timestamp = time.time()  # Host timestamp for synchronization
        header = struct.pack('>IIIQ', width, height, depth_raw.dtype.itemsize, int(timestamp * 1000000))
        
        # Convert to bytes
        depth_bytes = depth_raw.tobytes()
        data = header + depth_bytes
        
        for client in clients:
            try:
                frame_size_bytes = len(data).to_bytes(4, byteorder='big')
                client.sendall(frame_size_bytes)
                client.sendall(data)
                stats['frames_sent'] += 1
            except (socket.error, BrokenPipeError):
                disconnected.append(client)
                stats['frames_dropped'] += 1
        for client in disconnected:
            print(f"Depth client disconnected")
            clients.remove(client)
            try:
                client.close()
            except:
                pass
    def send_imu_data(self, imu_packet):
        if self.imu_client_address and self.imu_socket:
            try:
                # Access accelerometer and gyroscope data
                accelero = imu_packet.acceleroMeter
                gyro = imu_packet.gyroscope

                # Use host timestamp for synchronization (Fix #2)
                host_timestamp = time.time()

                # Format IMU data as JSON with synchronized timestamp
                imu_dict = {
                    'timestamp': host_timestamp,  # Use host timestamp for sync
                    'accelerometer': {
                        'x': accelero.x,
                        'y': accelero.y,
                        'z': accelero.z,
                        'timestamp': host_timestamp
                    },
                    'gyroscope': {
                        'x': gyro.x,
                        'y': gyro.y,
                        'z': gyro.z,
                        'timestamp': host_timestamp
                    }
                }
                json_data = json.dumps(imu_dict)
                self.imu_socket.sendto(json_data.encode(), self.imu_client_address)
                self.imu_stats['packets_sent'] += 1
            except Exception as e:
                print(f"Error sending IMU data: {e}")
    def run(self):
        self.running = True
        self.start_rgb_server()
        self.start_left_server()
        self.start_right_server()
        self.start_depth_server()
        self.start_imu_server()

        print(f"Setting up OAK-D Pro quad pipeline with depth and IMU:")
        print(f"  RGB: {self.rgb_width}x{self.rgb_height} @ {self.fps}fps")
        print(f"  Left: {self.mono_width}x{self.mono_height} @ {self.fps}fps")
        print(f"  Right: {self.mono_width}x{self.mono_height} @ {self.fps}fps")
        print(f"  Depth: {self.mono_width}x{self.mono_height} @ {self.fps}fps")
        print(f"  IMU: Accelerometer + Gyroscope @ 100Hz")

        pipeline = dai.Pipeline()

        # RGB Camera
        camRgb = pipeline.create(dai.node.ColorCamera)
        camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setVideoSize(1280, 720)  # Full 1080p output - PC scales to 720p
        camRgb.setFps(self.fps)

        # Mono cameras
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoLeft.setBoardSocket(dai.CameraBoardSocket.CAM_B)
        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

        monoRight = pipeline.create(dai.node.MonoCamera)
        monoRight.setBoardSocket(dai.CameraBoardSocket.CAM_C)
        monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

        # Depth node
        stereoDepth = pipeline.create(dai.node.StereoDepth)
        stereoDepth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DETAIL)
        stereoDepth.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_5x5)
        stereoDepth.setLeftRightCheck(True)
        stereoDepth.setExtendedDisparity(False)
        stereoDepth.setSubpixel(False)
        monoLeft.out.link(stereoDepth.left)
        monoRight.out.link(stereoDepth.right)

        # IMU node
        imu = pipeline.create(dai.node.IMU)
        # Enable accelerometer and gyroscope at 100Hz
        imu.enableIMUSensor([dai.IMUSensor.ACCELEROMETER_RAW, dai.IMUSensor.GYROSCOPE_RAW], 200)
        # Set batch report threshold to 1 for low latency
        imu.setBatchReportThreshold(1)
        # Max batch reports to 10
        imu.setMaxBatchReports(10)

        # Encoders for RGB, Left, Right
        rgbEncoder = pipeline.create(dai.node.VideoEncoder)
        leftEncoder = pipeline.create(dai.node.VideoEncoder)
        rightEncoder = pipeline.create(dai.node.VideoEncoder)

        rgb_bitrate_kbps = 8000
        mono_bitrate_kbps = 3000

        rgbEncoder_built = rgbEncoder.build(
            input=camRgb.video,
            bitrate=rgb_bitrate_kbps * 1000,
            frameRate=self.fps,
            profile=dai.VideoEncoderProperties.Profile.H264_HIGH,
            keyframeFrequency=15
        )

        leftEncoder_built = leftEncoder.build(
            input=monoLeft.out,
            bitrate=mono_bitrate_kbps * 1000,
            frameRate=self.fps,
            profile=dai.VideoEncoderProperties.Profile.H264_HIGH,
            keyframeFrequency=15
        )

        rightEncoder_built = rightEncoder.build(
            input=monoRight.out,
            bitrate=mono_bitrate_kbps * 1000,
            frameRate=self.fps,
            profile=dai.VideoEncoderProperties.Profile.H264_HIGH,
            keyframeFrequency=15
        )

        # Create output queues
        rgbQueue = rgbEncoder_built.bitstream.createOutputQueue(maxSize=1, blocking=False)
        leftQueue = leftEncoder_built.bitstream.createOutputQueue(maxSize=1, blocking=False)
        rightQueue = rightEncoder_built.bitstream.createOutputQueue(maxSize=1, blocking=False)
        depthQueue = stereoDepth.depth.createOutputQueue(maxSize=1, blocking=False)
        imuQueue = imu.out.createOutputQueue(maxSize=50, blocking=False)

        print("Starting OAK-D Pro device...")

        try:
            pipeline.start()
            with pipeline:
                print("Quad streaming with IMU started. Press Ctrl+C to stop.")

                rgb_frame_count = 0
                left_frame_count = 0
                right_frame_count = 0
                depth_frame_count = 0
                imu_packet_count = 0
                start_time = time.time()
                last_stats_time = start_time

                while pipeline.isRunning() and self.running:
                    try:
                        # RGB H.264 stream
                        if rgbQueue.has():
                            h264Packet = rgbQueue.get()
                            data = h264Packet.getData()
                            if self.rgb_clients:
                                self.broadcast_frame(data, self.rgb_clients, "RGB", self.rgb_stats)
                            rgb_frame_count += 1

                        # Left H.264 stream
                        if leftQueue.has():
                            h264Packet = leftQueue.get()
                            data = h264Packet.getData()
                            if self.left_clients:
                                self.broadcast_frame(data, self.left_clients, "Left", self.left_stats)
                            left_frame_count += 1

                        # Right H.264 stream
                        if rightQueue.has():
                            h264Packet = rightQueue.get()
                            data = h264Packet.getData()
                            if self.right_clients:
                                self.broadcast_frame(data, self.right_clients, "Right", self.right_stats)
                            right_frame_count += 1

                        # Depth raw stream (converted to JPEG)
                        if depthQueue.has():
                            depthFrame = depthQueue.get().getFrame()
                            if self.depth_clients:
                                self.broadcast_depth_frame(depthFrame, self.depth_clients, self.depth_stats)
                            depth_frame_count += 1

                        # IMU data stream
                        if imuQueue.has():
                            imuData = imuQueue.get()
                            imuPackets = imuData.packets
                            for imuPacket in imuPackets:
                                self.send_imu_data(imuPacket)
                                imu_packet_count += 1

                        current_time = time.time()
                        if current_time - last_stats_time >= 2.0:
                            elapsed = current_time - start_time
                            rgb_fps = rgb_frame_count / elapsed if elapsed > 0 else 0
                            left_fps = left_frame_count / elapsed if elapsed > 0 else 0
                            right_fps = right_frame_count / elapsed if elapsed > 0 else 0
                            depth_fps = depth_frame_count / elapsed if elapsed > 0 else 0
                            imu_rate = imu_packet_count / elapsed if elapsed > 0 else 0

                            self.rgb_stats['last_fps'] = rgb_fps
                            self.left_stats['last_fps'] = left_fps
                            self.right_stats['last_fps'] = right_fps
                            self.depth_stats['last_fps'] = depth_fps
                            self.imu_stats['last_rate'] = imu_rate

                            print(f"RGB: {rgb_fps:.1f} fps ({len(self.rgb_clients)} clients) | "
                                  f"Left: {left_fps:.1f} fps ({len(self.left_clients)} clients) | "
                                  f"Right: {right_fps:.1f} fps ({len(self.right_clients)} clients) | "
                                  f"Depth: {depth_fps:.1f} fps ({len(self.depth_clients)} clients) | "
                                  f"IMU: {imu_rate:.1f} Hz")
                            last_stats_time = current_time

                        else:
                            time.sleep(0.001)

                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        print(f"Error in streaming loop: {e}")

        except Exception as e:
            print(f"Failed to start quad pipeline with IMU: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()

    def shutdown(self):
        print("\nShutting down quad streamer with IMU...")
        self.running = False
        for clients in [self.rgb_clients, self.left_clients, self.right_clients, self.depth_clients]:
            for client in clients:
                try:
                    client.close()
                except:
                    pass
        for socket_obj in [self.rgb_server_socket, self.left_server_socket, self.right_server_socket, self.depth_server_socket, self.imu_socket]:
            if socket_obj:
                try:
                    socket_obj.close()
                except:
                    pass
        print("Quad streamer with IMU stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OAK-D Pro Quad Streamer with Depth and IMU')
    parser.add_argument('--fps', type=int, default=30, help='FPS (default: 30)')
    args = parser.parse_args()

    streamer = QuadOakStreamerWithIMU(fps=args.fps)
    try:
        streamer.run()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)