#!/bin/bash

# Setup logging for installer script
LOG_FILE="/tmp/gaming_installer.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Gaming Installer Script Started" | tee -a "$LOG_FILE"

# Gaming Profile Installer
# This script calls the Gaming profile's install.sh script

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Please run as root" | tee -a "$LOG_FILE"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Starting Gaming Profile Installation..." | tee -a "$LOG_FILE"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILES_DIR="/usr/local/bin/profiles"
GAMING_PROFILE_DIR="$PROFILES_DIR/Gaming"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Script directory: $SCRIPT_DIR" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Profiles directory: $PROFILES_DIR" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Gaming profile directory: $GAMING_PROFILE_DIR" | tee -a "$LOG_FILE"

# Check if the Gaming profile directory exists
if [ ! -d "$GAMING_PROFILE_DIR" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Gaming profile directory not found at $GAMING_PROFILE_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Check if the install.sh script exists
if [ ! -f "$GAMING_PROFILE_DIR/install.sh" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] install.sh script not found in Gaming profile" | tee -a "$LOG_FILE"
    exit 1
fi

# Change to the Gaming profile directory
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Changing to Gaming profile directory" | tee -a "$LOG_FILE"
cd "$GAMING_PROFILE_DIR"

# Make the install script executable
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Making install script executable" | tee -a "$LOG_FILE"
chmod +x install.sh

# Run the Gaming profile's install script
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Executing Gaming profile installation..." | tee -a "$LOG_FILE"
./install.sh

# Return to original directory
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Returning to original directory" | tee -a "$LOG_FILE"
cd "$SCRIPT_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Gaming profile installation completed!" | tee -a "$LOG_FILE"
