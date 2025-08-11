"""
Welcome screen for GamerX installer
Shows introduction and system checks
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, ProgressBar
from textual.binding import Binding
import asyncio
from pathlib import Path

from ui.base import BaseInstallerScreen
from utils.logging import get_logger
from utils.validation import validate_network_connection

logger = get_logger(__name__)

class WelcomeScreen(BaseInstallerScreen):
    """Welcome screen with system checks"""
    
    BINDINGS = [
        Binding("enter", "continue", "Continue", priority=True),
        Binding("escape", "quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the welcome screen"""
        with Container(classes="container"):
            with Vertical():
                yield Static("🎮 Welcome to GamerX Linux Installer", classes="title")
                yield Static("Modular Arch Linux Installation System", classes="subtitle")
                yield Static("")
                
                yield Static("System Requirements Check:", classes="subtitle")
                with Container(id="checks-container"):
                    yield Static("⏳ Checking system requirements...", id="check-status")
                    yield ProgressBar(total=100, show_eta=False, id="check-progress")
                
                yield Static("")
                
                with Horizontal():
                    yield Button("Continue", variant="primary", id="continue-btn", disabled=True)
                    yield Button("Quit", variant="default", id="quit-btn")
    
    def on_mount(self) -> None:
        """Run system checks on mount"""
        super().on_mount()
        self.call_after_refresh(self.run_system_checks)
    
    async def run_system_checks(self) -> None:
        """Run system requirement checks"""
        try:
            progress = self.query_one("#check-progress", ProgressBar)
            status = self.query_one("#check-status", Static)
            
            checks = [
                ("Checking root privileges", self.check_root),
                ("Checking live environment", self.check_live_env),
                ("Checking disk space", self.check_disk_space),
                ("Checking network connection", self.check_network),
                ("Checking required tools", self.check_tools),
            ]
            
            total_checks = len(checks)
            passed_checks = 0
            
            for i, (description, check_func) in enumerate(checks):
                status.update(f"⏳ {description}...")
                progress.update(progress=(i * 100) // total_checks)
                
                await asyncio.sleep(0.5)  # Visual delay
                
                try:
                    result = check_func()
                    if result:
                        passed_checks += 1
                        status.update(f"✅ {description}")
                    else:
                        status.update(f"❌ {description} - FAILED")
                        await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Check failed: {description} - {e}")
                    status.update(f"❌ {description} - ERROR: {e}")
                    await asyncio.sleep(1)
            
            progress.update(progress=100)
            
            if passed_checks == total_checks:
                status.update("✅ All system checks passed! Ready to install.")
                self.query_one("#continue-btn", Button).disabled = False
                await self.show_success("System checks completed successfully")
            else:
                status.update(f"❌ {passed_checks}/{total_checks} checks passed. Cannot continue.")
                await self.show_error(f"System checks failed. {passed_checks}/{total_checks} passed.")
                
        except Exception as e:
            logger.error(f"System checks failed: {e}")
            await self.show_error(f"System checks failed: {e}")
    
    def check_root(self) -> bool:
        """Check if running as root"""
        import os
        return os.geteuid() == 0
    
    def check_live_env(self) -> bool:
        """Check if running in Arch Linux live environment"""
        try:
            # Check for live environment indicators
            live_indicators = [
                Path("/run/archiso"),
                Path("/etc/arch-release"),
            ]
            
            return any(indicator.exists() for indicator in live_indicators)
        except Exception:
            return False
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            import shutil
            # Check available space in /tmp (should have at least 1GB)
            _, _, free = shutil.disk_usage("/tmp")
            return free > 1024 * 1024 * 1024  # 1GB
        except Exception:
            return False
    
    def check_network(self) -> bool:
        """Check network connectivity"""
        return validate_network_connection()
    
    def check_tools(self) -> bool:
        """Check required tools are available"""
        try:
            import subprocess
            required_tools = [
                "pacstrap", "genfstab", "arch-chroot",
                "lsblk", "sgdisk", "mkfs.ext4", "mkfs.fat"
            ]
            
            for tool in required_tools:
                result = subprocess.run(
                    ["which", tool], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    logger.error(f"Required tool not found: {tool}")
                    return False
            
            return True
        except Exception:
            return False
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "continue-btn":
            await self.action_continue()
        elif event.button.id == "quit-btn":
            self.app.exit()
    
    async def action_continue(self) -> None:
        """Continue to disk selection"""
        await self.navigate_to("disk")
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()
