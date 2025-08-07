"""
Profile Selection Screen for GamerX Linux Installer

Provides profile selection with validation and detailed information display.
"""

import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, DataTable, Checkbox
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.app import BaseScreen
from core.profiles import ProfileManager


class ProfilesScreen(BaseScreen):
    """Profile selection screen with validation"""
    
    CSS = """
    ProfilesScreen {
        align: center middle;
    }
    
    .profiles-container {
        width: 90%;
        max-width: 120;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .profiles-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .profiles-table {
        height: 12;
        margin: 1 0;
    }
    
    .profile-details {
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
    
    .detail-header {
        color: $accent;
        text-style: bold;
    }
    
    .detail-text {
        color: $text;
        margin: 0 1;
    }
    
    .warning-text {
        color: $warning;
        text-style: bold;
    }
    
    .error-text {
        color: $error;
        text-style: bold;
    }
    """
    
    selected_profile = reactive("")
    profile_manager = None
    available_profiles = reactive([])
    
    def compose(self) -> ComposeResult:
        """Compose the profile selection screen"""
        yield Header()
        
        with Container(classes="profiles-container"):
            yield Static("🎯 Select Installation Profile", classes="profiles-header")
            yield Static("Choose a desktop environment and software collection", classes="info-text")
            
            yield DataTable(id="profiles_table", classes="profiles-table")
            
            with ScrollableContainer(classes="profile-details"):
                yield Static("Select a profile to view details", id="profile_info")
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("🔄 Refresh", id="refresh_button", variant="default")
                yield Button("Continue →", id="continue_button", variant="primary", disabled=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the profile screen when mounted"""
        self.profile_manager = ProfileManager()
        self.load_profiles()
        self.restore_previous_selection()
    
    def load_profiles(self) -> None:
        """Load available profiles"""
        try:
            profiles = self.profile_manager.get_available_profiles()
            self.available_profiles = profiles
            self.setup_profiles_table()
        except Exception as e:
            self.app.log(f"Error loading profiles: {e}")
            self.available_profiles = []
    
    def setup_profiles_table(self) -> None:
        """Setup the profiles table"""
        table = self.query_one("#profiles_table", DataTable)
        table.add_columns("Profile", "Description", "Status")
        table.cursor_type = "row"
        
        if not self.available_profiles:
            table.add_row("No profiles found", "Check profiles directory", "❌ Error")
            return
        
        for profile in self.available_profiles:
            # Validate profile
            is_valid, validation_msg = self.profile_manager.validate_profile(profile["name"])
            
            status = "✅ Ready" if is_valid else "❌ Invalid"
            description = profile.get("description", "No description available")
            
            table.add_row(
                profile["name"],
                description[:40] + "..." if len(description) > 40 else description,
                status,
                key=profile["name"]
            )
    
    def restore_previous_selection(self) -> None:
        """Restore previously selected profile"""
        config = self.app.get_config()
        if "profile" in config:
            selected_profile = config["profile"]
            table = self.query_one("#profiles_table", DataTable)
            
            # Find and select the row
            for row_key in table.rows:
                if row_key.value == selected_profile:
                    table.cursor_row = table.get_row_index(row_key)
                    self.selected_profile = selected_profile
                    self.update_profile_details(selected_profile)
                    break
    
    def update_profile_details(self, profile_name: str) -> None:
        """Update profile details display"""
        info_widget = self.query_one("#profile_info", Static)
        
        if not profile_name or not self.available_profiles:
            info_widget.update("Select a profile to view details")
            return
        
        # Find profile data
        profile_data = next(
            (p for p in self.available_profiles if p["name"] == profile_name),
            None
        )
        
        if not profile_data:
            info_widget.update("Profile not found")
            return
        
        # Validate profile
        is_valid, validation_msg = self.profile_manager.validate_profile(profile_name)
        
        # Build details text
        details = []
        details.append(f"📋 Profile: {profile_name}")
        details.append(f"📝 Description: {profile_data.get('description', 'No description')}")
        
        # Show package count if available
        try:
            packages = self.profile_manager.get_profile_packages(profile_name)
            details.append(f"📦 Packages: {len(packages)} packages")
            
            # Show sample packages
            if packages:
                sample = ", ".join(packages[:5])
                if len(packages) > 5:
                    sample += f" (and {len(packages) - 5} more)"
                details.append(f"   Examples: {sample}")
        except Exception as e:
            details.append(f"📦 Packages: Error reading package list")
        
        # Show validation status
        if is_valid:
            details.append("✅ Status: Ready for installation")
        else:
            details.append(f"❌ Status: {validation_msg}")
        
        # Show requirements if available
        if "requirements" in profile_data:
            req = profile_data["requirements"]
            details.append("⚙️ Requirements:")
            if "ram" in req:
                details.append(f"   RAM: {req['ram']}GB minimum")
            if "disk" in req:
                details.append(f"   Disk: {req['disk']}GB minimum")
            if "gpu" in req:
                details.append(f"   GPU: {req['gpu']}")
        
        info_widget.update("\n".join(details))
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle profile selection"""
        if event.data_table.id == "profiles_table":
            row_key = event.row_key
            if row_key and row_key.value != "No profiles found":
                self.selected_profile = row_key.value
                self.update_profile_details(self.selected_profile)
                
                # Check if profile is valid
                is_valid, _ = self.profile_manager.validate_profile(self.selected_profile)
                
                # Update continue button state
                continue_btn = self.query_one("#continue_button", Button)
                continue_btn.disabled = not is_valid
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back_button":
            await self.handle_back()
        elif event.button.id == "refresh_button":
            await self.handle_refresh()
        elif event.button.id == "continue_button":
            await self.handle_continue()
    
    async def handle_back(self) -> None:
        """Handle back button press"""
        await self.app.pop_screen()
    
    async def handle_refresh(self) -> None:
        """Handle refresh button press"""
        await self.app.show_message("Refreshing profiles...", "info")
        
        # Reload profiles
        self.load_profiles()
        
        # Clear selection if profile no longer exists
        if self.selected_profile:
            profile_exists = any(p["name"] == self.selected_profile for p in self.available_profiles)
            if not profile_exists:
                self.selected_profile = ""
                continue_btn = self.query_one("#continue_button", Button)
                continue_btn.disabled = True
                info_widget = self.query_one("#profile_info", Static)
                info_widget.update("Select a profile to view details")
        
        await self.app.show_message("Profiles refreshed", "success")
    
    async def handle_continue(self) -> None:
        """Handle continue button press"""
        if not self.selected_profile:
            await self.app.show_message("Please select a profile", "error")
            return
        
        # Final validation
        is_valid, validation_msg = self.profile_manager.validate_profile(self.selected_profile)
        if not is_valid:
            await self.app.show_message(f"Profile validation failed: {validation_msg}", "error")
            return
        
        # Check system requirements if available
        profile_data = next(
            (p for p in self.available_profiles if p["name"] == self.selected_profile),
            None
        )
        
        if profile_data and "requirements" in profile_data:
            req = profile_data["requirements"]
            
            # Check RAM requirement
            if "ram" in req:
                try:
                    from utils.validation import get_system_memory
                    system_ram_gb = get_system_memory() / (1024**3)  # Convert to GB
                    required_ram = req["ram"]
                    
                    if system_ram_gb < required_ram:
                        await self.app.show_message(
                            f"Warning: Profile requires {required_ram}GB RAM, system has {system_ram_gb:.1f}GB",
                            "warning"
                        )
                except Exception:
                    pass  # Continue if we can't check RAM
        
        # Update configuration
        config = self.app.get_config()
        config["profile"] = self.selected_profile
        
        await self.app.show_message(f"Profile set to: {self.selected_profile}", "success")
        
        # Navigate to next screen (summary)
        from ui.screens.summary import SummaryScreen
        await self.app.push_screen(SummaryScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "enter":
            if self.selected_profile:
                await self.handle_continue()
        elif event.key == "f5":
            await self.handle_refresh()
