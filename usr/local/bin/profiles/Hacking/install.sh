#!/bin/bash

# Setup logging for profile installer
LOG_FILE="/tmp/hacking_profile_install.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hacking Profile Installer Started" | tee -a "$LOG_FILE"

echo -e "\e[1;32mHacking Profile Installer Triggered\e[0m"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES_FILE="$SCRIPT_DIR/packages/package-list.txt"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Script directory: $SCRIPT_DIR" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Packages file: $PACKAGES_FILE" | tee -a "$LOG_FILE"

# Check if package list exists
if [ -f "$PACKAGES_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Installing Hacking packages from $PACKAGES_FILE" | tee -a "$LOG_FILE"
    # Read packages and install them
    while IFS= read -r package; do
        # Skip empty lines and comments
        if [[ -n "$package" && ! "$package" =~ ^[[:space:]]*# ]]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Installing: $package" | tee -a "$LOG_FILE"
            if pacman -S --noconfirm "$package"; then
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] Installed: $package" | tee -a "$LOG_FILE"
            else
                echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Failed to install: $package" | tee -a "$LOG_FILE"
            fi
        fi
    done < "$PACKAGES_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hacking packages installation completed!" | tee -a "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Package list not found at $PACKAGES_FILE" | tee -a "$LOG_FILE"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Hacking Profile Installer Completed" | tee -a "$LOG_FILE" 