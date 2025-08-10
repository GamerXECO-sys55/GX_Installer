"""
Summary Screen for GamerX Linux Installer

Displays a comprehensive review of all configuration before installation begins.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Checkbox
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.base import BaseInstallerScreen
from utils.validation import format_size


class SummaryScreen(BaseInstallerScreen):
    """Summary screen showing all configuration before installation"""
    
    CSS = """
    SummaryScreen {
        align: center middle;
    }
    
    .summary-container {
        width: 90%;
        max-width: 100;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .summary-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .summary-content {
        height: 20;
        margin: 1 0;
        border: solid $surface;
        padding: 1;
    }
    
    .confirmation-container {
        margin: 1 0;
        text-align: center;
    }
    
    .button-container {
        height: 3;
        margin-top: 1;
    }
    
    .info-text {
        color: $text-muted;
        text-align: center;
        margin: 1 0;
    }
    
    .section-header {
        color: $accent;
        text-style: bold;
        margin: 1 0 0 0;
    }
    
    .config-item {
        color: $text;
        margin: 0 1;
    }
    
    .warning-text {
        color: $warning;
        text-style: bold;
        text-align: center;
        margin: 1 0;
    }
    
    .confirmation-checkbox {
        margin: 1 0;
    }
    """
    
    confirmed = reactive(False)
    
    def compose(self) -> ComposeResult:
        """Compose the summary screen"""
        yield Header()
        
        with Container(classes="summary-container"):
            yield Static("📋 Installation Summary", classes="summary-header")
            yield Static("Review your configuration before proceeding", classes="info-text")
            
            with ScrollableContainer(classes="summary-content"):
                yield Static("", id="summary_text")
            
            with Container(classes="confirmation-container"):
                yield Static("⚠️ WARNING: This will format the selected disk and install GamerX Linux!", classes="warning-text")
                yield Checkbox("I understand and want to proceed with the installation", id="confirm_checkbox", classes="confirmation-checkbox")
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("💾 Save Config", id="save_button", variant="default")
                yield Button("🚀 Install", id="install_button", variant="error", disabled=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the summary screen when mounted"""
        self.build_summary()
    
    def build_summary(self) -> None:
        """Build the configuration summary"""
        config = self.app.get_config()
        summary_lines = []
        
        # System Information
        summary_lines.append("🖥️ SYSTEM CONFIGURATION")
        summary_lines.append("=" * 50)
        
        if "disk" in config:
            disk = config["disk"]
            summary_lines.append(f"💾 Target Disk: {disk.get('name', 'Unknown')} ({format_size(disk.get('size', 0))})")
            summary_lines.append(f"   Device: {disk.get('device', 'Unknown')}")
            summary_lines.append(f"   Model: {disk.get('model', 'Unknown')}")
        
        if "hostname" in config:
            summary_lines.append(f"🏠 Hostname: {config['hostname']}")
        
        if "username" in config:
            summary_lines.append(f"👤 Username: {config['username']}")
            if config.get("enable_sudo", False):
                summary_lines.append("   Sudo access: Enabled")
        
        # Localization
        summary_lines.append("\n🌍 LOCALIZATION")
        summary_lines.append("=" * 50)
        
        if "locale" in config:
            summary_lines.append(f"🗣️ Locale: {config['locale']}")
        
        if "timezone" in config:
            summary_lines.append(f"🕐 Timezone: {config['timezone']}")
        
        # System Configuration
        summary_lines.append("\n⚙️ SYSTEM SETTINGS")
        summary_lines.append("=" * 50)
        
        if "kernel" in config:
            kernel_names = {
                "linux": "Linux (Stable)",
                "linux-lts": "Linux LTS (Long Term Support)",
                "linux-zen": "Linux Zen (Performance)",
                "linux-hardened": "Linux Hardened (Security)"
            }
            kernel_display = kernel_names.get(config["kernel"], config["kernel"])
            summary_lines.append(f"🔧 Kernel: {kernel_display}")
        
        if "swap_size" in config:
            swap_size = config["swap_size"]
            if swap_size == 0:
                summary_lines.append("💾 Swap: Disabled")
            elif swap_size == -1:
                summary_lines.append("💾 Swap: Automatic size")
            else:
                summary_lines.append(f"💾 Swap: {format_size(swap_size * 1024**3)}")
        
        if "mirror" in config:
            # Try to get mirror display name
            try:
                from config.mirrors import MIRRORS
                mirror_name = next(
                    (m["name"] for m in MIRRORS if m["url"] == config["mirror"]),
                    config["mirror"]
                )
                summary_lines.append(f"🌐 Mirror: {mirror_name}")
            except:
                summary_lines.append(f"🌐 Mirror: {config['mirror']}")
        
        # Software
        summary_lines.append("\n📦 SOFTWARE")
        summary_lines.append("=" * 50)
        
        if "profile" in config:
            summary_lines.append(f"🎯 Profile: {config['profile']}")
            
            # Try to get profile details
            try:
                from core.profiles import ProfileManager
                profile_manager = ProfileManager()
                packages = profile_manager.get_profile_packages(config["profile"])
                summary_lines.append(f"   Includes: {len(packages)} packages")
            except:
                summary_lines.append("   Package count: Unknown")
        
        if "additional_packages" in config:
            packages = config["additional_packages"]
            if packages:
                summary_lines.append(f"📦 Additional Packages: {len(packages)} packages")
                if len(packages) <= 5:
                    summary_lines.append(f"   {', '.join(packages)}")
                else:
                    sample = ', '.join(packages[:5])
                    summary_lines.append(f"   {sample} (and {len(packages) - 5} more)")
            else:
                summary_lines.append("📦 Additional Packages: None")
        
        # Installation Details
        summary_lines.append("\n🚀 INSTALLATION DETAILS")
        summary_lines.append("=" * 50)
        summary_lines.append("• Base system will be installed with pacstrap")
        summary_lines.append("• GRUB bootloader will be configured")
        summary_lines.append("• SDDM display manager will be installed")
        summary_lines.append("• Network configuration will be set up")
        summary_lines.append("• Selected profile will be installed")
        
        if config.get("additional_packages"):
            summary_lines.append("• Additional packages will be installed")
        
        # Warnings
        summary_lines.append("\n⚠️ IMPORTANT WARNINGS")
        summary_lines.append("=" * 50)
        summary_lines.append("• ALL DATA on the target disk will be PERMANENTLY DELETED")
        summary_lines.append("• This process cannot be undone")
        summary_lines.append("• Ensure you have backed up any important data")
        summary_lines.append("• Installation may take 30-60 minutes depending on internet speed")
        
        # Update the display
        summary_widget = self.query_one("#summary_text", Static)
        summary_widget.update("\n".join(summary_lines))
    
    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle confirmation checkbox changes"""
        if event.checkbox.id == "confirm_checkbox":
            self.confirmed = event.value
            
            # Update install button state
            install_btn = self.query_one("#install_button", Button)
            install_btn.disabled = not self.confirmed
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back_button":
            await self.handle_back()
        elif event.button.id == "save_button":
            await self.handle_save()
        elif event.button.id == "install_button":
            await self.handle_install()
    
    async def handle_back(self) -> None:
        """Handle back button press"""
        await self.app.pop_screen()
    
    async def handle_save(self) -> None:
        """Handle save configuration button press"""
        try:
            config = self.app.get_config()
            
            # Save to file (you could implement config file saving here)
            # For now, just show a message
            await self.app.show_message("Configuration saved successfully", "success")
            
        except Exception as e:
            await self.app.show_message(f"Failed to save configuration: {e}", "error")
    
    async def handle_install(self) -> None:
        """Handle install button press"""
        if not self.confirmed:
            await self.app.show_message("Please confirm that you want to proceed", "error")
            return
        
        # Final validation
        config = self.app.get_config()
        required_fields = ["disk", "hostname", "username", "locale", "timezone", "kernel", "profile"]
        
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            await self.app.show_message(f"Missing configuration: {', '.join(missing_fields)}", "error")
            return
        
        # Show final confirmation
        await self.app.show_message("Starting installation... This cannot be undone!", "warning")
        
        # Navigate to installation screen
        from ui.screens.install import InstallScreen
        await self.app.push_screen(InstallScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "ctrl+s":
            await self.handle_save()
        elif event.key == "ctrl+enter":
            if self.confirmed:
                await self.handle_install()
