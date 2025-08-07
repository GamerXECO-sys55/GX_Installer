"""
Core system installation operations
Handles pacstrap, chroot, and system configuration
"""

import subprocess
import shutil
import os
from pathlib import Path
from typing import List, Dict, Optional, Callable
from utils.logging import get_logger
from config.settings import MOUNT_POINT, CONFIG

logger = get_logger(__name__)

class SystemInstallError(Exception):
    """Custom system installation error"""
    pass

class SystemInstaller:
    """Core system installation operations"""
    
    def __init__(self, progress_callback: Optional[Callable[[str, int], None]] = None):
        self.mount_point = MOUNT_POINT
        self.progress_callback = progress_callback
        
    def _update_progress(self, message: str, percentage: int):
        """Update progress if callback is provided"""
        if self.progress_callback:
            self.progress_callback(message, percentage)
        logger.info(f"Progress {percentage}%: {message}")
    
    def install_base_system(self, kernel: str = "linux", additional_packages: List[str] = None) -> bool:
        """Install base Arch Linux system with pacstrap"""
        try:
            self._update_progress("Installing base system...", 10)
            
            # Base packages
            base_packages = [
                "base", "base-devel", kernel, f"{kernel}-headers",
                "linux-firmware", "networkmanager", "grub", "efibootmgr",
                "nano", "vim", "git", "wget", "curl"
            ]
            
            # Add additional packages if provided
            if additional_packages:
                base_packages.extend(additional_packages)
            
            logger.info(f"Installing packages: {' '.join(base_packages)}")
            
            # Run pacstrap
            cmd = ["pacstrap", str(self.mount_point)] + base_packages
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = f"pacstrap failed: {result.stderr}"
                logger.error(error_msg)
                raise SystemInstallError(error_msg)
            
            self._update_progress("Base system installed successfully", 25)
            return True
            
        except subprocess.TimeoutExpired:
            error_msg = "Base system installation timed out"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
        except Exception as e:
            error_msg = f"Base system installation failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def generate_fstab(self) -> bool:
        """Generate fstab file"""
        try:
            self._update_progress("Generating fstab...", 30)
            
            fstab_path = self.mount_point / "etc" / "fstab"
            
            # Generate fstab using genfstab
            result = subprocess.run(
                ["genfstab", "-U", str(self.mount_point)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Write fstab
            with open(fstab_path, 'w') as f:
                f.write(result.stdout)
            
            logger.info(f"fstab generated: {len(result.stdout.splitlines())} entries")
            self._update_progress("fstab generated successfully", 35)
            return True
            
        except Exception as e:
            error_msg = f"fstab generation failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def setup_network_in_chroot(self, mirror_url: str = None) -> bool:
        """Setup network configuration for chroot environment"""
        try:
            self._update_progress("Setting up network configuration...", 40)
            
            # Copy resolv.conf for DNS resolution
            resolv_source = Path("/etc/resolv.conf")
            resolv_target = self.mount_point / "etc" / "resolv.conf"
            
            if resolv_source.exists():
                shutil.copy2(resolv_source, resolv_target)
                logger.info("DNS configuration copied")
            
            # Setup mirror configuration
            if mirror_url:
                mirrorlist_target = self.mount_point / "etc" / "pacman.d" / "mirrorlist"
                
                # Create mirrorlist with selected mirror
                with open(mirrorlist_target, 'w') as f:
                    f.write(f"# GamerX Installer - Selected Mirror\n")
                    f.write(f"Server = {mirror_url}\n")
                
                logger.info(f"Mirror configured: {mirror_url}")
            else:
                # Copy current mirrorlist
                mirrorlist_source = Path("/etc/pacman.d/mirrorlist")
                mirrorlist_target = self.mount_point / "etc" / "pacman.d" / "mirrorlist"
                
                if mirrorlist_source.exists():
                    shutil.copy2(mirrorlist_source, mirrorlist_target)
                    logger.info("Current mirrorlist copied")
            
            self._update_progress("Network configuration completed", 45)
            return True
            
        except Exception as e:
            error_msg = f"Network setup failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def copy_installer_files(self) -> bool:
        """Copy installer and profile files to target system"""
        try:
            self._update_progress("Copying installer files...", 50)
            
            # Source directories in live environment
            installer_source = Path("/usr/local/bin/Installer")
            profiles_source = Path("/usr/local/bin/profiles")
            
            # Target directories
            target_bin = self.mount_point / "usr" / "local" / "bin"
            target_bin.mkdir(parents=True, exist_ok=True)
            
            installer_target = target_bin / "Installer"
            profiles_target = target_bin / "profiles"
            
            # Copy Installer directory
            if installer_source.exists():
                if installer_target.exists():
                    shutil.rmtree(installer_target)
                shutil.copytree(installer_source, installer_target)
                logger.info(f"Installer directory copied: {installer_source} -> {installer_target}")
            else:
                logger.warning(f"Installer source directory not found: {installer_source}")
            
            # Copy profiles directory
            if profiles_source.exists():
                if profiles_target.exists():
                    shutil.rmtree(profiles_target)
                shutil.copytree(profiles_source, profiles_target)
                logger.info(f"Profiles directory copied: {profiles_source} -> {profiles_target}")
            else:
                logger.warning(f"Profiles source directory not found: {profiles_source}")
            
            self._update_progress("Installer files copied successfully", 55)
            return True
            
        except Exception as e:
            error_msg = f"Failed to copy installer files: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def create_user(self, username: str, password: str, sudo_enabled: bool = True) -> bool:
        """Create user account in chroot environment"""
        try:
            self._update_progress(f"Creating user account: {username}", 60)
            
            # Create user
            self._run_chroot_command([
                "useradd", "-m", "-G", "wheel,audio,video,optical,storage", username
            ])
            
            # Set password
            chpasswd_input = f"{username}:{password}"
            self._run_chroot_command(["chpasswd"], input_data=chpasswd_input)
            
            # Enable sudo if requested
            if sudo_enabled:
                sudoers_line = f"{username} ALL=(ALL:ALL) ALL"
                self._run_chroot_command([
                    "sh", "-c", f"echo '{sudoers_line}' >> /etc/sudoers.d/{username}"
                ])
                logger.info(f"Sudo enabled for user: {username}")
            
            self._update_progress(f"User {username} created successfully", 65)
            return True
            
        except Exception as e:
            error_msg = f"User creation failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def set_hostname(self, hostname: str) -> bool:
        """Set system hostname"""
        try:
            # Set hostname
            hostname_file = self.mount_point / "etc" / "hostname"
            with open(hostname_file, 'w') as f:
                f.write(hostname + '\n')
            
            # Update hosts file
            hosts_file = self.mount_point / "etc" / "hosts"
            hosts_content = f"""127.0.0.1	localhost
::1		localhost
127.0.1.1	{hostname}.localdomain	{hostname}
"""
            with open(hosts_file, 'w') as f:
                f.write(hosts_content)
            
            logger.info(f"Hostname set: {hostname}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to set hostname: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def configure_locale(self, locale: str = "en_US.UTF-8") -> bool:
        """Configure system locale"""
        try:
            self._update_progress("Configuring locale...", 70)
            
            # Enable locale in locale.gen
            locale_gen_file = self.mount_point / "etc" / "locale.gen"
            
            # Read current locale.gen
            with open(locale_gen_file, 'r') as f:
                content = f.read()
            
            # Uncomment the desired locale
            content = content.replace(f"#{locale}", locale)
            
            # Write back
            with open(locale_gen_file, 'w') as f:
                f.write(content)
            
            # Generate locale
            self._run_chroot_command(["locale-gen"])
            
            # Set locale.conf
            locale_conf_file = self.mount_point / "etc" / "locale.conf"
            with open(locale_conf_file, 'w') as f:
                f.write(f"LANG={locale}\n")
            
            logger.info(f"Locale configured: {locale}")
            self._update_progress("Locale configured successfully", 75)
            return True
            
        except Exception as e:
            error_msg = f"Locale configuration failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def configure_timezone(self, timezone: str = "UTC") -> bool:
        """Configure system timezone"""
        try:
            # Set timezone
            self._run_chroot_command([
                "ln", "-sf", f"/usr/share/zoneinfo/{timezone}", "/etc/localtime"
            ])
            
            # Set hardware clock
            self._run_chroot_command(["hwclock", "--systohc"])
            
            logger.info(f"Timezone configured: {timezone}")
            return True
            
        except Exception as e:
            error_msg = f"Timezone configuration failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def install_bootloader(self, disk_path: str) -> bool:
        """Install GRUB bootloader"""
        try:
            self._update_progress("Installing bootloader...", 80)
            
            # Install GRUB to EFI
            self._run_chroot_command([
                "grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", 
                "--bootloader-id=GRUB", "--removable"
            ])
            
            # Generate GRUB configuration
            self._run_chroot_command(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
            
            logger.info("GRUB bootloader installed successfully")
            self._update_progress("Bootloader installed successfully", 85)
            return True
            
        except Exception as e:
            error_msg = f"Bootloader installation failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def enable_services(self) -> bool:
        """Enable essential system services"""
        try:
            services = ["NetworkManager", "systemd-timesyncd"]
            
            for service in services:
                self._run_chroot_command(["systemctl", "enable", service])
                logger.info(f"Service enabled: {service}")
            
            return True
            
        except Exception as e:
            error_msg = f"Service enablement failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
    
    def _run_chroot_command(self, command: List[str], input_data: str = None) -> subprocess.CompletedProcess:
        """Run command in chroot environment"""
        chroot_cmd = ["arch-chroot", str(self.mount_point)] + command
        
        logger.debug(f"Running chroot command: {' '.join(chroot_cmd)}")
        
        result = subprocess.run(
            chroot_cmd,
            input=input_data,
            text=True,
            capture_output=True,
            check=True
        )
        
        return result
    
    def install_packages(self, packages: List[str]) -> bool:
        """Install additional packages in chroot"""
        try:
            if not packages:
                return True
                
            self._update_progress(f"Installing {len(packages)} additional packages...", 90)
            
            # Update package database first
            self._run_chroot_command(["pacman", "-Sy"])
            
            # Install packages
            cmd = ["pacman", "-S", "--noconfirm"] + packages
            self._run_chroot_command(cmd)
            
            logger.info(f"Additional packages installed: {' '.join(packages)}")
            self._update_progress("Additional packages installed", 95)
            return True
            
        except Exception as e:
            error_msg = f"Package installation failed: {e}"
            logger.error(error_msg)
            raise SystemInstallError(error_msg)
