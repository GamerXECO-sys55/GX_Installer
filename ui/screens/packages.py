"""
Additional Packages Screen for GamerX Linux Installer

Allows users to specify additional packages to install with validation.
"""

import asyncio
import re
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, TextArea, Checkbox
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.base import BaseInstallerScreen


class PackagesScreen(BaseInstallerScreen):
    """Additional packages screen with validation"""
    
    CSS = """
    PackagesScreen {
        align: center middle;
    }
    
    .packages-container {
        width: 80%;
        max-width: 100;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .packages-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .packages-input {
        height: 12;
        margin: 1 0;
        border: solid $surface;
    }
    
    .suggestions-container {
        height: 8;
        margin: 1 0;
        border: solid $surface;
        padding: 1;
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
    
    .validation-text {
        color: $warning;
        margin: 1 0;
    }
    
    .suggestion-item {
        color: $text;
        margin: 0 1;
    }
    
    .category-header {
        color: $accent;
        text-style: bold;
        margin: 1 0 0 0;
    }
    """
    
    # Common package suggestions by category
    PACKAGE_SUGGESTIONS = {
        "Development": [
            "git", "vim", "nano", "code", "docker", "nodejs", "npm", 
            "python-pip", "gcc", "make", "cmake", "gdb"
        ],
        "Media & Graphics": [
            "vlc", "gimp", "blender", "obs-studio", "audacity", 
            "inkscape", "krita", "ffmpeg", "imagemagick"
        ],
        "Internet & Communication": [
            "firefox", "chromium", "discord", "telegram-desktop", 
            "thunderbird", "filezilla", "wget", "curl"
        ],
        "Gaming": [
            "steam", "lutris", "wine", "gamemode", "mangohud", 
            "retroarch", "dosbox", "scummvm"
        ],
        "System Tools": [
            "htop", "neofetch", "tree", "unzip", "zip", "rsync", 
            "tmux", "screen", "lsof", "strace"
        ],
        "Office & Productivity": [
            "libreoffice-fresh", "thunderbird", "keepassxc", 
            "nextcloud-client", "syncthing", "calibre"
        ]
    }
    
    packages_text = reactive("")
    validation_message = reactive("")
    
    def compose(self) -> ComposeResult:
        """Compose the packages screen"""
        yield Header()
        
        with Container(classes="packages-container"):
            yield Static("📦 Additional Packages", classes="packages-header")
            yield Static("Specify additional packages to install (optional)", classes="info-text")
            
            yield TextArea(
                placeholder="Enter package names separated by spaces or newlines...\nExample: git vim firefox steam",
                id="packages_input",
                classes="packages-input"
            )
            
            yield Static("", id="validation_text", classes="validation-text")
            
            with ScrollableContainer(classes="suggestions-container"):
                yield Static("💡 Popular Package Suggestions:", classes="category-header")
                
                for category, packages in self.PACKAGE_SUGGESTIONS.items():
                    yield Static(f"\n{category}:", classes="category-header")
                    package_list = ", ".join(packages)
                    yield Static(package_list, classes="suggestion-item")
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("Skip", id="skip_button", variant="default")
                yield Button("Continue →", id="continue_button", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the packages screen when mounted"""
        self.restore_previous_packages()
    
    def restore_previous_packages(self) -> None:
        """Restore previously entered packages"""
        config = self.app.get_config()
        if "additional_packages" in config:
            packages = config["additional_packages"]
            if packages:
                packages_input = self.query_one("#packages_input", TextArea)
                if isinstance(packages, list):
                    packages_input.text = " ".join(packages)
                else:
                    packages_input.text = str(packages)
                self.packages_text = packages_input.text
    
    def validate_packages(self, packages_text: str) -> tuple[list[str], str]:
        """Validate package names and return cleaned list with validation message"""
        if not packages_text.strip():
            return [], ""
        
        # Split by spaces and newlines, remove empty strings
        packages = [pkg.strip() for pkg in re.split(r'[\s\n]+', packages_text) if pkg.strip()]
        
        valid_packages = []
        invalid_packages = []
        warnings = []
        
        # Package name validation regex (Arch Linux package naming rules)
        package_regex = re.compile(r'^[a-z0-9][a-z0-9+._-]*$')
        
        for pkg in packages:
            # Check basic format
            if not package_regex.match(pkg):
                invalid_packages.append(pkg)
                continue
            
            # Check length
            if len(pkg) > 255:
                invalid_packages.append(pkg)
                continue
            
            # Warn about potentially problematic packages
            if pkg in ['linux', 'linux-lts', 'linux-zen', 'linux-hardened']:
                warnings.append(f"'{pkg}' is a kernel package (already selected)")
                continue
            
            if pkg in ['base', 'base-devel']:
                warnings.append(f"'{pkg}' is a base package (already installed)")
                continue
            
            valid_packages.append(pkg)
        
        # Build validation message
        messages = []
        if valid_packages:
            messages.append(f"✅ {len(valid_packages)} valid packages")
        
        if invalid_packages:
            messages.append(f"❌ Invalid: {', '.join(invalid_packages[:3])}")
            if len(invalid_packages) > 3:
                messages.append(f"... and {len(invalid_packages) - 3} more")
        
        if warnings:
            messages.extend([f"⚠️ {warning}" for warning in warnings[:2]])
        
        validation_msg = " | ".join(messages) if messages else ""
        
        return valid_packages, validation_msg
    
    async def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle package input changes"""
        if event.text_area.id == "packages_input":
            self.packages_text = event.text_area.text
            
            # Validate packages
            valid_packages, validation_msg = self.validate_packages(self.packages_text)
            
            # Update validation display
            validation_widget = self.query_one("#validation_text", Static)
            validation_widget.update(validation_msg)
            
            # Update continue button state
            continue_btn = self.query_one("#continue_button", Button)
            # Allow continue even with no packages (optional step)
            continue_btn.disabled = False
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back_button":
            await self.handle_back()
        elif event.button.id == "skip_button":
            await self.handle_skip()
        elif event.button.id == "continue_button":
            await self.handle_continue()
    
    async def handle_back(self) -> None:
        """Handle back button press"""
        await self.app.pop_screen()
    
    async def handle_skip(self) -> None:
        """Handle skip button press"""
        # Clear packages and continue
        config = self.app.get_config()
        config["additional_packages"] = []
        
        await self.app.show_message("No additional packages will be installed", "info")
        
        # Navigate to next screen (profiles)
        from ui.screens.profiles import ProfilesScreen
        await self.app.push_screen(ProfilesScreen())
    
    async def handle_continue(self) -> None:
        """Handle continue button press"""
        # Validate and save packages
        valid_packages, validation_msg = self.validate_packages(self.packages_text)
        
        # Check for invalid packages
        if "❌" in validation_msg:
            await self.app.show_message("Please fix invalid package names before continuing", "error")
            return
        
        # Update configuration
        config = self.app.get_config()
        config["additional_packages"] = valid_packages
        
        # Show confirmation
        if valid_packages:
            count = len(valid_packages)
            sample = ", ".join(valid_packages[:3])
            if count > 3:
                sample += f" (and {count - 3} more)"
            await self.app.show_message(f"Will install {count} additional packages: {sample}", "success")
        else:
            await self.app.show_message("No additional packages selected", "info")
        
        # Navigate to next screen (profiles)
        from ui.screens.profiles import ProfilesScreen
        await self.app.push_screen(ProfilesScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "ctrl+enter":
            await self.handle_continue()
        elif event.key == "f1":
            # Show help with common packages
            help_text = "Common packages:\n\n"
            for category, packages in list(self.PACKAGE_SUGGESTIONS.items())[:3]:
                help_text += f"{category}: {', '.join(packages[:5])}\n"
            await self.app.show_message(help_text, "info")
