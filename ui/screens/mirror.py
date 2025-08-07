"""
Mirror Selection Screen for GamerX Linux Installer

Provides mirror selection with parallel speed testing and user-friendly country display.
"""

import asyncio
import aiohttp
import time
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable, ProgressBar
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.app import BaseScreen
from config.mirrors import MIRRORS


class MirrorScreen(BaseScreen):
    """Mirror selection screen with speed testing"""
    
    CSS = """
    MirrorScreen {
        align: center middle;
    }
    
    .mirror-container {
        width: 90%;
        max-width: 120;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .mirror-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .mirror-table {
        height: 18;
        margin: 1 0;
    }
    
    .progress-container {
        height: 4;
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
    
    .testing-text {
        color: $warning;
        text-align: center;
        text-style: bold;
    }
    """
    
    selected_mirror = reactive("")
    testing_in_progress = reactive(False)
    mirror_speeds = reactive({})
    
    def compose(self) -> ComposeResult:
        """Compose the mirror selection screen"""
        yield Header()
        
        with Container(classes="mirror-container"):
            yield Static("🌍 Select Package Mirror", classes="mirror-header")
            yield Static("Choose a fast mirror for downloading packages", classes="info-text")
            
            yield DataTable(id="mirror_table", classes="mirror-table")
            
            with Container(classes="progress-container"):
                yield Static("", id="progress_text", classes="testing-text")
                yield ProgressBar(id="test_progress", show_eta=False)
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("🔄 Test Speed", id="test_button", variant="success")
                yield Button("Continue →", id="continue_button", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the mirror table when screen mounts"""
        self.setup_mirror_table()
        self.restore_previous_selection()
    
    def setup_mirror_table(self) -> None:
        """Setup the mirror selection table"""
        table = self.query_one("#mirror_table", DataTable)
        table.add_columns("Flag", "Country/Provider", "Speed", "URL")
        table.cursor_type = "row"
        
        # Add all mirrors to table
        for mirror in MIRRORS:
            speed_text = self.mirror_speeds.get(mirror["url"], "Not tested")
            table.add_row(
                mirror["flag"],
                mirror["name"],
                speed_text,
                mirror["url"][:50] + "..." if len(mirror["url"]) > 50 else mirror["url"],
                key=mirror["url"]
            )
    
    def restore_previous_selection(self) -> None:
        """Restore previously selected mirror"""
        config = self.app.get_config()
        if "mirror" in config:
            selected_mirror = config["mirror"]
            table = self.query_one("#mirror_table", DataTable)
            
            # Find and select the row
            for row_key in table.rows:
                if row_key.value == selected_mirror:
                    table.cursor_row = table.get_row_index(row_key)
                    self.selected_mirror = selected_mirror
                    break
    
    def update_mirror_table(self) -> None:
        """Update mirror table with speed test results"""
        table = self.query_one("#mirror_table", DataTable)
        table.clear()
        
        # Sort mirrors by speed (fastest first)
        sorted_mirrors = sorted(
            MIRRORS,
            key=lambda m: self.mirror_speeds.get(m["url"], float('inf'))
        )
        
        for mirror in sorted_mirrors:
            speed = self.mirror_speeds.get(mirror["url"], "Not tested")
            if isinstance(speed, (int, float)):
                if speed == float('inf'):
                    speed_text = "Failed"
                else:
                    speed_text = f"{speed:.0f}ms"
            else:
                speed_text = str(speed)
            
            table.add_row(
                mirror["flag"],
                mirror["name"],
                speed_text,
                mirror["url"][:50] + "..." if len(mirror["url"]) > 50 else mirror["url"],
                key=mirror["url"]
            )
        
        # Restore selection if it exists
        if self.selected_mirror:
            for row_key in table.rows:
                if row_key.value == self.selected_mirror:
                    table.cursor_row = table.get_row_index(row_key)
                    break
    
    async def test_mirror_speed(self, mirror_url: str) -> float:
        """Test the speed of a single mirror"""
        try:
            # Test URL - try to download a small file
            test_url = f"{mirror_url}/core/os/x86_64/core.db"
            
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = time.time()
                async with session.head(test_url) as response:
                    if response.status == 200:
                        end_time = time.time()
                        return (end_time - start_time) * 1000  # Convert to milliseconds
                    else:
                        return float('inf')  # Failed
        except Exception:
            return float('inf')  # Failed
    
    async def test_all_mirrors(self) -> None:
        """Test speed of all mirrors in parallel"""
        if self.testing_in_progress:
            return
        
        self.testing_in_progress = True
        progress_text = self.query_one("#progress_text", Static)
        progress_bar = self.query_one("#test_progress", ProgressBar)
        
        progress_text.update("Testing mirror speeds...")
        progress_bar.update(total=len(MIRRORS))
        
        # Test mirrors in batches to avoid overwhelming the system
        batch_size = 5
        completed = 0
        
        for i in range(0, len(MIRRORS), batch_size):
            batch = MIRRORS[i:i + batch_size]
            
            # Test batch in parallel
            tasks = [self.test_mirror_speed(mirror["url"]) for mirror in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update speeds
            for mirror, result in zip(batch, results):
                if isinstance(result, Exception):
                    self.mirror_speeds[mirror["url"]] = float('inf')
                else:
                    self.mirror_speeds[mirror["url"]] = result
                
                completed += 1
                progress_bar.update(progress=completed)
                progress_text.update(f"Testing mirrors... ({completed}/{len(MIRRORS)})")
            
            # Update table with current results
            self.update_mirror_table()
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        # Final update
        progress_text.update("Mirror speed testing complete!")
        progress_bar.update(progress=len(MIRRORS))
        
        # Clear progress after a delay
        await asyncio.sleep(2)
        progress_text.update("")
        progress_bar.update(progress=0)
        
        self.testing_in_progress = False
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle mirror selection"""
        if event.data_table.id == "mirror_table":
            row_key = event.row_key
            if row_key:
                self.selected_mirror = row_key.value
                
                # Update continue button state
                continue_btn = self.query_one("#continue_button", Button)
                continue_btn.disabled = False
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back_button":
            await self.handle_back()
        elif event.button.id == "test_button":
            await self.handle_test_speed()
        elif event.button.id == "continue_button":
            await self.handle_continue()
    
    async def handle_back(self) -> None:
        """Handle back button press"""
        await self.app.pop_screen()
    
    async def handle_test_speed(self) -> None:
        """Handle speed test button press"""
        if not self.testing_in_progress:
            await self.test_all_mirrors()
    
    async def handle_continue(self) -> None:
        """Handle continue button press"""
        if not self.selected_mirror:
            await self.app.show_message("Please select a mirror", "error")
            return
        
        # Update configuration
        config = self.app.get_config()
        config["mirror"] = self.selected_mirror
        
        # Find the display name for the selected mirror
        display_name = next(
            (m["name"] for m in MIRRORS if m["url"] == self.selected_mirror),
            self.selected_mirror
        )
        
        speed_info = ""
        if self.selected_mirror in self.mirror_speeds:
            speed = self.mirror_speeds[self.selected_mirror]
            if isinstance(speed, (int, float)) and speed != float('inf'):
                speed_info = f" ({speed:.0f}ms)"
        
        await self.app.show_message(f"Mirror set to: {display_name}{speed_info}", "success")
        
        # Navigate to next screen (packages)
        from ui.screens.packages import PackagesScreen
        await self.app.push_screen(PackagesScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "enter":
            if self.selected_mirror:
                await self.handle_continue()
        elif event.key == "f5" or event.key == "ctrl+r":
            # Refresh/test speeds
            await self.handle_test_speed()
