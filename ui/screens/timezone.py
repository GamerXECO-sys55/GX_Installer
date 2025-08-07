"""
Timezone Selection Screen for GamerX Linux Installer

Provides timezone selection with search functionality and regional grouping.
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable, Input
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.app import BaseScreen


class TimezoneScreen(BaseScreen):
    """Timezone selection screen with search and filtering"""
    
    CSS = """
    TimezoneScreen {
        align: center middle;
    }
    
    .timezone-container {
        width: 80%;
        max-width: 100;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .timezone-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .timezone-table {
        height: 20;
        margin: 1 0;
    }
    
    .search-container {
        height: 3;
        margin-bottom: 1;
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
    """
    
    # Common timezones grouped by region
    TIMEZONES = [
        # Americas
        ("🇺🇸", "New York (EST)", "America/New_York"),
        ("🇺🇸", "Los Angeles (PST)", "America/Los_Angeles"),
        ("🇺🇸", "Chicago (CST)", "America/Chicago"),
        ("🇺🇸", "Denver (MST)", "America/Denver"),
        ("🇨🇦", "Toronto", "America/Toronto"),
        ("🇨🇦", "Vancouver", "America/Vancouver"),
        ("🇲🇽", "Mexico City", "America/Mexico_City"),
        ("🇧🇷", "São Paulo", "America/Sao_Paulo"),
        ("🇦🇷", "Buenos Aires", "America/Argentina/Buenos_Aires"),
        
        # Europe
        ("🇬🇧", "London (GMT)", "Europe/London"),
        ("🇫🇷", "Paris (CET)", "Europe/Paris"),
        ("🇩🇪", "Berlin (CET)", "Europe/Berlin"),
        ("🇮🇹", "Rome (CET)", "Europe/Rome"),
        ("🇪🇸", "Madrid (CET)", "Europe/Madrid"),
        ("🇳🇱", "Amsterdam (CET)", "Europe/Amsterdam"),
        ("🇨🇭", "Zurich (CET)", "Europe/Zurich"),
        ("🇦🇹", "Vienna (CET)", "Europe/Vienna"),
        ("🇸🇪", "Stockholm (CET)", "Europe/Stockholm"),
        ("🇳🇴", "Oslo (CET)", "Europe/Oslo"),
        ("🇩🇰", "Copenhagen (CET)", "Europe/Copenhagen"),
        ("🇫🇮", "Helsinki (EET)", "Europe/Helsinki"),
        ("🇵🇱", "Warsaw (CET)", "Europe/Warsaw"),
        ("🇨🇿", "Prague (CET)", "Europe/Prague"),
        ("🇭🇺", "Budapest (CET)", "Europe/Budapest"),
        ("🇬🇷", "Athens (EET)", "Europe/Athens"),
        ("🇷🇺", "Moscow (MSK)", "Europe/Moscow"),
        ("🇹🇷", "Istanbul (TRT)", "Europe/Istanbul"),
        
        # Asia
        ("🇯🇵", "Tokyo (JST)", "Asia/Tokyo"),
        ("🇰🇷", "Seoul (KST)", "Asia/Seoul"),
        ("🇨🇳", "Shanghai (CST)", "Asia/Shanghai"),
        ("🇨🇳", "Beijing (CST)", "Asia/Beijing"),
        ("🇮🇳", "Kolkata (IST)", "Asia/Kolkata"),
        ("🇮🇳", "Mumbai (IST)", "Asia/Kolkata"),
        ("🇹🇭", "Bangkok (ICT)", "Asia/Bangkok"),
        ("🇻🇳", "Ho Chi Minh City", "Asia/Ho_Chi_Minh"),
        ("🇸🇬", "Singapore (SGT)", "Asia/Singapore"),
        ("🇭🇰", "Hong Kong (HKT)", "Asia/Hong_Kong"),
        ("🇹🇼", "Taipei (CST)", "Asia/Taipei"),
        ("🇮🇩", "Jakarta (WIB)", "Asia/Jakarta"),
        ("🇵🇭", "Manila (PHT)", "Asia/Manila"),
        
        # Oceania
        ("🇦🇺", "Sydney (AEDT)", "Australia/Sydney"),
        ("🇦🇺", "Melbourne (AEDT)", "Australia/Melbourne"),
        ("🇦🇺", "Brisbane (AEST)", "Australia/Brisbane"),
        ("🇦🇺", "Perth (AWST)", "Australia/Perth"),
        ("🇳🇿", "Auckland (NZDT)", "Pacific/Auckland"),
        
        # Africa
        ("🇿🇦", "Johannesburg (SAST)", "Africa/Johannesburg"),
        ("🇪🇬", "Cairo (EET)", "Africa/Cairo"),
        ("🇰🇪", "Nairobi (EAT)", "Africa/Nairobi"),
        ("🇳🇬", "Lagos (WAT)", "Africa/Lagos"),
        
        # UTC
        ("🌍", "UTC (Coordinated Universal Time)", "UTC"),
    ]
    
    selected_timezone = reactive("")
    search_query = reactive("")
    
    def compose(self) -> ComposeResult:
        """Compose the timezone selection screen"""
        yield Header()
        
        with Container(classes="timezone-container"):
            yield Static("🕐 Select System Timezone", classes="timezone-header")
            yield Static("Choose your timezone for accurate time display", classes="info-text")
            
            with Container(classes="search-container"):
                yield Input(
                    placeholder="Search timezones (e.g., New York, London, Tokyo)...",
                    id="timezone_search"
                )
            
            yield DataTable(id="timezone_table", classes="timezone-table")
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("Continue →", id="continue_button", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the timezone table when screen mounts"""
        self.setup_timezone_table()
        self.restore_previous_selection()
    
    def setup_timezone_table(self) -> None:
        """Setup the timezone selection table"""
        table = self.query_one("#timezone_table", DataTable)
        table.add_columns("Flag", "City/Region", "Timezone")
        table.cursor_type = "row"
        
        # Add all timezones to table
        for flag, display_name, tz_code in self.TIMEZONES:
            table.add_row(flag, display_name, tz_code, key=tz_code)
    
    def restore_previous_selection(self) -> None:
        """Restore previously selected timezone"""
        config = self.app.get_config()
        if "timezone" in config:
            selected_timezone = config["timezone"]
            table = self.query_one("#timezone_table", DataTable)
            
            # Find and select the row
            for row_key in table.rows:
                if row_key.value == selected_timezone:
                    table.cursor_row = table.get_row_index(row_key)
                    self.selected_timezone = selected_timezone
                    break
    
    def filter_timezones(self, query: str) -> None:
        """Filter timezones based on search query"""
        table = self.query_one("#timezone_table", DataTable)
        table.clear()
        
        query_lower = query.lower()
        filtered_timezones = [
            (flag, display_name, tz_code) for flag, display_name, tz_code in self.TIMEZONES
            if (query_lower in display_name.lower() or 
                query_lower in tz_code.lower() or
                query_lower in tz_code.split('/')[-1].lower())
        ]
        
        for flag, display_name, tz_code in filtered_timezones:
            table.add_row(flag, display_name, tz_code, key=tz_code)
        
        # Restore selection if it's still visible
        if self.selected_timezone:
            for row_key in table.rows:
                if row_key.value == self.selected_timezone:
                    table.cursor_row = table.get_row_index(row_key)
                    break
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        if event.input.id == "timezone_search":
            self.search_query = event.value
            self.filter_timezones(event.value)
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle timezone selection"""
        if event.data_table.id == "timezone_table":
            row_key = event.row_key
            if row_key:
                self.selected_timezone = row_key.value
                
                # Update continue button state
                continue_btn = self.query_one("#continue_button", Button)
                continue_btn.disabled = False
    
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
        if not self.selected_timezone:
            await self.app.show_message("Please select a timezone", "error")
            return
        
        # Update configuration
        config = self.app.get_config()
        config["timezone"] = self.selected_timezone
        
        # Find the display name for the selected timezone
        display_name = next(
            (name for flag, name, code in self.TIMEZONES if code == self.selected_timezone),
            self.selected_timezone
        )
        
        await self.app.show_message(f"Timezone set to: {display_name}", "success")
        
        # Navigate to next screen (kernel)
        from ui.screens.kernel import KernelScreen
        await self.app.push_screen(KernelScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "enter":
            if self.selected_timezone:
                await self.handle_continue()
        elif event.key == "ctrl+f":
            # Focus search input
            search_input = self.query_one("#timezone_search", Input)
            search_input.focus()
