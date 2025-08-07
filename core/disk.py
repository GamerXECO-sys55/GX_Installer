"""
Intelligent disk management with logical validation
Enhanced version of gx_disk.py with better error handling and space validation
"""

import subprocess
import glob
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from utils.logging import get_logger
from config.settings import MOUNT_POINT, FILESYSTEMS

logger = get_logger(__name__)

class DiskError(Exception):
    """Custom disk operation error"""
    pass

class DiskManager:
    """Intelligent disk management with logical validation"""
    
    def __init__(self):
        self.mount_point = MOUNT_POINT
        
    def list_disks(self) -> List[Dict[str, str]]:
        """List available disks with size and model info"""
        disks = []
        
        try:
            # Get disk info using lsblk
            result = subprocess.run([
                'lsblk', '-d', '-n', '-o', 'NAME,SIZE,MODEL,TYPE'
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                parts = line.split(None, 3)
                if len(parts) >= 3 and parts[3] == 'disk':
                    name = parts[0]
                    size = parts[1]
                    model = parts[2] if len(parts) > 2 else "Unknown"
                    
                    # Full device path
                    device_path = f"/dev/{name}"
                    
                    # Check if disk exists
                    if Path(device_path).exists():
                        disks.append({
                            'name': name,
                            'path': device_path,
                            'size': size,
                            'model': model,
                            'display': f"💾 {name} ({size}) - {model}"
                        })
                        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list disks: {e}")
            raise DiskError(f"Could not list disks: {e}")
        
        if not disks:
            raise DiskError("No suitable disks found")
            
        logger.info(f"Found {len(disks)} available disks")
        return disks
    
    def get_disk_info(self, disk_path: str) -> Dict[str, str]:
        """Get detailed disk information"""
        try:
            # Get disk size in bytes
            result = subprocess.run([
                'lsblk', '-b', '-d', '-n', '-o', 'SIZE,MODEL,FSTYPE', disk_path
            ], capture_output=True, text=True, check=True)
            
            parts = result.stdout.strip().split(None, 2)
            size_bytes = int(parts[0])
            size_gb = size_bytes // (1024**3)
            model = parts[1] if len(parts) > 1 else "Unknown"
            
            # Check if disk is currently mounted
            mount_result = subprocess.run([
                'lsblk', '-n', '-o', 'MOUNTPOINT', disk_path
            ], capture_output=True, text=True)
            
            is_mounted = bool(mount_result.stdout.strip())
            
            return {
                'path': disk_path,
                'size_bytes': size_bytes,
                'size_gb': size_gb,
                'model': model,
                'is_mounted': is_mounted,
                'suitable': size_gb >= 20  # Minimum 20GB
            }
            
        except Exception as e:
            logger.error(f"Failed to get disk info for {disk_path}: {e}")
            raise DiskError(f"Could not get disk info: {e}")
    
    def validate_disk_for_installation(self, disk_path: str, swap_size: str = "2G") -> Tuple[bool, str]:
        """Validate disk is suitable for installation with logical space checking"""
        try:
            disk_info = self.get_disk_info(disk_path)
            
            # Check minimum size
            if disk_info['size_gb'] < 20:
                return False, f"Disk too small: {disk_info['size_gb']}GB (minimum 20GB required)"
            
            # Calculate space requirements
            base_system_gb = 10  # Base Arch system
            boot_partition_gb = 1  # EFI boot partition
            
            # Calculate swap size in GB
            swap_gb = 0
            if swap_size != "none":
                if swap_size == "auto":
                    # Auto = RAM size, max 8GB
                    try:
                        with open('/proc/meminfo', 'r') as f:
                            for line in f:
                                if line.startswith('MemTotal:'):
                                    ram_kb = int(line.split()[1])
                                    ram_gb = ram_kb // (1024 * 1024)
                                    swap_gb = min(ram_gb, 8)
                                    break
                    except:
                        swap_gb = 2  # Default fallback
                elif swap_size.endswith('G'):
                    swap_gb = int(swap_size[:-1])
                elif swap_size.endswith('M'):
                    swap_gb = max(1, int(swap_size[:-1]) // 1024)
            
            total_required_gb = base_system_gb + boot_partition_gb + swap_gb + 5  # 5GB buffer
            
            if disk_info['size_gb'] < total_required_gb:
                return False, f"Insufficient space: {disk_info['size_gb']}GB available, {total_required_gb}GB required (including {swap_gb}GB swap)"
            
            # Check if disk is currently in use
            if disk_info['is_mounted']:
                return False, f"Disk is currently mounted and in use"
            
            available_space = disk_info['size_gb'] - total_required_gb
            return True, f"Disk suitable: {disk_info['size_gb']}GB total, {available_space}GB will remain free"
            
        except Exception as e:
            logger.error(f"Disk validation failed: {e}")
            return False, f"Validation failed: {e}"
    
    def auto_partition(self, disk_path: str, filesystem: str = "ext4", swap_size: str = "2G") -> Dict[str, str]:
        """Automatically partition and format disk with intelligent space allocation"""
        logger.info(f"Auto-partitioning {disk_path} with {filesystem} filesystem and {swap_size} swap")
        
        try:
            # Validate inputs
            if filesystem not in FILESYSTEMS:
                raise DiskError(f"Unsupported filesystem: {filesystem}")
            
            # Validate disk first
            valid, msg = self.validate_disk_for_installation(disk_path, swap_size)
            if not valid:
                raise DiskError(f"Disk validation failed: {msg}")
            
            # Unmount any existing partitions
            self._unmount_disk(disk_path)
            
            # Wipe disk
            logger.info("Wiping disk...")
            subprocess.run(['wipefs', '-a', disk_path], check=True, capture_output=True)
            subprocess.run(['sgdisk', '-Z', disk_path], check=True, capture_output=True)
            
            # Create partitions
            logger.info("Creating partitions...")
            # EFI System Partition (512MB)
            subprocess.run(['sgdisk', '-n', '1:0:+512M', '-t', '1:ef00', disk_path], 
                         check=True, capture_output=True)
            
            # Root partition (remaining space)
            subprocess.run(['sgdisk', '-n', '2:0:0', '-t', '2:8300', disk_path], 
                         check=True, capture_output=True)
            
            # Wait for partition creation
            subprocess.run(['partprobe', disk_path], check=True, capture_output=True)
            
            # Determine partition names
            if 'nvme' in disk_path:
                boot_part = f"{disk_path}p1"
                root_part = f"{disk_path}p2"
            else:
                boot_part = f"{disk_path}1"
                root_part = f"{disk_path}2"
            
            # Format partitions
            logger.info("Formatting partitions...")
            # Format EFI partition
            subprocess.run(['mkfs.fat', '-F32', boot_part], check=True, capture_output=True)
            
            # Format root partition based on filesystem choice
            if filesystem == "ext4":
                subprocess.run(['mkfs.ext4', '-F', root_part], check=True, capture_output=True)
            elif filesystem == "btrfs":
                subprocess.run(['mkfs.btrfs', '-f', root_part], check=True, capture_output=True)
            elif filesystem == "xfs":
                subprocess.run(['mkfs.xfs', '-f', root_part], check=True, capture_output=True)
            elif filesystem == "f2fs":
                subprocess.run(['mkfs.f2fs', '-f', root_part], check=True, capture_output=True)
            
            # Mount partitions
            logger.info("Mounting partitions...")
            self.mount_point.mkdir(exist_ok=True)
            subprocess.run(['mount', root_part, str(self.mount_point)], check=True, capture_output=True)
            
            boot_mount = self.mount_point / "boot" / "efi"
            boot_mount.mkdir(parents=True, exist_ok=True)
            subprocess.run(['mount', boot_part, str(boot_mount)], check=True, capture_output=True)
            
            # Create swap file if requested
            swap_info = "No swap"
            if swap_size != "none":
                swap_info = self._create_swap_file(swap_size)
            
            result = {
                'status': 'success',
                'message': f'Disk {disk_path} successfully partitioned and mounted',
                'disk': disk_path,
                'filesystem': filesystem,
                'boot_partition': boot_part,
                'root_partition': root_part,
                'mount_point': str(self.mount_point),
                'swap_info': swap_info
            }
            
            logger.info(f"Partitioning completed successfully: {result}")
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Partitioning failed: {e}"
            logger.error(error_msg)
            # Cleanup on failure
            self._cleanup_mounts()
            raise DiskError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during partitioning: {e}"
            logger.error(error_msg)
            self._cleanup_mounts()
            raise DiskError(error_msg)
    
    def _unmount_disk(self, disk_path: str):
        """Safely unmount all partitions on a disk"""
        try:
            # Find all partitions on the disk
            if 'nvme' in disk_path:
                partitions = glob.glob(f"{disk_path}p*")
            else:
                partitions = glob.glob(f"{disk_path}*")
            
            # Remove the base disk path
            partitions = [p for p in partitions if p != disk_path]
            
            # Unmount each partition
            for partition in partitions:
                try:
                    subprocess.run(['umount', partition], check=False, capture_output=True)
                except:
                    pass  # Ignore unmount errors
                    
        except Exception as e:
            logger.warning(f"Error unmounting disk partitions: {e}")
    
    def _create_swap_file(self, swap_size: str) -> str:
        """Create and activate swap file with intelligent sizing"""
        try:
            # Calculate swap size
            if swap_size == "auto":
                # Auto = RAM size, max 8GB
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            ram_kb = int(line.split()[1])
                            ram_gb = ram_kb // (1024 * 1024)
                            swap_size = f"{min(ram_gb, 8)}G"
                            break
            
            swap_file = self.mount_point / "swapfile"
            
            logger.info(f"Creating {swap_size} swap file...")
            
            # Create swap file
            subprocess.run(['fallocate', '-l', swap_size, str(swap_file)], 
                         check=True, capture_output=True)
            
            # Set permissions
            subprocess.run(['chmod', '600', str(swap_file)], 
                         check=True, capture_output=True)
            
            # Make swap
            subprocess.run(['mkswap', str(swap_file)], 
                         check=True, capture_output=True)
            
            return f"Swap file created: {swap_size}"
            
        except Exception as e:
            logger.error(f"Failed to create swap file: {e}")
            return f"Swap file creation failed: {e}"
    
    def _cleanup_mounts(self):
        """Clean up mounts on error"""
        try:
            # Unmount in reverse order
            boot_mount = self.mount_point / "boot" / "efi"
            if boot_mount.is_mount():
                subprocess.run(['umount', str(boot_mount)], check=False, capture_output=True)
            
            if self.mount_point.is_mount():
                subprocess.run(['umount', str(self.mount_point)], check=False, capture_output=True)
                
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def get_mount_status(self) -> Dict[str, bool]:
        """Check current mount status"""
        return {
            'root_mounted': self.mount_point.is_mount(),
            'boot_mounted': (self.mount_point / "boot" / "efi").is_mount(),
            'mount_point_exists': self.mount_point.exists()
        }
