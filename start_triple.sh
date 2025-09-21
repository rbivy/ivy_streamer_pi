#!/bin/bash
# Start Triple Streamer - RGB + Left + Right cameras

PI_HOST="192.168.1.202"
PI_USER="ivyspec"
PI_PASSWORD="ivyspec"
PROJECT_DIR="/home/ivyspec/ivy_streamer"

echo "========================================="
echo "  Triple OAK-D Pro Streamer"
echo "========================================="
echo "RGB:   1920x1080 @ 30fps -> Port 5000"
echo "Left:  1280x720  @ 30fps -> Port 5001"
echo "Right: 1280x720  @ 30fps -> Port 5002"
echo ""

# Stop current streamers
echo "Stopping current streamers..."
sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" \
"pkill -f streamer && echo 'Streamers stopped' || echo 'No streamers running'"

sleep 3

# Copy triple streamer
echo "Copying triple streamer to Pi..."
sshpass -p "$PI_PASSWORD" scp -o StrictHostKeyChecking=no triple_streamer.py "$PI_USER@$PI_HOST:$PROJECT_DIR/"

# Start triple streamer
echo "Starting triple streamer..."
sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" \
"cd $PROJECT_DIR && source venv/bin/activate && python triple_streamer.py" &

echo ""
echo "Triple streamer started!"
echo "Wait 10 seconds then test with: ./test_triple.sh"