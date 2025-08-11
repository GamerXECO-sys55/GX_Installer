"""
Main Textual application for GamerX installer
Handles screen navigation and global state management
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer
from textual.screen import Screen
from textual.binding import Binding
from typing import Dict, Any, Optional
import asyncio

from utils.logging import get_logger
from config.settings import CONFIG, THEME_COLORS
from ui.screens.welcome import WelcomeScreen
from ui.screens.disk import DiskSelectionScreen
from ui.screens.hostname import HostnameScreen
from ui.screens.user import UserScreen
from ui.screens.locale import LocaleScreen
from ui.screens.timezone import TimezoneScreen
from ui.screens.kernel import KernelScreen
from ui.screens.swap import SwapScreen
from ui.screens.mirror import MirrorScreen
from ui.screens.packages import PackagesScreen
from ui.screens.profiles import ProfilesScreen
from ui.screens.summary import SummaryScreen
from ui.screens.install import InstallScreen

logger = get_logger(__name__)

class GamerXApp(App):
    """Main GamerX installer application"""
    
    CSS = f"""
    Screen {{
        background: {THEME_COLORS['background']};
    }}
    
    .title {{
        color: {THEME_COLORS['primary']};
        text-style: bold;
    }}
    
    .subtitle {{
        color: {THEME_COLORS['secondary']};
    }}
    
    .success {{
        color: {THEME_COLORS['success']};
    }}
    
    .warning {{
        color: {THEME_COLORS['warning']};
    }}
    
    .error {{
        color: {THEME_COLORS['error']};
    }}
    
    .highlight {{
        background: {THEME_COLORS['highlight']};
        color: {THEME_COLORS['background']};
    }}
    
    Button {{
        margin: 1;
    }}
    
    Button.-primary {{
        background: {THEME_COLORS['primary']};
        color: {THEME_COLORS['background']};
    }}
    
    Button.-secondary {{
        background: {THEME_COLORS['secondary']};
        color: {THEME_COLORS['background']};
    }}
    
    Input {{
        margin: 1;
    }}
    
    Select {{
        margin: 1;
    }}
    
    .container {{
        padding: 1;
        margin: 1;
        border: solid {THEME_COLORS['secondary']};
    }}
    
    .progress {{
        color: {THEME_COLORS['success']};
        text-style: bold;
    }}
    """
    
    TITLE = "GamerX Linux Installer"
    SUB_TITLE = "Modular Arch Linux Installation System"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
        ("f1", "help", "Help"),
        ("f10", "debug", "Debug"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config = CONFIG.copy()

        
    def compose(self) -> ComposeResult:
        """Compose the main app layout"""
        yield Header(show_clock=True)
        yield Container(id="main-container")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize the application"""
        logger.info("GamerX installer app started")
        
        # Start with welcome screen
        await self.push_screen(WelcomeScreen(self.config))
    
    def action_quit(self) -> None:
        """Quit the application"""
        logger.info("Application quit requested")
        self.exit()
    
    def action_help(self) -> None:
        """Show help information"""
        self.push_screen("help")
    
    def action_debug(self) -> None:
        """Show debug information"""
        debug_info = f"""
Configuration:
{self.config}

Active Screens: {len(self.screen_stack)}
"""
        self.notify(debug_info, title="Debug Info", timeout=10)
    
    async def navigate_to_screen(self, screen_name: str) -> None:
        """Navigate to a specific screen"""
        screen_map = {
            'welcome': WelcomeScreen,
            'disk': DiskSelectionScreen,
            'hostname': HostnameScreen,
            'user': UserScreen,
            'locale': LocaleScreen,
            'timezone': TimezoneScreen,
            'kernel': KernelScreen,
            'swap': SwapScreen,
            'mirror': MirrorScreen,
            'packages': PackagesScreen,
            'profiles': ProfilesScreen,
            'summary': SummaryScreen,
            'install': InstallScreen,
        }
        
        if screen_name in screen_map:
            screen_class = screen_map[screen_name]
            await self.push_screen(screen_class(self.config))
        else:
            logger.error(f"Unknown screen: {screen_name}")
            self.notify(f"Unknown screen: {screen_name}", severity="error")
    
    async def go_back(self) -> None:
        """Go back to previous screen"""
        if len(self.screen_stack) > 1:
            await self.pop_screen()
        else:
            logger.info("Already at first screen")
    
    def update_config(self, key: str, value: Any) -> None:
        """Update configuration value"""
        self.config[key] = value
        logger.debug(f"Config updated: {key} = {value}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate current configuration"""
        errors = []
        
        # Required fields
        required = ['disk', 'hostname', 'username', 'password']
        for field in required:
            if not self.config.get(field):
                errors.append(f"Missing {field}")
        
        # Validation rules
        if self.config.get('hostname'):
            hostname = self.config['hostname']
            if len(hostname) < 2 or len(hostname) > 63:
                errors.append("Hostname must be 2-63 characters")
        
        if self.config.get('username'):
            username = self.config['username']
            if len(username) < 2 or len(username) > 32:
                errors.append("Username must be 2-32 characters")
        
        if self.config.get('password'):
            password = self.config['password']
            if len(password) < 6:
                errors.append("Password must be at least 6 characters")
        
        return len(errors) == 0, errors
    
    def get_installation_summary(self) -> Dict[str, Any]:
        """Get formatted installation summary"""
        return {
            'System': {
                'Disk': self.config.get('disk', 'Not selected'),
                'Hostname': self.config.get('hostname', 'Not set'),
                'Username': self.config.get('username', 'Not set'),
                'Kernel': self.config.get('kernel', 'linux'),
                'Swap': self.config.get('swap_size', '0'),
            },
            'Localization': {
                'Language': self.config.get('language', 'English (US)'),
                'Locale': self.config.get('locale', 'en_US.UTF-8'),
                'Timezone': self.config.get('timezone', 'UTC'),
            },
            'Network': {
                'Mirror': self.config.get('mirror_country', 'Auto'),
                'Mirror URL': self.config.get('mirror_url', 'Auto-selected'),
            },
            'Software': {
                'Profiles': self.config.get('profiles', []),
                'Additional Packages': self.config.get('additional_packages', []),
            }
        }
    
    async def show_error(self, message: str, title: str = "Error") -> None:
        """Show error message"""
        logger.error(f"{title}: {message}")
        self.notify(message, title=title, severity="error", timeout=10)
    
    async def show_success(self, message: str, title: str = "Success") -> None:
        """Show success message"""
        logger.info(f"{title}: {message}")
        self.notify(message, title=title, severity="information", timeout=5)
    
    async def show_message(self, message: str, message_type: str = "info") -> None:
        """Show message with different types"""
        severity_map = {
            "info": "information",
            "success": "information", 
            "warning": "warning",
            "error": "error"
        }
        severity = severity_map.get(message_type, "information")
        logger.info(f"Message ({message_type}): {message}")
        self.notify(message, severity=severity, timeout=5)
    
    async def show_confirmation(self, message: str, title: str = "Confirm") -> bool:
        """Show confirmation dialog - simplified version"""
        logger.info(f"Confirmation requested: {title} - {message}")
        # For now, just show a notification and return True
        # In a real implementation, this would show a modal dialog
        self.notify(f"{title}: {message}", severity="warning", timeout=10)
        return True
    
    async def show_warning(self, message: str, title: str = "Warning") -> None:
        """Show warning message"""
        logger.warning(f"{title}: {message}")
        self.notify(message, title=title, severity="warning", timeout=8)


