"""
Swap Configuration Screen for GamerX Linux Installer

Provides swap configuration with intelligent recommendations based on RAM and disk space.
"""

import asyncio
import shutil
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, RadioSet, RadioButton
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.base import BaseInstallerScreen
from utils.validation import get_system_memory, format_size


class SwapScreen(BaseInstallerScreen):
    """Swap configuration screen with intelligent recommendations"""
    
    CSS = """
    SwapScreen {
        align: center middle;
    }
    
    .swap-container {
        width: 80%;
        max-width: 100;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .swap-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .swap-options {
        height: 12;
        margin: 1 0;
    }
    
    .swap-info {
        height: 8;
        border: solid $surface;
        padding: 1;
        margin: 1 0;
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
    
    .recommended {
        color: $success;
        text-style: bold;
    }
    
    .warning {
        color: $warning;
        text-style: bold;
    }
    
    .error {
        color: $error;
        text-style: bold;
    }
    
    .info-content {
        color: $text;
        margin: 0 1;
    }
    """
    
    selected_swap = reactive("auto")
    system_ram_gb = reactive(0)
    available_space_gb = reactive(0)
    
    def compose(self) -> ComposeResult:
        """Compose the swap configuration screen"""
        yield Header()
        
        with Container(classes="swap-container"):
            yield Static("💾 Configure Swap Space", classes="swap-header")
            yield Static("Swap provides virtual memory when RAM is full", classes="info-text")
            
            with RadioSet(id="swap_options", classes="swap-options"):
                yield RadioButton("🤖 Automatic (Recommended)", value=True, id="swap_auto")
                yield RadioButton("📏 2 GB", id="swap_2gb")
                yield RadioButton("📏 4 GB", id="swap_4gb")
                yield RadioButton("📏 8 GB", id="swap_8gb")
                yield RadioButton("📏 16 GB", id="swap_16gb")
                yield RadioButton("🚫 No Swap", id="swap_none")
            
            with Container(classes="swap-info"):
                yield Static("Loading system information...", id="swap_info_text", classes="info-content")
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("Continue →", id="continue_button", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Load system information on mount"""
        super().on_mount()
        self.call_after_refresh(self.load_system_info)
        self.restore_previous_selection()
        self.update_swap_info()
    
    async def load_system_info(self) -> None:
        """Load system memory and disk space information"""
        try:
            # Get system RAM
            self.system_ram_gb = get_system_memory() // (1024 ** 3)  # Convert to GB
            
            # Get available disk space on selected disk
            config = self.app.get_config()
            if "disk" in config:
                disk_path = config["disk"]
                # For now, estimate available space (this would be more accurate with actual partitioning)
                stat = shutil.disk_usage("/")
                self.available_space_gb = stat.free // (1024 ** 3)  # Convert to GB
            else:
                self.available_space_gb = 100  # Default estimate
                
        except Exception as e:
            self.system_ram_gb = 8  # Default fallback
            self.available_space_gb = 100  # Default fallback
    
    def get_recommended_swap_size(self) -> int:
        """Calculate recommended swap size based on RAM"""
        ram_gb = self.system_ram_gb
        
        if ram_gb <= 2:
            return ram_gb * 2  # 2x RAM for low memory systems
        elif ram_gb <= 8:
            return ram_gb  # 1x RAM for moderate memory systems
        elif ram_gb <= 16:
            return ram_gb // 2  # 0.5x RAM for high memory systems
        else:
            return 8  # Cap at 8GB for very high memory systems
    
    def restore_previous_selection(self) -> None:
        """Restore previously selected swap configuration"""
        config = self.app.get_config()
        if "swap_size" in config:
            swap_size = config["swap_size"]
            
            # Map swap size to radio button
            if swap_size == "auto":
                self.selected_swap = "auto"
                radio_id = "swap_auto"
            elif swap_size == 0:
                self.selected_swap = "none"
                radio_id = "swap_none"
            elif swap_size == 2:
                self.selected_swap = "2gb"
                radio_id = "swap_2gb"
            elif swap_size == 4:
                self.selected_swap = "4gb"
                radio_id = "swap_4gb"
            elif swap_size == 8:
                self.selected_swap = "8gb"
                radio_id = "swap_8gb"
            elif swap_size == 16:
                self.selected_swap = "16gb"
                radio_id = "swap_16gb"
            else:
                self.selected_swap = "auto"
                radio_id = "swap_auto"
            
            # Update radio buttons
            for button_id in ["swap_auto", "swap_2gb", "swap_4gb", "swap_8gb", "swap_16gb", "swap_none"]:
                radio_button = self.query_one(f"#{button_id}", RadioButton)
                radio_button.value = (button_id == radio_id)
    
    def update_swap_info(self) -> None:
        """Update swap information display"""
        info_widget = self.query_one("#swap_info_text", Static)
        
        ram_gb = self.system_ram_gb
        available_gb = self.available_space_gb
        recommended_gb = self.get_recommended_swap_size()
        
        # Build info text
        info_lines = [
            f"System RAM: {ram_gb} GB",
            f"Available Disk Space: ~{available_gb} GB",
            f"Recommended Swap: {recommended_gb} GB",
            ""
        ]
        
        # Add selection-specific information
        if self.selected_swap == "auto":
            info_lines.extend([
                "[bold green]AUTOMATIC CONFIGURATION[/bold green]",
                f"Will create {recommended_gb} GB swap file based on your {ram_gb} GB RAM.",
                "This is the recommended option for most users."
            ])
        elif self.selected_swap == "none":
            if ram_gb >= 16:
                info_lines.extend([
                    "[bold yellow]NO SWAP[/bold yellow]",
                    f"With {ram_gb} GB RAM, you may not need swap space.",
                    "However, swap is still recommended for hibernation support."
                ])
            else:
                info_lines.extend([
                    "[bold red]WARNING: NO SWAP[/bold red]",
                    f"With only {ram_gb} GB RAM, no swap may cause system instability.",
                    "Consider using automatic configuration instead."
                ])
        else:
            # Fixed size selection
            size_map = {"2gb": 2, "4gb": 4, "8gb": 8, "16gb": 16}
            selected_size = size_map.get(self.selected_swap, 0)
            
            if selected_size > available_gb * 0.8:  # More than 80% of available space
                info_lines.extend([
                    f"[bold red]ERROR: {selected_size} GB SWAP[/bold red]",
                    f"Not enough disk space! Only ~{available_gb} GB available.",
                    "Please select a smaller swap size or use automatic."
                ])
            elif selected_size > recommended_gb * 2:  # Much larger than recommended
                info_lines.extend([
                    f"[bold yellow]LARGE SWAP: {selected_size} GB[/bold yellow]",
                    f"This is larger than recommended ({recommended_gb} GB).",
                    "Large swap files may impact performance."
                ])
            else:
                info_lines.extend([
                    f"[bold green]FIXED SWAP: {selected_size} GB[/bold green]",
                    f"Will create a {selected_size} GB swap file.",
                    "Fixed size gives you precise control over swap usage."
                ])
        
        info_widget.update("\n".join(info_lines))
    
    async def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle swap selection change"""
        if event.radio_set.id == "swap_options":
            # Find which radio button is selected
            button_map = {
                "swap_auto": "auto",
                "swap_2gb": "2gb",
                "swap_4gb": "4gb",
                "swap_8gb": "8gb",
                "swap_16gb": "16gb",
                "swap_none": "none"
            }
            
            for button_id, swap_type in button_map.items():
                radio_button = self.query_one(f"#{button_id}", RadioButton)
                if radio_button.value:
                    self.selected_swap = swap_type
                    self.update_swap_info()
                    break
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back_button":
            await self.handle_back()
        elif event.button.id == "continue_button":
            await self.handle_continue()
    
    async def handle_back(self) -> None:
        """Handle back button press"""
        await self.app.pop_screen()
    
    async def handle_continue(self) -> None:
        """Handle continue button press"""
        # Validate swap configuration
        size_map = {"auto": "auto", "2gb": 2, "4gb": 4, "8gb": 8, "16gb": 16, "none": 0}
        swap_size = size_map.get(self.selected_swap, "auto")
        
        # Check if fixed size is too large
        if isinstance(swap_size, int) and swap_size > 0:
            if swap_size > self.available_space_gb * 0.8:
                await self.app.show_message(
                    f"Not enough disk space for {swap_size} GB swap. Please select a smaller size.",
                    "error"
                )
                return
        
        # Update configuration
        config = self.app.get_config()
        config["swap_size"] = swap_size
        
        # Show confirmation message
        if swap_size == "auto":
            recommended = self.get_recommended_swap_size()
            message = f"Swap set to automatic ({recommended} GB recommended)"
        elif swap_size == 0:
            message = "Swap disabled"
        else:
            message = f"Swap set to {swap_size} GB"
        
        await self.app.show_message(message, "success")
        
        # Navigate to next screen (mirror)
        from ui.screens.mirror import MirrorScreen
        await self.app.push_screen(MirrorScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "enter":
            await self.handle_continue()
        elif event.key in ["1", "2", "3", "4", "5", "6"]:
            # Quick selection with number keys
            key_map = {
                "1": "swap_auto",
                "2": "swap_2gb", 
                "3": "swap_4gb",
                "4": "swap_8gb",
                "5": "swap_16gb",
                "6": "swap_none"
            }
            
            button_id = key_map.get(event.key)
            if button_id:
                # Update radio buttons
                for bid in key_map.values():
                    radio_button = self.query_one(f"#{bid}", RadioButton)
                    radio_button.value = (bid == button_id)
                
                # Update selection
                button_map = {
                    "swap_auto": "auto",
                    "swap_2gb": "2gb",
                    "swap_4gb": "4gb", 
                    "swap_8gb": "8gb",
                    "swap_16gb": "16gb",
                    "swap_none": "none"
                }
                self.selected_swap = button_map[button_id]
                self.update_swap_info()
