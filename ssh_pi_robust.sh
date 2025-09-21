#!/bin/bash

# Robust SSH script for Raspberry Pi OAK-D Pro project
# Enhanced error handling and connectivity checking

PI_HOST="192.168.1.202"
PI_USER="ivyspec"
PI_PASSWORD="ivyspec"
PROJECT_DIR="/home/ivyspec/ivy_streamer"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check dependencies
check_dependencies() {
    if ! command -v sshpass &> /dev/null; then
        print_error "sshpass not found. Install it with:"
        print_info "sudo apt update && sudo apt install sshpass"
        return 1
    fi

    if ! command -v ssh &> /dev/null; then
        print_error "ssh not found. Install openssh-client."
        return 1
    fi

    return 0
}

# Function to check network connectivity
check_connectivity() {
    print_info "Checking connectivity to Pi..."

    if ! ping -c 1 -W 3 "$PI_HOST" &> /dev/null; then
        print_error "Cannot reach Pi at $PI_HOST"
        print_info "Check Pi is powered on and connected to network"
        return 1
    fi

    print_status "Pi reachable at $PI_HOST"

    # Check if SSH port is open
    if ! nc -z -w5 "$PI_HOST" 22 2>/dev/null; then
        print_error "SSH port (22) not accessible on $PI_HOST"
        print_info "Check if SSH is enabled on Pi"
        return 1
    fi

    print_status "SSH port accessible"
    return 0
}

# Function to test SSH authentication
test_ssh_auth() {
    print_info "Testing SSH authentication..."

    if sshpass -p "$PI_PASSWORD" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
        "$PI_USER@$PI_HOST" "echo 'SSH test successful'" &> /dev/null; then
        print_status "SSH authentication successful"
        return 0
    else
        print_error "SSH authentication failed"
        print_info "Check username and password:"
        print_info "  Username: $PI_USER"
        print_info "  Password: [hidden]"
        return 1
    fi
}

# Enhanced SSH execution function
execute_ssh() {
    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if sshpass -p "$PI_PASSWORD" ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no \
            "$PI_USER@$PI_HOST" "$@" 2>/dev/null; then
            return 0
        fi

        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            print_warning "SSH attempt $retry_count failed, retrying..."
            sleep 1
        fi
    done

    print_error "SSH failed after $max_retries attempts"
    return 1
}

# Main function
main() {
    echo "========================================="
    echo "  Robust SSH Connection to Pi"
    echo "========================================="
    echo "Target: $PI_USER@$PI_HOST"
    echo "Project Dir: $PROJECT_DIR"
    echo ""

    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi

    # Check connectivity
    if ! check_connectivity; then
        exit 1
    fi

    # Test authentication
    if ! test_ssh_auth; then
        exit 1
    fi

    echo ""

    if [ $# -eq 0 ]; then
        # Interactive SSH session
        print_info "Starting interactive SSH session..."
        print_info "You'll be automatically in the project directory"
        print_info "Press Ctrl+D or type 'exit' to disconnect"
        echo ""

        sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" \
            -t "cd $PROJECT_DIR 2>/dev/null || echo 'Warning: Project directory not found'; exec bash -l"
    else
        # Execute command on Pi
        print_info "Executing command on Pi: $*"
        echo ""

        if execute_ssh "cd $PROJECT_DIR 2>/dev/null; $*"; then
            print_status "Command executed successfully"
        else
            print_error "Command execution failed"
            exit 1
        fi
    fi
}

# Error handling
set -e
trap 'print_error "Script interrupted"; exit 130' INT

# Run main function
main "$@"