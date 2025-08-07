"""
Hostname configuration screen
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input
from textual.binding import Binding

from ui.app import BaseInstallerScreen
from utils.validation import validate_hostname
from utils.logging import get_logger

logger = get_logger(__name__)

class HostnameScreen(BaseInstallerScreen):
    """Hostname configuration screen"""
    
    BINDINGS = [
        Binding("enter", "continue", "Continue"),
        Binding("escape", "back", "Back"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the hostname screen"""
        with Container(classes="container"):
            with Vertical():
                yield Static("🏠 System Hostname", classes="title")
                yield Static("Set the hostname for your GamerX Linux system", classes="subtitle")
                yield Static("")
                
                yield Static("Hostname:")
                yield Input(
                    placeholder="Enter hostname (e.g., gamerx-desktop)",
                    id="hostname-input",
                    value=self.get_config('hostname', '')
                )
                
                yield Static("")
                yield Static("Requirements:", classes="subtitle")
                yield Static("• 2-63 characters long")
                yield Static("• Only letters, numbers, and hyphens")
                yield Static("• Cannot start or end with hyphen")
                yield Static("• Cannot contain consecutive hyphens")
                
                yield Static("")
                with Horizontal():
                    yield Button("Back", variant="default", id="back-btn")
                    yield Button("Continue", variant="primary", id="continue-btn")
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Validate hostname as user types"""
        if event.input.id == "hostname-input":
            hostname = event.value.strip()
            
            if hostname:
                is_valid, error_msg = validate_hostname(hostname)
                if is_valid:
                    event.input.remove_class("error")
                    event.input.add_class("success")
                    self.update_config('hostname', hostname)
                else:
                    event.input.remove_class("success")
                    event.input.add_class("error")
                    event.input.tooltip = error_msg
            else:
                event.input.remove_class("success", "error")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back-btn":
            await self.action_back()
        elif event.button.id == "continue-btn":
            await self.action_continue()
    
    async def action_back(self) -> None:
        """Go back to previous screen"""
        await self.go_back()
    
    async def action_continue(self) -> None:
        """Continue to next screen"""
        hostname_input = self.query_one("#hostname-input", Input)
        hostname = hostname_input.value.strip()
        
        if not hostname:
            await self.show_error("Please enter a hostname")
            hostname_input.focus()
            return
        
        is_valid, error_msg = validate_hostname(hostname)
        if not is_valid:
            await self.show_error(f"Invalid hostname: {error_msg}")
            hostname_input.focus()
            return
        
        self.update_config('hostname', hostname)
        await self.navigate_to("user")
