"""
Base screen class for GamerX installer screens
"""

from textual.screen import Screen
from textual.widgets import Button, Static
from textual.containers import Horizontal, Vertical
from typing import Dict, Any, Optional
import asyncio

from utils.logging import get_logger

logger = get_logger(__name__)

class BaseInstallerScreen(Screen):
    """Base class for all installer screens"""
    
    def __init__(self, name: str = None, id: str = None, classes: str = None):
        super().__init__(name, id, classes)
        self.installer_data: Dict[str, Any] = {}
        self.logger = get_logger(self.__class__.__name__)
    
    def compose(self):
        """Override in subclasses"""
        yield Static("Base screen - override compose() method")
    
    def on_mount(self):
        """Called when screen is mounted"""
        self.logger.info(f"Mounted {self.__class__.__name__}")
    
    def get_installer_data(self) -> Dict[str, Any]:
        """Get installer data from app"""
        if hasattr(self.app, 'installer_data'):
            return self.app.installer_data
        return {}
    
    def set_installer_data(self, key: str, value: Any):
        """Set installer data in app"""
        if hasattr(self.app, 'installer_data'):
            self.app.installer_data[key] = value
    
    def create_navigation_buttons(self, show_back: bool = True, show_next: bool = True, 
                                next_text: str = "Next", next_action: str = "next"):
        """Create standard navigation buttons"""
        buttons = []
        
        if show_back:
            back_btn = Button("← Back", variant="secondary", id="back_btn")
            buttons.append(back_btn)
        
        if show_next:
            next_btn = Button(next_text, variant="primary", id="next_btn")
            next_btn.action = next_action
            buttons.append(next_btn)
        
        return Horizontal(*buttons, classes="navigation")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back_btn":
            await self.handle_back()
        elif event.button.id == "next_btn":
            await self.handle_next()
    
    async def handle_back(self):
        """Handle back button - override in subclasses"""
        self.app.pop_screen()
    
    async def handle_next(self):
        """Handle next button - override in subclasses"""
        pass
    
    def show_error(self, message: str):
        """Show error message"""
        self.logger.error(message)
        # Could add notification widget here
    
    def show_success(self, message: str):
        """Show success message"""
        self.logger.info(message)
        # Could add notification widget here
