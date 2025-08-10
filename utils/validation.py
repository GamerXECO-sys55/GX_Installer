"""
Input validation utilities
"""

import re
import shutil
import subprocess
import socket
from pathlib import Path
from typing import Tuple, Optional
from config.settings import VALIDATION, MOUNT_POINT
from utils.logging import get_logger

logger = get_logger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_hostname(hostname: str) -> Tuple[bool, str]:
    """Validate hostname according to RFC standards"""
    if not hostname:
        return False, "Hostname cannot be empty"
    
    if len(hostname) > 63:
        return False, "Hostname too long (max 63 characters)"
    
    if not re.match(VALIDATION["hostname"], hostname):
        return False, "Invalid hostname format (use letters, numbers, hyphens only)"
    
    if hostname.startswith('-') or hostname.endswith('-'):
        return False, "Hostname cannot start or end with hyphen"
    
    return True, "Valid hostname"

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username according to Linux standards"""
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) > 32:
        return False, "Username too long (max 32 characters)"
    
    if not re.match(VALIDATION["username"], username):
        return False, "Invalid username (use lowercase letters, numbers, underscore, hyphen only)"
    
    if username in ['root', 'bin', 'daemon', 'sys', 'sync', 'games', 'man', 'lp', 'mail', 'news', 'uucp', 'proxy', 'www-data', 'backup', 'list', 'irc', 'gnats', 'nobody']:
        return False, "Username conflicts with system user"
    
    return True, "Valid username"

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 6:
        return False, "Password too short (minimum 6 characters)"
    
    if len(password) > 128:
        return False, "Password too long (maximum 128 characters)"
    
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    
    if not (has_letter and has_number):
        return False, "Password should contain both letters and numbers"
    
    return True, "Strong password"

def validate_package_list(packages: str) -> Tuple[bool, str, list]:
    """Validate additional packages list"""
    if not packages.strip():
        return True, "No additional packages", []
    
    # Split packages by whitespace and comma
    package_list = []
    for pkg in re.split(r'[,\s]+', packages.strip()):
        pkg = pkg.strip()
        if not pkg:
            continue
            
        # Basic package name validation
        if not re.match(VALIDATION["package_name"], pkg):
            return False, f"Invalid package name: {pkg}", []
        
        package_list.append(pkg)
    
    if len(package_list) > 50:
        return False, "Too many packages (maximum 50)", []
    
    return True, f"Valid packages: {len(package_list)}", package_list

def validate_disk_space(disk_path: str, required_gb: int = 20) -> Tuple[bool, str]:
    """Validate disk has enough space"""
    try:
        # Get disk size using lsblk
        import subprocess
        result = subprocess.run(
            ['lsblk', '-b', '-d', '-n', '-o', 'SIZE', disk_path],
            capture_output=True, text=True, check=True
        )
        
        disk_size_bytes = int(result.stdout.strip())
        disk_size_gb = disk_size_bytes // (1024**3)
        
        if disk_size_gb < required_gb:
            return False, f"Insufficient disk space: {disk_size_gb}GB (minimum {required_gb}GB required)"
        
        return True, f"Sufficient disk space: {disk_size_gb}GB available"
        
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        return False, f"Could not verify disk space: {e}"

def validate_swap_size(swap_size: str, disk_path: str) -> Tuple[bool, str]:
    """Validate swap size is reasonable for the disk"""
    if swap_size == "none":
        return True, "No swap file will be created"
    
    try:
        # Get available RAM
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    ram_kb = int(line.split()[1])
                    ram_gb = ram_kb // (1024 * 1024)
                    break
        
        if swap_size == "auto":
            # Auto swap = RAM size, max 8GB
            auto_size = min(ram_gb, 8)
            return True, f"Auto swap size: {auto_size}GB (based on {ram_gb}GB RAM)"
        
        # Parse manual swap size
        if swap_size.endswith('G'):
            swap_gb = int(swap_size[:-1])
        elif swap_size.endswith('M'):
            swap_gb = int(swap_size[:-1]) // 1024
        else:
            return False, "Invalid swap size format (use 1G, 2G, etc.)"
        
        # Check if swap size is reasonable
        if swap_gb > 16:
            return False, "Swap size too large (maximum 16GB recommended)"
        
        if swap_gb < 1:
            return False, "Swap size too small (minimum 1GB)"
        
        # Check if disk has enough space for swap + system
        disk_valid, disk_msg = validate_disk_space(disk_path, 20 + swap_gb)
        if not disk_valid:
            return False, f"Not enough space for swap: {disk_msg}"
        
        return True, f"Valid swap size: {swap_gb}GB"
        
    except Exception as e:
        logger.error(f"Error validating swap size: {e}")
        return False, f"Could not validate swap size: {e}"

def get_system_memory() -> int:
    """Get system memory in MB"""
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    # Extract memory in kB and convert to MB
                    mem_kb = int(line.split()[1])
                    return mem_kb // 1024
        return 0
    except Exception as e:
        logger.error(f"Error getting system memory: {e}")
        return 0

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username according to Linux standards"""
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) > 32:
        return False, "Username too long (max 32 characters)"
    
    if not re.match(r'^[a-z_][a-z0-9_-]*$', username):
        return False, "Invalid username format (use lowercase letters, numbers, underscore, hyphen)"
    
    if username in ['root', 'bin', 'daemon', 'sys', 'sync', 'games', 'man', 'lp', 'mail', 'news', 'uucp', 'proxy', 'www-data', 'backup', 'list', 'irc', 'gnats', 'nobody']:
        return False, "Username is reserved"
    
    return True, "Valid username"

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 6:
        return False, "Password too short (minimum 6 characters)"
    
    if len(password) > 128:
        return False, "Password too long (maximum 128 characters)"
    
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    
    if not has_letter:
        return False, "Password must contain at least one letter"
    
    if not has_number:
        return False, "Password must contain at least one number"
    
    return True, "Strong password"

def validate_network_connection() -> Tuple[bool, str]:
    """Check if network connection is available"""
    try:
        # Try to connect to Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True, "Network connection available"
    except OSError:
        try:
            # Try alternative DNS
            socket.create_connection(("1.1.1.1", 53), timeout=3)
            return True, "Network connection available"
        except OSError:
            return False, "No network connection detected"

def validate_mount_point() -> Tuple[bool, str]:
    """Validate mount point is ready for installation"""
    if not MOUNT_POINT.exists():
        return False, f"Mount point {MOUNT_POINT} does not exist"
    
    if not MOUNT_POINT.is_mount():
        return False, f"Nothing mounted at {MOUNT_POINT}"
    
    # Check if mount point has enough space
    try:
        stat = shutil.disk_usage(MOUNT_POINT)
        free_gb = stat.free // (1024**3)
        
        if free_gb < 10:
            return False, f"Insufficient space at mount point: {free_gb}GB free"
        
        return True, f"Mount point ready: {free_gb}GB available"
        
    except Exception as e:
        logger.error(f"Error checking mount point: {e}")
        return False, f"Could not validate mount point: {e}"

def validate_network_connection() -> Tuple[bool, str]:
    """Validate network connectivity"""
    try:
        import urllib.request
        
        # Test connection to Arch Linux website
        urllib.request.urlopen('https://archlinux.org', timeout=5)
        return True, "Network connection available"
        
    except Exception as e:
        logger.error(f"Network validation failed: {e}")
        return False, f"No network connection: {e}"
