"""
Global settings and configuration for GamerX Installer
"""

import os
from pathlib import Path

# Application info
APP_NAME = "GamerX Installer"
VERSION = "1.6.0"
DESCRIPTION = "Modern Arch Linux installer with beautiful TUI"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PROFILES_DIR = PROJECT_ROOT / "profiles"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = Path("/tmp/gxinstall-logs")

# Installation paths
MOUNT_POINT = Path("/mnt")
INSTALLER_DIR = Path("/usr/local/bin/Installer")
TARGET_PROFILES_DIR = MOUNT_POINT / "usr/local/bin/profiles"
TARGET_INSTALLER_DIR = MOUNT_POINT / "usr/local/bin/Installer"

# System settings
DEFAULT_MIRROR = "https://geo.mirror.pkgbuild.com/$repo/os/$arch"
MIRROR_TEST_TIMEOUT = 3
MIRROR_TEST_SIZE = 2048  # 2KB test download
MAX_PARALLEL_MIRRORS = 20

# UI settings
THEME_COLORS = {
    "primary": "#00ff88",
    "secondary": "#88ff00", 
    "accent": "#ff8800",
    "error": "#ff4444",
    "warning": "#ffaa00",
    "success": "#44ff44",
    "info": "#4488ff",
    "background": "#1a1a1a",
    "surface": "#2a2a2a",
    "text": "#ffffff",
    "text_secondary": "#cccccc",
    "border": "#444444",
    "highlight": "#333333"
}

# Installation configuration state
CONFIG = {
    # Disk configuration
    "disk": None,
    "filesystem": "ext4",
    "swap_size": "2G",
    
    # User configuration
    "hostname": "",
    "username": "",
    "password": "",
    "sudo_enabled": True,
    
    # System configuration
    "language": ("en_US.UTF-8", "🇺🇸 English (United States)"),
    "locale": ("en_US.UTF-8", "🇺🇸 English (United States)"),
    "timezone": "UTC",
    "kernel": "linux",
    
    # Network configuration
    "mirror": None,
    "mirror_list": [],
    
    # Installation options
    "profile": "Hyprland",
    "additional_packages": "",
    
    # Advanced options
    "enable_multilib": True,
    "install_yay": True,
    "install_hyde": True,
}

# Validation patterns
VALIDATION = {
    "hostname": r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}[a-zA-Z0-9]?$",
    "username": r"^[a-z_][a-z0-9_-]{0,31}$",
    "package_name": r"^[a-z0-9][a-z0-9+._-]*$"
}

# Available options
FILESYSTEMS = ["ext4", "btrfs", "xfs", "f2fs"]
KERNELS = [
    ("linux", "🐧 Linux (Stable)"),
    ("linux-lts", "🔒 Linux LTS (Long Term Support)"),
    ("linux-zen", "⚡ Linux Zen (Performance)"),
    ("linux-hardened", "🛡️ Linux Hardened (Security)")
]

SWAP_SIZES = [
    ("none", "❌ No Swap"),
    ("1G", "💾 1 GB"),
    ("2G", "💾 2 GB"), 
    ("4G", "💾 4 GB"),
    ("8G", "💾 8 GB"),
    ("auto", "🤖 Auto (RAM size)")
]

PROFILES = [
    ("Hyprland", "🪟 Hyprland (Wayland WM)", "Modern tiling window manager"),
    ("Gaming", "🎮 Gaming Setup", "Optimized for gaming with Steam, Lutris"),
    ("Hacking", "🔐 Security/Hacking", "Penetration testing and security tools")
]
