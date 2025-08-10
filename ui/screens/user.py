"""
User account configuration screen
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input, Checkbox
from textual.binding import Binding

from ui.base import BaseInstallerScreen
from utils.validation import validate_username, validate_password
from utils.logging import get_logger

logger = get_logger(__name__)

class UserScreen(BaseInstallerScreen):
    """User account configuration screen"""
    
    BINDINGS = [
        Binding("enter", "continue", "Continue"),
        Binding("escape", "back", "Back"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the user screen"""
        with Container(classes="container"):
            with Vertical():
                yield Static("👤 User Account Setup", classes="title")
                yield Static("Create your user account for GamerX Linux", classes="subtitle")
                yield Static("")
                
                yield Static("Username:")
                yield Input(
                    placeholder="Enter username (e.g., gamer)",
                    id="username-input",
                    value=self.get_config('username', '')
                )
                
                yield Static("")
                yield Static("Password:")
                yield Input(
                    placeholder="Enter password",
                    password=True,
                    id="password-input"
                )
                
                yield Static("")
                yield Static("Confirm Password:")
                yield Input(
                    placeholder="Confirm password",
                    password=True,
                    id="confirm-password-input"
                )
                
                yield Static("")
                yield Checkbox(
                    "Enable sudo privileges for this user",
                    value=self.get_config('sudo_enabled', True),
                    id="sudo-checkbox"
                )
                
                yield Static("")
                yield Static("Requirements:", classes="subtitle")
                yield Static("• Username: 2-32 characters, lowercase letters, numbers, underscore")
                yield Static("• Password: At least 6 characters (8+ recommended)")
                yield Static("• Sudo privileges allow administrative access")
                
                yield Static("")
                with Horizontal():
                    yield Button("Back", variant="default", id="back-btn")
                    yield Button("Continue", variant="primary", id="continue-btn")
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Validate inputs as user types"""
        if event.input.id == "username-input":
            username = event.value.strip()
            
            if username:
                is_valid, error_msg = validate_username(username)
                if is_valid:
                    event.input.remove_class("error")
                    event.input.add_class("success")
                    self.update_config('username', username)
                else:
                    event.input.remove_class("success")
                    event.input.add_class("error")
                    event.input.tooltip = error_msg
            else:
                event.input.remove_class("success", "error")
        
        elif event.input.id == "password-input":
            password = event.value
            
            if password:
                is_valid, error_msg = validate_password(password)
                if is_valid:
                    event.input.remove_class("error")
                    event.input.add_class("success")
                else:
                    event.input.remove_class("success")
                    event.input.add_class("error")
                    event.input.tooltip = error_msg
            else:
                event.input.remove_class("success", "error")
        
        elif event.input.id == "confirm-password-input":
            password = self.query_one("#password-input", Input).value
            confirm_password = event.value
            
            if confirm_password:
                if password == confirm_password:
                    event.input.remove_class("error")
                    event.input.add_class("success")
                else:
                    event.input.remove_class("success")
                    event.input.add_class("error")
                    event.input.tooltip = "Passwords do not match"
            else:
                event.input.remove_class("success", "error")
    
    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes"""
        if event.checkbox.id == "sudo-checkbox":
            self.update_config('sudo_enabled', event.value)
    
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
        username_input = self.query_one("#username-input", Input)
        password_input = self.query_one("#password-input", Input)
        confirm_password_input = self.query_one("#confirm-password-input", Input)
        sudo_checkbox = self.query_one("#sudo-checkbox", Checkbox)
        
        username = username_input.value.strip()
        password = password_input.value
        confirm_password = confirm_password_input.value
        
        # Validate username
        if not username:
            await self.show_error("Please enter a username")
            username_input.focus()
            return
        
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            await self.show_error(f"Invalid username: {error_msg}")
            username_input.focus()
            return
        
        # Validate password
        if not password:
            await self.show_error("Please enter a password")
            password_input.focus()
            return
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            await self.show_error(f"Invalid password: {error_msg}")
            password_input.focus()
            return
        
        # Validate password confirmation
        if password != confirm_password:
            await self.show_error("Passwords do not match")
            confirm_password_input.focus()
            return
        
        # Update configuration
        self.update_config('username', username)
        self.update_config('password', password)
        self.update_config('sudo_enabled', sudo_checkbox.value)
        
        await self.navigate_to("locale")
