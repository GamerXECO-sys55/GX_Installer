#!/bin/bash

# Path verification script for Hyprland profile installation
# This script runs inside chroot environment to verify paths

# Setup logging
LOG_DIR="/tmp/gxinstall_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/hyprland_chroot_paths_${TIMESTAMP}.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log_path() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +%Y-%m-%d_%H:%M:%S)
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    echo "[$level] $message"
}

# Function to verify path with chroot permissions
verify_chroot_path() {
    local path="$1"
    local description="$2"
    
    if [ ! -e "$path" ]; then
        log_path "ERROR" "Path not found: $path ($description)"
        return 1
    fi
    
    # Check permissions
    if [ ! -r "$path" ]; then
        log_path "WARNING" "No read permission: $path"
    fi
    if [ ! -w "$path" ]; then
        log_path "WARNING" "No write permission: $path"
    fi
    if [ ! -x "$path" ]; then
        log_path "WARNING" "No execute permission: $path"
    fi
    
    # Log detailed info
    log_path "INFO" "Path verified: $path ($description)"
    log_path "DEBUG" "Permissions: $(stat -c %a "$path")"
    log_path "DEBUG" "Owner: $(stat -c %U:%G "$path")"
    log_path "DEBUG" "Size: $(stat -c %s "$path") bytes"
    
    return 0
}

# Main path verification function
verify_chroot_paths() {
    log_path "INFO" "Chroot path verification skipped (all checks disabled as per user request)"
    log_path "INFO" "Logs saved to: $LOG_FILE"
}

# Run the verification
verify_chroot_paths
