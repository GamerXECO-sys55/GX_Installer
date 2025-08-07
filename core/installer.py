"""
Main installation orchestrator
Coordinates all installation steps with proper error handling and progress tracking
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable
from utils.logging import get_logger
from config.settings import CONFIG, MOUNT_POINT
from core.disk import DiskManager
from core.system import SystemInstaller, SystemInstallError
from core.profiles import ProfileManager, ProfileError

logger = get_logger(__name__)

class InstallationError(Exception):
    """Custom installation error"""
    pass

class GamerXInstaller:
    """Main installation orchestrator"""
    
    def __init__(self, progress_callback: Optional[Callable[[str, int], None]] = None):
        self.progress_callback = progress_callback
        self.disk_manager = DiskManager()
        self.system_installer = SystemInstaller(progress_callback)
        self.profile_manager = ProfileManager()
        self.mount_point = MOUNT_POINT
        
    def _update_progress(self, message: str, percentage: int):
        """Update progress if callback is provided"""
        if self.progress_callback:
            self.progress_callback(message, percentage)
        logger.info(f"Installation Progress {percentage}%: {message}")
    
    async def run_full_installation(self, config: Dict) -> bool:
        """Run complete installation process"""
        try:
            logger.info("Starting GamerX Linux installation...")
            self._update_progress("Starting installation...", 0)
            
            # Validate configuration
            if not self._validate_config(config):
                raise InstallationError("Invalid configuration")
            
            # Step 1: Prepare disk
            await self._prepare_disk(config)
            
            # Step 2: Install base system
            await self._install_base_system(config)
            
            # Step 3: Configure system
            await self._configure_system(config)
            
            # Step 4: Install profiles
            await self._install_profiles(config)
            
            # Step 5: Finalize installation
            await self._finalize_installation(config)
            
            self._update_progress("Installation completed successfully!", 100)
            logger.info("GamerX Linux installation completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Installation failed: {e}"
            logger.error(error_msg)
            self._update_progress(f"Installation failed: {e}", -1)
            
            # Attempt cleanup
            await self._cleanup_on_failure()
            raise InstallationError(error_msg)
    
    def _validate_config(self, config: Dict) -> bool:
        """Validate installation configuration"""
        required_fields = [
            'disk', 'hostname', 'username', 'password', 
            'locale', 'timezone', 'kernel'
        ]
        
        for field in required_fields:
            if field not in config or not config[field]:
                logger.error(f"Missing required configuration: {field}")
                return False
        
        logger.info("Configuration validation passed")
        return True
    
    async def _prepare_disk(self, config: Dict):
        """Prepare disk for installation"""
        try:
            self._update_progress("Preparing disk...", 5)
            
            disk_path = config['disk']
            swap_size = config.get('swap_size', '2G')
            
            # Unmount any existing mounts
            self.disk_manager.unmount_all(disk_path)
            
            # Partition disk
            self.disk_manager.auto_partition_disk(disk_path)
            
            # Format partitions
            self.disk_manager.format_partitions(disk_path)
            
            # Mount partitions
            self.disk_manager.mount_partitions(disk_path)
            
            # Create swap if requested
            if swap_size and swap_size != "0":
                self.disk_manager.create_swap_file(swap_size)
            
            self._update_progress("Disk preparation completed", 10)
            
        except Exception as e:
            raise InstallationError(f"Disk preparation failed: {e}")
    
    async def _install_base_system(self, config: Dict):
        """Install base Arch Linux system"""
        try:
            self._update_progress("Installing base system...", 15)
            
            kernel = config.get('kernel', 'linux')
            additional_packages = config.get('additional_packages', [])
            
            # Install base system
            self.system_installer.install_base_system(kernel, additional_packages)
            
            # Generate fstab
            self.system_installer.generate_fstab()
            
            # Setup network for chroot
            mirror_url = config.get('mirror_url')
            self.system_installer.setup_network_in_chroot(mirror_url)
            
            # Copy installer files
            self.system_installer.copy_installer_files()
            
            self._update_progress("Base system installation completed", 30)
            
        except SystemInstallError as e:
            raise InstallationError(f"Base system installation failed: {e}")
    
    async def _configure_system(self, config: Dict):
        """Configure the installed system"""
        try:
            self._update_progress("Configuring system...", 35)
            
            # Set hostname
            self.system_installer.set_hostname(config['hostname'])
            
            # Configure locale
            locale = config.get('locale', 'en_US.UTF-8')
            self.system_installer.configure_locale(locale)
            
            # Configure timezone
            timezone = config.get('timezone', 'UTC')
            self.system_installer.configure_timezone(timezone)
            
            # Create user
            username = config['username']
            password = config['password']
            sudo_enabled = config.get('sudo_enabled', True)
            self.system_installer.create_user(username, password, sudo_enabled)
            
            # Set root password if provided
            if config.get('root_password'):
                self._set_root_password(config['root_password'])
            
            # Enable essential services
            self.system_installer.enable_services()
            
            self._update_progress("System configuration completed", 50)
            
        except Exception as e:
            raise InstallationError(f"System configuration failed: {e}")
    
    async def _install_profiles(self, config: Dict):
        """Install selected profiles"""
        try:
            profiles = config.get('profiles', [])
            if not profiles:
                logger.info("No profiles selected for installation")
                self._update_progress("Skipping profile installation", 70)
                return
            
            self._update_progress(f"Installing {len(profiles)} profile(s)...", 55)
            
            username = config['username']
            
            # Install yay AUR helper first
            try:
                self.profile_manager.install_yay_and_aur_packages(username)
            except ProfileError as e:
                logger.warning(f"yay installation failed: {e}")
            
            # Install each selected profile
            for i, profile_name in enumerate(profiles):
                progress = 60 + (i * 10 // len(profiles))
                self._update_progress(f"Installing profile: {profile_name}", progress)
                
                try:
                    self.profile_manager.install_profile(profile_name, username)
                    logger.info(f"Profile {profile_name} installed successfully")
                except ProfileError as e:
                    logger.error(f"Profile {profile_name} installation failed: {e}")
                    # Continue with other profiles
            
            # Install HyDE theme if Hyprland profile is selected
            if 'Hyprland' in profiles:
                try:
                    self._update_progress("Installing HyDE theme...", 68)
                    self.profile_manager.install_hyde_theme(username)
                except Exception as e:
                    logger.warning(f"HyDE theme installation failed: {e}")
            
            self._update_progress("Profile installation completed", 70)
            
        except Exception as e:
            raise InstallationError(f"Profile installation failed: {e}")
    
    async def _finalize_installation(self, config: Dict):
        """Finalize installation with bootloader and cleanup"""
        try:
            self._update_progress("Installing bootloader...", 80)
            
            disk_path = config['disk']
            
            # Install bootloader
            self.system_installer.install_bootloader(disk_path)
            
            # Install additional packages if specified
            additional_packages = config.get('additional_packages', [])
            if additional_packages:
                self._update_progress("Installing additional packages...", 90)
                self.system_installer.install_packages(additional_packages)
            
            # Apply any custom configurations
            await self._apply_custom_configs(config)
            
            self._update_progress("Finalizing installation...", 95)
            
            # Sync filesystem
            await asyncio.create_subprocess_exec('sync')
            
            logger.info("Installation finalization completed")
            
        except Exception as e:
            raise InstallationError(f"Installation finalization failed: {e}")
    
    async def _apply_custom_configs(self, config: Dict):
        """Apply custom user configurations"""
        try:
            # Apply any custom settings from config
            custom_configs = config.get('custom_configs', {})
            
            for config_name, config_value in custom_configs.items():
                logger.info(f"Applying custom config: {config_name} = {config_value}")
                # Add specific configuration logic here as needed
            
        except Exception as e:
            logger.warning(f"Custom configuration application failed: {e}")
    
    def _set_root_password(self, root_password: str):
        """Set root password"""
        try:
            chpasswd_input = f"root:{root_password}"
            self.system_installer._run_chroot_command(["chpasswd"], input_data=chpasswd_input)
            logger.info("Root password set successfully")
        except Exception as e:
            logger.error(f"Failed to set root password: {e}")
    
    async def _cleanup_on_failure(self):
        """Cleanup on installation failure"""
        try:
            logger.info("Performing cleanup after installation failure...")
            
            # Unmount all partitions
            if self.mount_point.exists():
                self.disk_manager.unmount_all_from_mount_point()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def get_installation_summary(self, config: Dict) -> Dict[str, any]:
        """Get installation summary for confirmation"""
        try:
            profiles = config.get('profiles', [])
            profile_info = []
            
            for profile_name in profiles:
                summary = self.profile_manager.get_profile_summary(profile_name)
                profile_info.append(summary)
            
            return {
                'disk': config.get('disk', 'Unknown'),
                'hostname': config.get('hostname', 'Unknown'),
                'username': config.get('username', 'Unknown'),
                'locale': config.get('locale', 'en_US.UTF-8'),
                'timezone': config.get('timezone', 'UTC'),
                'kernel': config.get('kernel', 'linux'),
                'swap_size': config.get('swap_size', '0'),
                'profiles': profile_info,
                'additional_packages': config.get('additional_packages', []),
                'total_profiles': len(profiles),
                'estimated_time': self._estimate_installation_time(config)
            }
            
        except Exception as e:
            logger.error(f"Error generating installation summary: {e}")
            return {'error': str(e)}
    
    def _estimate_installation_time(self, config: Dict) -> str:
        """Estimate installation time based on configuration"""
        base_time = 10  # Base system: ~10 minutes
        
        profiles = config.get('profiles', [])
        profile_time = len(profiles) * 5  # ~5 minutes per profile
        
        additional_packages = config.get('additional_packages', [])
        package_time = len(additional_packages) * 0.5  # ~30 seconds per package
        
        total_minutes = base_time + profile_time + package_time
        
        if total_minutes < 60:
            return f"~{int(total_minutes)} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"~{int(hours)}h {int(minutes)}m"
