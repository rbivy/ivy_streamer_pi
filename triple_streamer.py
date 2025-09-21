#!/usr/bin/env python3
"""
OAK-D Pro Triple H.264 Video Streamer
RGB (port 5000) + Left Mono (port 5001) + Right Mono (port 5002)
Clean separate streams following exact working pattern from streamer_v3.py
"""

import depthai as dai
import socket
import threading
import time
import argparse
import sys
import struct
import json

class TripleOakStreamer:
    def __init__(self, host='0.0.0.0', rgb_port=5000, left_port=5001, right_port=5002,
                 rgb_width=1920, rgb_height=1080, mono_width=1280, mono_height=720, fps=30):
        self.host = host
        self.rgb_port = rgb_port
        self.left_port = left_port
        self.right_port = right_port
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

        # Separate server sockets
        self.rgb_server_socket = None
        self.left_server_socket = None
        self.right_server_socket = None

        # Telemetry tracking
        self.rgb_stats = {'frames_sent': 0, 'frames_dropped': 0, 'last_fps': 0}
        self.left_stats = {'frames_sent': 0, 'frames_dropped': 0, 'last_fps': 0}
        self.right_stats = {'frames_sent': 0, 'frames_dropped': 0, 'last_fps': 0}

    def start_rgb_server(self):
        """Start TCP server for RGB streaming"""
        self.rgb_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rgb_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rgb_server_socket.bind((self.host, self.rgb_port))
        self.rgb_server_socket.listen(5)
        print(f"RGB server listening on {self.host}:{self.rgb_port}")

        accept_thread = threading.Thread(target=self.accept_rgb_clients)
        accept_thread.daemon = True
        accept_thread.start()

    def start_left_server(self):
        """Start TCP server for Left camera streaming"""
        self.left_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.left_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.left_server_socket.bind((self.host, self.left_port))
        self.left_server_socket.listen(5)
        print(f"Left camera server listening on {self.host}:{self.left_port}")

        accept_thread = threading.Thread(target=self.accept_left_clients)
        accept_thread.daemon = True
        accept_thread.start()

    def start_right_server(self):
        """Start TCP server for Right camera streaming"""
        self.right_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.right_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.right_server_socket.bind((self.host, self.right_port))
        self.right_server_socket.listen(5)
        print(f"Right camera server listening on {self.host}:{self.right_port}")

        accept_thread = threading.Thread(target=self.accept_right_clients)
        accept_thread.daemon = True
        accept_thread.start()

    def accept_rgb_clients(self):
        """Accept incoming RGB client connections"""
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
        """Accept incoming Left camera client connections"""
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
        """Accept incoming Right camera client connections"""
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

    def broadcast_frame(self, data, clients, stream_name, stats):
        """Send frame data to all connected clients with telemetry"""
        disconnected = []

        # Prepare telemetry packet
        telemetry = {
            'stream': stream_name,
            'resolution': f"{self.rgb_width}x{self.rgb_height}" if stream_name == "RGB" else f"{self.mono_width}x{self.mono_height}",
            'fps': stats['last_fps'],
            'frames_sent': stats['frames_sent'],
            'frames_dropped': stats['frames_dropped'],
            'clients': len(clients),
            'timestamp': time.time()
        }
        telemetry_json = json.dumps(telemetry).encode('utf-8')
        telemetry_size = len(telemetry_json)

        for client in clients:
            try:
                # Send frame size (4 bytes) + telemetry size (4 bytes)
                frame_size_bytes = len(data).to_bytes(4, byteorder='big')
                telemetry_size_bytes = telemetry_size.to_bytes(4, byteorder='big')

                # Send header: frame_size + telemetry_size + telemetry_data + frame_data
                client.sendall(frame_size_bytes)
                client.sendall(telemetry_size_bytes)
                client.sendall(telemetry_json)
                client.sendall(data)

                stats['frames_sent'] += 1
            except (socket.error, BrokenPipeError):
                disconnected.append(client)
                stats['frames_dropped'] += 1

        # Remove disconnected clients
        for client in disconnected:
            print(f"{stream_name} client disconnected")
            clients.remove(client)
            try:
                client.close()
            except:
                pass

    def run(self):
        """Main triple streaming loop - exact same pattern as working version"""
        self.running = True

        # Start all three servers
        self.start_rgb_server()
        self.start_left_server()
        self.start_right_server()

        print(f"Setting up OAK-D Pro triple pipeline:")
        print(f"  RGB: {self.rgb_width}x{self.rgb_height} @ {self.fps}fps")
        print(f"  Left: {self.mono_width}x{self.mono_height} @ {self.fps}fps")
        print(f"  Right: {self.mono_width}x{self.mono_height} @ {self.fps}fps")
        print("DepthAI version:", dai.__version__)

        # Create pipeline - EXACT same pattern as working version
        pipeline = dai.Pipeline()

        # RGB ColorCamera - exact same as working version
        camRgb = pipeline.create(dai.node.ColorCamera)
        camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setVideoSize(self.rgb_width, self.rgb_height)
        camRgb.setFps(self.fps)

        # Left MonoCamera
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoLeft.setBoardSocket(dai.CameraBoardSocket.CAM_B)
        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

        # Right MonoCamera
        monoRight = pipeline.create(dai.node.MonoCamera)
        monoRight.setBoardSocket(dai.CameraBoardSocket.CAM_C)
        monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

        # Create VideoEncoder nodes - EXACT same pattern as working version
        rgbEncoder = pipeline.create(dai.node.VideoEncoder)
        leftEncoder = pipeline.create(dai.node.VideoEncoder)
        rightEncoder = pipeline.create(dai.node.VideoEncoder)

        # Set bitrates - same logic as working version
        rgb_bitrate_kbps = 8000 if self.rgb_width >= 1920 else 4000
        mono_bitrate_kbps = 3000 if self.mono_width >= 1280 else 1500

        print(f"RGB H.264 encoder configuration: {rgb_bitrate_kbps} kbps bitrate")
        print(f"Left H.264 encoder configuration: {mono_bitrate_kbps} kbps bitrate")
        print(f"Right H.264 encoder configuration: {mono_bitrate_kbps} kbps bitrate")

        # Build encoders with input links - EXACT same pattern as working version
        rgbEncoder_built = rgbEncoder.build(
            input=camRgb.video,
            bitrate=rgb_bitrate_kbps * 1000,
            frameRate=self.fps,
            profile=dai.VideoEncoderProperties.Profile.H264_BASELINE,
            keyframeFrequency=30
        )

        leftEncoder_built = leftEncoder.build(
            input=monoLeft.out,
            bitrate=mono_bitrate_kbps * 1000,
            frameRate=self.fps,
            profile=dai.VideoEncoderProperties.Profile.H264_BASELINE,
            keyframeFrequency=30
        )

        rightEncoder_built = rightEncoder.build(
            input=monoRight.out,
            bitrate=mono_bitrate_kbps * 1000,
            frameRate=self.fps,
            profile=dai.VideoEncoderProperties.Profile.H264_BASELINE,
            keyframeFrequency=30
        )

        # Create output queues BEFORE starting pipeline - EXACT same pattern as working version
        rgbQueue = rgbEncoder_built.bitstream.createOutputQueue(maxSize=1, blocking=False)
        leftQueue = leftEncoder_built.bitstream.createOutputQueue(maxSize=1, blocking=False)
        rightQueue = rightEncoder_built.bitstream.createOutputQueue(maxSize=1, blocking=False)

        print("Starting OAK-D Pro device...")

        try:
            # Start pipeline - EXACT same pattern as working version
            pipeline.start()

            # Use context manager for automatic cleanup - EXACT same pattern as working version
            with pipeline:
                print("Triple streaming started. Press Ctrl+C to stop.")
                print(f"Waiting for clients to connect...")
                print(f"  RGB clients: port {self.rgb_port}")
                print(f"  Left camera clients: port {self.left_port}")
                print(f"  Right camera clients: port {self.right_port}")

                rgb_frame_count = 0
                left_frame_count = 0
                right_frame_count = 0
                start_time = time.time()
                last_stats_time = start_time

                # Check pipeline.isRunning() - EXACT same pattern as working version
                while pipeline.isRunning() and self.running:
                    try:
                        # Get RGB H.264 encoded frame - EXACT same pattern as working version
                        if rgbQueue.has():
                            h264Packet = rgbQueue.get()
                            data = h264Packet.getData()

                            if self.rgb_clients:
                                self.broadcast_frame(data, self.rgb_clients, "RGB", self.rgb_stats)

                            rgb_frame_count += 1

                        # Get Left H.264 encoded frame - same pattern
                        if leftQueue.has():
                            h264Packet = leftQueue.get()
                            data = h264Packet.getData()

                            if self.left_clients:
                                self.broadcast_frame(data, self.left_clients, "Left", self.left_stats)

                            left_frame_count += 1

                        # Get Right H.264 encoded frame - same pattern
                        if rightQueue.has():
                            h264Packet = rightQueue.get()
                            data = h264Packet.getData()

                            if self.right_clients:
                                self.broadcast_frame(data, self.right_clients, "Right", self.right_stats)

                            right_frame_count += 1

                        # Print stats every 2 seconds - same pattern
                        current_time = time.time()
                        if current_time - last_stats_time >= 2.0:
                            elapsed = current_time - start_time
                            rgb_fps = rgb_frame_count / elapsed if elapsed > 0 else 0
                            left_fps = left_frame_count / elapsed if elapsed > 0 else 0
                            right_fps = right_frame_count / elapsed if elapsed > 0 else 0

                            # Update stats for telemetry
                            self.rgb_stats['last_fps'] = rgb_fps
                            self.left_stats['last_fps'] = left_fps
                            self.right_stats['last_fps'] = right_fps

                            print(f"RGB: {rgb_fps:.1f} fps ({len(self.rgb_clients)} clients, {self.rgb_stats['frames_dropped']} dropped) | "
                                  f"Left: {left_fps:.1f} fps ({len(self.left_clients)} clients, {self.left_stats['frames_dropped']} dropped) | "
                                  f"Right: {right_fps:.1f} fps ({len(self.right_clients)} clients, {self.right_stats['frames_dropped']} dropped)")
                            last_stats_time = current_time

                        else:
                            time.sleep(0.001)  # Small delay if no frame available

                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        print(f"Error in streaming loop: {e}")

                # Print final stats
                elapsed = time.time() - start_time
                if elapsed > 0:
                    print(f"\nFinal stats:")
                    print(f"  RGB: {rgb_frame_count} frames = {rgb_frame_count/elapsed:.1f} fps")
                    print(f"  Left: {left_frame_count} frames = {left_frame_count/elapsed:.1f} fps")
                    print(f"  Right: {right_frame_count} frames = {right_frame_count/elapsed:.1f} fps")

        except Exception as e:
            print(f"Failed to start triple pipeline: {e}")
            if "No available devices" in str(e):
                print("ERROR: OAK-D Pro not detected. Check:")
                print("1. USB connection")
                print("2. Device permissions (udev rules)")
                print("3. No other processes using the device")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown"""
        print("\nShutting down triple streamer...")
        self.running = False

        # Close all client connections
        for client in self.rgb_clients:
            try:
                client.close()
            except:
                pass

        for client in self.left_clients:
            try:
                client.close()
            except:
                pass

        for client in self.right_clients:
            try:
                client.close()
            except:
                pass

        # Close server sockets
        if self.rgb_server_socket:
            try:
                self.rgb_server_socket.close()
            except:
                pass

        if self.left_server_socket:
            try:
                self.left_server_socket.close()
            except:
                pass

        if self.right_server_socket:
            try:
                self.right_server_socket.close()
            except:
                pass

        print("Triple streamer stopped")

def main():
    parser = argparse.ArgumentParser(description='OAK-D Pro Triple H.264 Video Streamer')
    parser.add_argument('--host', default='0.0.0.0', help='Host IP (default: 0.0.0.0)')
    parser.add_argument('--rgb-port', type=int, default=5000, help='RGB port (default: 5000)')
    parser.add_argument('--left-port', type=int, default=5001, help='Left port (default: 5001)')
    parser.add_argument('--right-port', type=int, default=5002, help='Right port (default: 5002)')
    parser.add_argument('--rgb-width', type=int, default=1920, help='RGB width (default: 1920)')
    parser.add_argument('--rgb-height', type=int, default=1080, help='RGB height (default: 1080)')
    parser.add_argument('--mono-width', type=int, default=1280, help='Mono width (default: 1280)')
    parser.add_argument('--mono-height', type=int, default=720, help='Mono height (default: 720)')
    parser.add_argument('--fps', type=int, default=30, help='FPS (default: 30)')

    args = parser.parse_args()

    streamer = TripleOakStreamer(
        host=args.host,
        rgb_port=args.rgb_port,
        left_port=args.left_port,
        right_port=args.right_port,
        rgb_width=args.rgb_width,
        rgb_height=args.rgb_height,
        mono_width=args.mono_width,
        mono_height=args.mono_height,
        fps=args.fps
    )

    try:
        streamer.run()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()