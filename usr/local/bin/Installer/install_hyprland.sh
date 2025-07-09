#!/bin/bash

# Setup logging for installer script
LOG_FILE="/tmp/hyprland_installer.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hyprland Installer Script Started" | tee -a "$LOG_FILE"

# Hyprland Profile Installer
# This script calls the Hyprland profile's install.sh script

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Please run as root" | tee -a "$LOG_FILE"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Starting Hyprland Profile Installation..." | tee -a "$LOG_FILE"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILES_DIR="/usr/local/bin/profiles"
HYPRLAND_PROFILE_DIR="$PROFILES_DIR/Hyprland"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Script directory: $SCRIPT_DIR" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Profiles directory: $PROFILES_DIR" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hyprland profile directory: $HYPRLAND_PROFILE_DIR" | tee -a "$LOG_FILE"

# Check if the Hyprland profile directory exists
if [ ! -d "$HYPRLAND_PROFILE_DIR" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Hyprland profile directory not found at $HYPRLAND_PROFILE_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Check if the install.sh script exists
if [ ! -f "$HYPRLAND_PROFILE_DIR/install.sh" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] install.sh script not found in Hyprland profile" | tee -a "$LOG_FILE"
    exit 1
fi

# Change to the Hyprland profile directory
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Changing to Hyprland profile directory" | tee -a "$LOG_FILE"
cd "$HYPRLAND_PROFILE_DIR"

# Make the install script executable
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Making install script executable" | tee -a "$LOG_FILE"
chmod +x install.sh

# Run the Hyprland profile's install script
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Executing Hyprland profile installation..." | tee -a "$LOG_FILE"
./install.sh

# Return to original directory
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Returning to original directory" | tee -a "$LOG_FILE"
cd "$SCRIPT_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hyprland profile installation completed!" | tee -a "$LOG_FILE"
