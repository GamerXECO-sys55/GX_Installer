"""
Kernel Selection Screen for GamerX Linux Installer

Provides kernel selection with descriptions and recommendations.
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable, RadioSet, RadioButton
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.app import BaseScreen


class KernelScreen(BaseScreen):
    """Kernel selection screen with descriptions and recommendations"""
    
    CSS = """
    KernelScreen {
        align: center middle;
    }
    
    .kernel-container {
        width: 80%;
        max-width: 100;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .kernel-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .kernel-options {
        height: 15;
        margin: 1 0;
    }
    
    .kernel-description {
        height: 6;
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
    
    .description-text {
        color: $text;
        margin: 0 1;
    }
    """
    
    # Available kernels with descriptions
    KERNELS = [
        {
            "name": "linux",
            "display": "🐧 Linux (Stable) - Recommended",
            "description": "The standard Arch Linux kernel. This is the most stable and well-tested kernel, receiving regular updates and security patches. Recommended for most users, especially beginners and those who prioritize stability over cutting-edge features.",
            "recommended": True
        },
        {
            "name": "linux-lts",
            "display": "🛡️ Linux LTS (Long Term Support)",
            "description": "Long Term Support kernel with extended maintenance period. This kernel receives security updates for a longer time but may have older features. Ideal for servers, production systems, or users who prefer maximum stability and minimal changes.",
            "recommended": False
        },
        {
            "name": "linux-zen",
            "display": "⚡ Linux Zen (Performance)",
            "description": "Performance-optimized kernel with additional patches for better desktop responsiveness and gaming performance. Includes optimizations for CPU scheduling, memory management, and I/O performance. Great for gaming, multimedia work, and power users.",
            "recommended": False
        },
        {
            "name": "linux-hardened",
            "display": "🔒 Linux Hardened (Security)",
            "description": "Security-focused kernel with additional hardening patches and security features. Includes enhanced protection against various attack vectors but may have slightly reduced performance. Recommended for security-conscious users and sensitive environments.",
            "recommended": False
        }
    ]
    
    selected_kernel = reactive("linux")  # Default to stable kernel
    
    def compose(self) -> ComposeResult:
        """Compose the kernel selection screen"""
        yield Header()
        
        with Container(classes="kernel-container"):
            yield Static("🐧 Select Linux Kernel", classes="kernel-header")
            yield Static("Choose the kernel variant that best fits your needs", classes="info-text")
            
            with RadioSet(id="kernel_options", classes="kernel-options"):
                for kernel in self.KERNELS:
                    yield RadioButton(
                        kernel["display"],
                        value=kernel["name"] == self.selected_kernel,
                        id=f"kernel_{kernel['name']}"
                    )
            
            with Container(classes="kernel-description"):
                yield Static("Select a kernel to see its description", id="description_text", classes="description-text")
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("Continue →", id="continue_button", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the kernel selection when screen mounts"""
        self.restore_previous_selection()
        self.update_description()
    
    def restore_previous_selection(self) -> None:
        """Restore previously selected kernel"""
        config = self.app.get_config()
        if "kernel" in config:
            self.selected_kernel = config["kernel"]
        
        # Update radio buttons
        radio_set = self.query_one("#kernel_options", RadioSet)
        for kernel in self.KERNELS:
            radio_button = self.query_one(f"#kernel_{kernel['name']}", RadioButton)
            radio_button.value = (kernel["name"] == self.selected_kernel)
    
    def update_description(self) -> None:
        """Update the kernel description based on selection"""
        description_widget = self.query_one("#description_text", Static)
        
        # Find the selected kernel
        selected_kernel_info = next(
            (k for k in self.KERNELS if k["name"] == self.selected_kernel),
            self.KERNELS[0]  # Default to first kernel
        )
        
        # Update description text
        description = selected_kernel_info["description"]
        if selected_kernel_info["recommended"]:
            description = f"[bold green]RECOMMENDED[/bold green]\n\n{description}"
        
        description_widget.update(description)
    
    async def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle kernel selection change"""
        if event.radio_set.id == "kernel_options":
            # Find which radio button is selected
            for kernel in self.KERNELS:
                radio_button = self.query_one(f"#kernel_{kernel['name']}", RadioButton)
                if radio_button.value:
                    self.selected_kernel = kernel["name"]
                    self.update_description()
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
        if not self.selected_kernel:
            await self.app.show_message("Please select a kernel", "error")
            return
        
        # Update configuration
        config = self.app.get_config()
        config["kernel"] = self.selected_kernel
        
        # Find the display name for the selected kernel
        display_name = next(
            (k["display"] for k in self.KERNELS if k["name"] == self.selected_kernel),
            self.selected_kernel
        )
        
        await self.app.show_message(f"Kernel set to: {display_name}", "success")
        
        # Navigate to next screen (swap)
        from ui.screens.swap import SwapScreen
        await self.app.push_screen(SwapScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "enter":
            await self.handle_continue()
        elif event.key in ["1", "2", "3", "4"]:
            # Quick selection with number keys
            try:
                index = int(event.key) - 1
                if 0 <= index < len(self.KERNELS):
                    kernel = self.KERNELS[index]
                    self.selected_kernel = kernel["name"]
                    
                    # Update radio buttons
                    radio_set = self.query_one("#kernel_options", RadioSet)
                    for i, k in enumerate(self.KERNELS):
                        radio_button = self.query_one(f"#kernel_{k['name']}", RadioButton)
                        radio_button.value = (i == index)
                    
                    self.update_description()
            except (ValueError, IndexError):
                pass
