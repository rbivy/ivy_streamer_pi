#!/usr/bin/env python3

import subprocess
import psutil
import os
import signal
import time
import socket
import json
import threading

class SimpleOakController:
    def __init__(self):
        self.streamer_process = None
        self.streamer_script = '/home/ivyspec/ivy_streamer/quad_streamer_with_imu.py'
        self.venv_activate = '/home/ivyspec/ivy_streamer/venv/bin/activate'
        self.log_file = '/tmp/streamer.log'
        self.control_port = 9999
        self.running = True

        self.start_server()

    def is_streamer_running(self):
        if self.streamer_process is None:
            return False

        if self.streamer_process.poll() is not None:
            self.streamer_process = None
            return False

        try:
            process = psutil.Process(self.streamer_process.pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.streamer_process = None
            return False

    def start_streamer(self):
        if self.is_streamer_running():
            return {"success": False, "message": f"Streamer already running (PID: {self.streamer_process.pid})"}

        if not os.path.exists(self.streamer_script):
            return {"success": False, "message": f"Streamer script not found: {self.streamer_script}"}

        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)

            cmd = f'source {self.venv_activate} && python3 {self.streamer_script} > {self.log_file} 2>&1'

            self.streamer_process = subprocess.Popen(
                cmd,
                shell=True,
                executable='/bin/bash',
                cwd=os.path.dirname(self.streamer_script),
                preexec_fn=os.setsid
            )

            time.sleep(2)

            if self.is_streamer_running():
                return {"success": True, "message": f"Streamer started (PID: {self.streamer_process.pid})"}
            else:
                return {"success": False, "message": "Streamer failed to start - check log file"}

        except Exception as e:
            return {"success": False, "message": f"Failed to start streamer: {str(e)}"}

    def stop_streamer(self):
        if not self.is_streamer_running():
            if os.path.exists(self.log_file):
                try:
                    os.remove(self.log_file)
                except:
                    pass
            return {"success": True, "message": "Streamer was not running"}

        try:
            pid = self.streamer_process.pid

            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

            timeout = 5
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.is_streamer_running():
                    break
                time.sleep(0.1)

            if self.is_streamer_running():
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                time.sleep(0.5)

            if os.path.exists(self.log_file):
                try:
                    os.remove(self.log_file)
                except:
                    pass

            self.streamer_process = None
            return {"success": True, "message": f"Streamer stopped (PID: {pid})"}

        except Exception as e:
            return {"success": False, "message": f"Failed to stop streamer: {str(e)}"}

    def get_status(self):
        if self.is_streamer_running():
            try:
                process = psutil.Process(self.streamer_process.pid)
                cpu = process.cpu_percent(interval=0.1)
                mem = process.memory_info().rss / 1024 / 1024
                uptime = int(time.time() - process.create_time())

                return {
                    "success": True,
                    "message": f"RUNNING|{self.streamer_process.pid}|{uptime}|{cpu:.1f}|{mem:.1f}"
                }
            except Exception:
                return {"success": True, "message": f"RUNNING|{self.streamer_process.pid}|0|0|0"}
        else:
            return {"success": True, "message": "STOPPED"}

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024).decode()
            command = data.strip()

            if command == "START":
                response = self.start_streamer()
            elif command == "STOP":
                response = self.stop_streamer()
            elif command == "STATUS":
                response = self.get_status()
            elif command == "HEARTBEAT":
                response = self.get_status()
            else:
                response = {"success": False, "message": f"Unknown command: {command}"}

            client_socket.sendall(json.dumps(response).encode())

        except Exception as e:
            error_response = {"success": False, "message": f"Error: {str(e)}"}
            try:
                client_socket.sendall(json.dumps(error_response).encode())
            except:
                pass
        finally:
            client_socket.close()

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.control_port))
        server.listen(5)
        print(f"Controller listening on port {self.control_port}")

        def accept_connections():
            while self.running:
                try:
                    server.settimeout(1.0)
                    client, addr = server.accept()
                    threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Server error: {e}")
                    break

        server_thread = threading.Thread(target=accept_connections, daemon=False)
        server_thread.start()

        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("Shutting down...")
            self.running = False
            if self.is_streamer_running():
                self.stop_streamer()
            server_thread.join(timeout=2)

if __name__ == '__main__':
    controller = SimpleOakController()
