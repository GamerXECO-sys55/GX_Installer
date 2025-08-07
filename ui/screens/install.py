"""
Installation Screen for GamerX Linux Installer

Runs the actual installation process with real-time progress updates.
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, ProgressBar, Log
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.app import BaseScreen
from core.installer import GamerXInstaller


class InstallScreen(BaseScreen):
    """Installation screen with progress tracking"""
    
    CSS = """
    InstallScreen {
        align: center middle;
    }
    
    .install-container {
        width: 95%;
        max-width: 120;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .install-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .progress-container {
        height: 6;
        margin: 1 0;
        border: solid $surface;
        padding: 1;
    }
    
    .log-container {
        height: 16;
        margin: 1 0;
        border: solid $surface;
    }
    
    .button-container {
        height: 3;
        margin-top: 1;
    }
    
    .status-text {
        text-align: center;
        margin: 1 0;
    }
    
    .progress-text {
        color: $text;
        text-align: center;
        margin: 0 0 1 0;
    }
    
    .success-text {
        color: $success;
        text-style: bold;
    }
    
    .error-text {
        color: $error;
        text-style: bold;
    }
    
    .warning-text {
        color: $warning;
        text-style: bold;
    }
    """
    
    installation_complete = reactive(False)
    installation_error = reactive("")
    current_step = reactive("")
    progress_percentage = reactive(0)
    
    def compose(self) -> ComposeResult:
        """Compose the installation screen"""
        yield Header()
        
        with Container(classes="install-container"):
            yield Static("🚀 Installing GamerX Linux", classes="install-header")
            
            with Container(classes="progress-container"):
                yield Static("Preparing installation...", id="step_text", classes="progress-text")
                yield ProgressBar(id="main_progress", show_eta=True, show_percentage=True)
                yield Static("0% Complete", id="progress_text", classes="progress-text")
            
            with Container(classes="log-container"):
                yield Log(id="install_log", auto_scroll=True)
            
            with Horizontal(classes="button-container"):
                yield Button("View Logs", id="logs_button", variant="default", disabled=True)
                yield Button("Reboot", id="reboot_button", variant="success", disabled=True)
                yield Button("Exit", id="exit_button", variant="default", disabled=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Start installation when screen mounts"""
        # Start installation in background
        asyncio.create_task(self.run_installation())
    
    async def run_installation(self) -> None:
        """Run the complete installation process"""
        log_widget = self.query_one("#install_log", Log)
        
        try:
            # Get configuration
            config = self.app.get_config()
            
            # Initialize installer
            installer = GamerXInstaller(config)
            
            # Set up progress callback
            def progress_callback(step: str, percentage: int, message: str = ""):
                self.current_step = step
                self.progress_percentage = percentage
                
                # Update UI
                step_widget = self.query_one("#step_text", Static)
                progress_widget = self.query_one("#main_progress", ProgressBar)
                progress_text = self.query_one("#progress_text", Static)
                
                step_widget.update(step)
                progress_widget.update(progress=percentage)
                progress_text.update(f"{percentage}% Complete")
                
                # Log the step
                if message:
                    log_widget.write_line(f"[{percentage}%] {step}: {message}")
                else:
                    log_widget.write_line(f"[{percentage}%] {step}")
            
            # Log start
            log_widget.write_line("🚀 Starting GamerX Linux installation...")
            log_widget.write_line(f"Target disk: {config.get('disk', {}).get('device', 'Unknown')}")
            log_widget.write_line(f"Profile: {config.get('profile', 'Unknown')}")
            log_widget.write_line("")
            
            # Run installation
            await installer.install(progress_callback)
            
            # Installation completed successfully
            self.installation_complete = True
            
            step_widget = self.query_one("#step_text", Static)
            progress_widget = self.query_one("#main_progress", ProgressBar)
            progress_text = self.query_one("#progress_text", Static)
            
            step_widget.update("✅ Installation completed successfully!")
            step_widget.add_class("success-text")
            progress_widget.update(progress=100)
            progress_text.update("100% Complete")
            
            log_widget.write_line("")
            log_widget.write_line("🎉 Installation completed successfully!")
            log_widget.write_line("Your GamerX Linux system is ready to use.")
            log_widget.write_line("Please reboot to start using your new system.")
            
            # Enable buttons
            reboot_btn = self.query_one("#reboot_button", Button)
            exit_btn = self.query_one("#exit_button", Button)
            logs_btn = self.query_one("#logs_button", Button)
            
            reboot_btn.disabled = False
            exit_btn.disabled = False
            logs_btn.disabled = False
            
        except Exception as e:
            # Installation failed
            self.installation_error = str(e)
            
            step_widget = self.query_one("#step_text", Static)
            progress_text = self.query_one("#progress_text", Static)
            
            step_widget.update(f"❌ Installation failed: {str(e)}")
            step_widget.add_class("error-text")
            progress_text.update("Installation Failed")
            
            log_widget.write_line("")
            log_widget.write_line(f"❌ Installation failed: {str(e)}")
            log_widget.write_line("Please check the logs for more details.")
            
            # Enable exit button
            exit_btn = self.query_one("#exit_button", Button)
            logs_btn = self.query_one("#logs_button", Button)
            exit_btn.disabled = False
            logs_btn.disabled = False
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "logs_button":
            await self.handle_view_logs()
        elif event.button.id == "reboot_button":
            await self.handle_reboot()
        elif event.button.id == "exit_button":
            await self.handle_exit()
    
    async def handle_view_logs(self) -> None:
        """Handle view logs button press"""
        # You could implement a detailed log viewer here
        await self.app.show_message("Detailed logs are displayed in the log area above", "info")
    
    async def handle_reboot(self) -> None:
        """Handle reboot button press"""
        # Show confirmation dialog
        confirm = await self.app.show_confirmation(
            "Reboot System",
            "Are you sure you want to reboot now?\nMake sure to remove the installation media."
        )
        
        if confirm:
            try:
                # Run reboot command
                import subprocess
                subprocess.run(["reboot"], check=True)
            except Exception as e:
                await self.app.show_message(f"Failed to reboot: {e}", "error")
    
    async def handle_exit(self) -> None:
        """Handle exit button press"""
        if self.installation_complete:
            # Show reminder about rebooting
            await self.app.show_message(
                "Installation complete! Don't forget to reboot and remove the installation media.",
                "success"
            )
        else:
            # Show warning about incomplete installation
            confirm = await self.app.show_confirmation(
                "Exit Installer",
                "Installation did not complete successfully.\nAre you sure you want to exit?"
            )
            
            if not confirm:
                return
        
        # Exit the application
        await self.app.exit()
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "ctrl+c":
            # Prevent accidental exit during installation
            if not self.installation_complete and not self.installation_error:
                await self.app.show_message(
                    "Cannot exit during installation. Please wait for completion.",
                    "warning"
                )
            else:
                await self.handle_exit()
        elif event.key == "f12":
            # Quick reboot shortcut (only if installation complete)
            if self.installation_complete:
                await self.handle_reboot()
    
    def can_dismiss(self) -> bool:
        """Prevent dismissing screen during installation"""
        return self.installation_complete or bool(self.installation_error)
