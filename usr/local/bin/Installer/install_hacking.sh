#!/bin/bash

# Setup logging for installer script
LOG_FILE="/tmp/hacking_installer.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hacking Installer Script Started" | tee -a "$LOG_FILE"

# Hacking Profile Installer
# This script calls the Hacking profile's install.sh script

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Please run as root" | tee -a "$LOG_FILE"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Starting Hacking Profile Installation..." | tee -a "$LOG_FILE"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILES_DIR="/usr/local/bin/profiles"
HACKING_PROFILE_DIR="$PROFILES_DIR/Hacking"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Script directory: $SCRIPT_DIR" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Profiles directory: $PROFILES_DIR" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hacking profile directory: $HACKING_PROFILE_DIR" | tee -a "$LOG_FILE"

# Check if the Hacking profile directory exists
if [ ! -d "$HACKING_PROFILE_DIR" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Hacking profile directory not found at $HACKING_PROFILE_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Check if the install.sh script exists
if [ ! -f "$HACKING_PROFILE_DIR/install.sh" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] install.sh script not found in Hacking profile" | tee -a "$LOG_FILE"
    exit 1
fi

# Change to the Hacking profile directory
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Changing to Hacking profile directory" | tee -a "$LOG_FILE"
cd "$HACKING_PROFILE_DIR"

# Make the install script executable
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Making install script executable" | tee -a "$LOG_FILE"
chmod +x install.sh

# Run the Hacking profile's install script
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Executing Hacking profile installation..." | tee -a "$LOG_FILE"
./install.sh

# Return to original directory
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Returning to original directory" | tee -a "$LOG_FILE"
cd "$SCRIPT_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hacking profile installation completed!" | tee -a "$LOG_FILE"
