"""
Profile management and validation system
Handles profile detection, validation, and execution
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from utils.logging import get_logger
from config.settings import PROFILES_DIR, TARGET_PROFILES_DIR, TARGET_INSTALLER_DIR, MOUNT_POINT

logger = get_logger(__name__)

class ProfileError(Exception):
    """Custom profile error"""
    pass

class ProfileManager:
    """Manages installation profiles with validation"""
    
    def __init__(self):
        self.profiles_dir = PROFILES_DIR
        self.target_profiles_dir = TARGET_PROFILES_DIR
        self.target_installer_dir = TARGET_INSTALLER_DIR
        self.mount_point = MOUNT_POINT
    
    def discover_profiles(self) -> List[Dict[str, str]]:
        """Discover available profiles with validation"""
        profiles = []
        
        if not self.profiles_dir.exists():
            logger.warning(f"Profiles directory not found: {self.profiles_dir}")
            return profiles
        
        for profile_dir in self.profiles_dir.iterdir():
            if profile_dir.is_dir():
                profile_info = self._validate_profile(profile_dir)
                if profile_info:
                    profiles.append(profile_info)
        
        logger.info(f"Discovered {len(profiles)} valid profiles")
        return profiles
    
    def _validate_profile(self, profile_path: Path) -> Optional[Dict[str, str]]:
        """Validate a profile directory structure"""
        try:
            profile_name = profile_path.name
            
            # Check for required files
            install_script = profile_path / "install.sh"
            packages_dir = profile_path / "packages"
            package_list = packages_dir / "package-list.txt"
            
            if not install_script.exists():
                logger.warning(f"Profile {profile_name}: missing install.sh")
                return None
            
            if not package_list.exists():
                logger.warning(f"Profile {profile_name}: missing package-list.txt")
                return None
            
            # Check if install.sh is executable
            if not install_script.stat().st_mode & 0o111:
                logger.info(f"Profile {profile_name}: making install.sh executable")
                install_script.chmod(0o755)
            
            # Count packages
            package_count = 0
            try:
                with open(package_list, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            package_count += 1
            except Exception as e:
                logger.warning(f"Profile {profile_name}: error reading package list: {e}")
            
            # Get profile description
            description = self._get_profile_description(profile_name)
            
            # Get profile icon
            icon = self._get_profile_icon(profile_name)
            
            return {
                'name': profile_name,
                'path': str(profile_path),
                'description': description,
                'icon': icon,
                'package_count': package_count,
                'display': f"{icon} {profile_name}",
                'details': f"{description} ({package_count} packages)"
            }
            
        except Exception as e:
            logger.error(f"Profile validation failed for {profile_path}: {e}")
            return None
    
    def _get_profile_description(self, profile_name: str) -> str:
        """Get profile description"""
        descriptions = {
            'Hyprland': 'Modern tiling window manager with beautiful animations',
            'Gaming': 'Optimized gaming setup with Steam, Lutris, and performance tools',
            'Hacking': 'Security and penetration testing tools collection',
            'Development': 'Complete development environment with IDEs and tools',
            'Multimedia': 'Media creation and editing software suite'
        }
        return descriptions.get(profile_name, 'Custom profile configuration')
    
    def _get_profile_icon(self, profile_name: str) -> str:
        """Get profile icon emoji"""
        icons = {
            'Hyprland': '🪟',
            'Gaming': '🎮',
            'Hacking': '🔐',
            'Development': '💻',
            'Multimedia': '🎨'
        }
        return icons.get(profile_name, '📦')
    
    def validate_profile_in_target(self, profile_name: str) -> Tuple[bool, str]:
        """Validate profile exists in target system"""
        try:
            # Check target profile directory
            target_profile_dir = self.target_profiles_dir / profile_name
            if not target_profile_dir.exists():
                return False, f"Profile directory not found in target: {target_profile_dir}"
            
            # Check install script
            install_script = target_profile_dir / "install.sh"
            if not install_script.exists():
                return False, f"install.sh not found: {install_script}"
            
            # Check package list
            package_list = target_profile_dir / "packages" / "package-list.txt"
            if not package_list.exists():
                return False, f"package-list.txt not found: {package_list}"
            
            # Check installer wrapper script
            installer_script = self.target_installer_dir / f"install_{profile_name.lower()}.sh"
            if not installer_script.exists():
                return False, f"Installer script not found: {installer_script}"
            
            return True, f"Profile {profile_name} validated in target system"
            
        except Exception as e:
            return False, f"Profile validation error: {e}"
    
    def get_profile_packages(self, profile_name: str) -> List[str]:
        """Get list of packages for a profile"""
        packages = []
        
        try:
            profile_dir = self.profiles_dir / profile_name
            package_list = profile_dir / "packages" / "package-list.txt"
            
            if package_list.exists():
                with open(package_list, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            packages.append(line)
            
            logger.info(f"Profile {profile_name}: {len(packages)} packages")
            
        except Exception as e:
            logger.error(f"Error reading packages for {profile_name}: {e}")
        
        return packages
    
    def install_profile(self, profile_name: str, username: str) -> bool:
        """Install a profile using the installer script"""
        try:
            logger.info(f"Installing profile: {profile_name}")
            
            # Validate profile exists in target
            valid, msg = self.validate_profile_in_target(profile_name)
            if not valid:
                raise ProfileError(f"Profile validation failed: {msg}")
            
            # Get installer script path
            installer_script = self.target_installer_dir / f"install_{profile_name.lower()}.sh"
            
            # Make sure script is executable
            self._run_chroot_command(["chmod", "+x", str(installer_script).replace(str(self.mount_point), "")])
            
            # Run installer script
            script_path = str(installer_script).replace(str(self.mount_point), "")
            result = self._run_chroot_command([script_path])
            
            logger.info(f"Profile {profile_name} installation completed")
            return True
            
        except Exception as e:
            error_msg = f"Profile installation failed: {e}"
            logger.error(error_msg)
            raise ProfileError(error_msg)
    
    def install_yay_and_aur_packages(self, username: str) -> bool:
        """Install yay AUR helper and any AUR packages"""
        try:
            logger.info("Installing yay AUR helper...")
            
            # Switch to user for yay installation
            yay_commands = [
                "cd /tmp",
                "git clone https://aur.archlinux.org/yay.git",
                "cd yay",
                "makepkg -si --noconfirm --break-system-packages"
            ]
            
            # Run as user
            for cmd in yay_commands:
                self._run_chroot_command([
                    "su", "-", username, "-c", cmd
                ])
            
            logger.info("yay installed successfully")
            return True
            
        except Exception as e:
            error_msg = f"yay installation failed: {e}"
            logger.error(error_msg)
            raise ProfileError(error_msg)
    
    def install_hyde_theme(self, username: str) -> bool:
        """Install HyDE theme for Hyprland"""
        try:
            logger.info("Installing HyDE theme...")
            
            # Clone HyDE repository
            hyde_commands = [
                "cd /tmp",
                "git clone --depth 1 https://github.com/prasanthrangan/hyprdots.git HyDE",
                "cd HyDE",
                "./install.sh"
            ]
            
            # Run as user
            for cmd in hyde_commands:
                self._run_chroot_command([
                    "su", "-", username, "-c", cmd
                ])
            
            logger.info("HyDE theme installed successfully")
            return True
            
        except Exception as e:
            logger.warning(f"HyDE theme installation failed: {e}")
            # Don't fail the entire installation for theme issues
            return False
    
    def _run_chroot_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run command in chroot environment"""
        chroot_cmd = ["arch-chroot", str(self.mount_point)] + command
        
        logger.debug(f"Running chroot command: {' '.join(chroot_cmd)}")
        
        result = subprocess.run(
            chroot_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return result
    
    def get_profile_summary(self, profile_name: str) -> Dict[str, any]:
        """Get comprehensive profile information"""
        try:
            profile_dir = self.profiles_dir / profile_name
            
            if not profile_dir.exists():
                return {'error': f'Profile {profile_name} not found'}
            
            # Get packages
            packages = self.get_profile_packages(profile_name)
            
            # Get file sizes
            total_size = 0
            for file_path in profile_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            # Check for additional scripts
            additional_scripts = []
            for script in profile_dir.glob('*.sh'):
                if script.name != 'install.sh':
                    additional_scripts.append(script.name)
            
            return {
                'name': profile_name,
                'package_count': len(packages),
                'packages': packages,
                'total_size_bytes': total_size,
                'additional_scripts': additional_scripts,
                'description': self._get_profile_description(profile_name),
                'icon': self._get_profile_icon(profile_name)
            }
            
        except Exception as e:
            logger.error(f"Error getting profile summary: {e}")
            return {'error': str(e)}
