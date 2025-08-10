"""
Disk selection screen for GamerX installer
Shows available disks and allows selection
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Select, DataTable
from textual.binding import Binding
import asyncio

from ui.base import BaseInstallerScreen
from core.disk import DiskManager
from utils.logging import get_logger

logger = get_logger(__name__)

class DiskSelectionScreen(BaseInstallerScreen):
    """Disk selection screen"""
    
    BINDINGS = [
        Binding("enter", "continue", "Continue"),
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self, config):
        super().__init__(config)
        self.disk_manager = DiskManager()
        self.selected_disk = None
        self.disks = []
    
    def compose(self) -> ComposeResult:
        """Compose the disk selection screen"""
        with Container(classes="container"):
            with Vertical():
                yield Static("💾 Select Installation Disk", classes="title")
                yield Static("Choose the disk where GamerX Linux will be installed", classes="subtitle")
                yield Static("⚠️  WARNING: All data on the selected disk will be erased!", classes="error")
                yield Static("")
                
                yield Static("Available Disks:", classes="subtitle")
                yield DataTable(id="disk-table", cursor_type="row")
                
                yield Static("")
                yield Static("Selected disk details will appear here...", id="disk-details")
                
                yield Static("")
                with Horizontal():
                    yield Button("Back", variant="default", id="back-btn")
                    yield Button("Refresh", variant="default", id="refresh-btn")
                    yield Button("Continue", variant="primary", id="continue-btn", disabled=True)
    
    async def on_mount(self) -> None:
        """Initialize disk table on mount"""
        super().on_mount()
        await self.refresh_disks()
    
    async def refresh_disks(self) -> None:
        """Refresh disk list"""
        try:
            table = self.query_one("#disk-table", DataTable)
            table.clear(columns=True)
            
            # Setup table columns
            table.add_columns("Device", "Size", "Model", "Type", "Status")
            
            # Get disk information
            self.disks = self.disk_manager.list_disks()
            
            if not self.disks:
                await self.show_error("No suitable disks found for installation")
                return
            
            # Populate table
            for disk in self.disks:
                table.add_row(
                    disk['device'],
                    disk['size'],
                    disk.get('model', 'Unknown'),
                    disk.get('type', 'Unknown'),
                    "Available" if disk.get('mountpoint') is None else "Mounted"
                )
            
            # Restore selection if previously selected
            if self.get_config('disk'):
                selected_disk = self.get_config('disk')
                for i, disk in enumerate(self.disks):
                    if disk['device'] == selected_disk:
                        table.cursor_row = i
                        await self.update_disk_details(disk)
                        break
            
            logger.info(f"Found {len(self.disks)} disks")
            
        except Exception as e:
            logger.error(f"Failed to refresh disks: {e}")
            await self.show_error(f"Failed to refresh disks: {e}")
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle disk selection"""
        try:
            if event.row_index < len(self.disks):
                selected_disk = self.disks[event.row_index]
                self.selected_disk = selected_disk
                await self.update_disk_details(selected_disk)
                
                # Enable continue button
                self.query_one("#continue-btn", Button).disabled = False
                
                # Update config
                self.update_config('disk', selected_disk['device'])
                
        except Exception as e:
            logger.error(f"Error selecting disk: {e}")
            await self.show_error(f"Error selecting disk: {e}")
    
    async def update_disk_details(self, disk):
        """Update disk details display"""
        try:
            details = self.query_one("#disk-details", Static)
            
            # Get detailed disk information
            disk_info = self.disk_manager.get_disk_info(disk['device'])
            
            detail_text = f"""Selected Disk: {disk['device']}
Size: {disk['size']}
Model: {disk.get('model', 'Unknown')}
Type: {disk.get('type', 'Unknown')}
Filesystem: {disk_info.get('fstype', 'None')}
Mount Point: {disk_info.get('mountpoint', 'Not mounted')}

Partition Layout:
"""
            
            # Add partition information
            partitions = disk_info.get('children', [])
            if partitions:
                for part in partitions:
                    detail_text += f"  {part['name']}: {part.get('size', 'Unknown')} ({part.get('fstype', 'Unknown')})\n"
            else:
                detail_text += "  No partitions found\n"
            
            detail_text += f"\n⚠️  All data on {disk['device']} will be permanently erased!"
            
            details.update(detail_text)
            
        except Exception as e:
            logger.error(f"Error updating disk details: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back-btn":
            await self.action_back()
        elif event.button.id == "refresh-btn":
            await self.action_refresh()
        elif event.button.id == "continue-btn":
            await self.action_continue()
    
    async def action_back(self) -> None:
        """Go back to previous screen"""
        await self.go_back()
    
    async def action_refresh(self) -> None:
        """Refresh disk list"""
        await self.refresh_disks()
        await self.show_success("Disk list refreshed")
    
    async def action_continue(self) -> None:
        """Continue to next screen"""
        if not self.selected_disk:
            await self.show_error("Please select a disk first")
            return
        
        # Validate disk selection
        if self.selected_disk.get('mountpoint'):
            await self.show_warning("Selected disk is currently mounted. It will be unmounted during installation.")
        
        # Check disk size (minimum 20GB recommended)
        try:
            size_str = self.selected_disk['size']
            # Parse size (assumes format like "500G" or "1T")
            if 'G' in size_str:
                size_gb = float(size_str.replace('G', ''))
            elif 'T' in size_str:
                size_gb = float(size_str.replace('T', '')) * 1024
            else:
                size_gb = 0
            
            if size_gb < 20:
                await self.show_warning("Selected disk is smaller than 20GB. Installation may fail.")
        except:
            pass  # Skip size validation if parsing fails
        
        await self.navigate_to("hostname")
