"""
Locale Selection Screen for GamerX Linux Installer

Provides user-friendly locale selection with country flags and proper names
instead of cryptic locale codes like en_US.UTF-8.
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable, Input
from textual.reactive import reactive
from textual.message import Message
from textual import events

from ui.app import BaseScreen


class LocaleScreen(BaseScreen):
    """Locale selection screen with user-friendly display"""
    
    CSS = """
    LocaleScreen {
        align: center middle;
    }
    
    .locale-container {
        width: 80%;
        max-width: 100;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .locale-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .locale-table {
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
    
    # Common locales with user-friendly display
    LOCALES = [
        ("🇺🇸", "English (United States)", "en_US.UTF-8"),
        ("🇬🇧", "English (United Kingdom)", "en_GB.UTF-8"),
        ("🇨🇦", "English (Canada)", "en_CA.UTF-8"),
        ("🇦🇺", "English (Australia)", "en_AU.UTF-8"),
        ("🇫🇷", "French (France)", "fr_FR.UTF-8"),
        ("🇨🇦", "French (Canada)", "fr_CA.UTF-8"),
        ("🇩🇪", "German (Germany)", "de_DE.UTF-8"),
        ("🇦🇹", "German (Austria)", "de_AT.UTF-8"),
        ("🇨🇭", "German (Switzerland)", "de_CH.UTF-8"),
        ("🇪🇸", "Spanish (Spain)", "es_ES.UTF-8"),
        ("🇲🇽", "Spanish (Mexico)", "es_MX.UTF-8"),
        ("🇦🇷", "Spanish (Argentina)", "es_AR.UTF-8"),
        ("🇮🇹", "Italian (Italy)", "it_IT.UTF-8"),
        ("🇵🇹", "Portuguese (Portugal)", "pt_PT.UTF-8"),
        ("🇧🇷", "Portuguese (Brazil)", "pt_BR.UTF-8"),
        ("🇷🇺", "Russian (Russia)", "ru_RU.UTF-8"),
        ("🇯🇵", "Japanese (Japan)", "ja_JP.UTF-8"),
        ("🇰🇷", "Korean (South Korea)", "ko_KR.UTF-8"),
        ("🇨🇳", "Chinese Simplified (China)", "zh_CN.UTF-8"),
        ("🇹🇼", "Chinese Traditional (Taiwan)", "zh_TW.UTF-8"),
        ("🇳🇱", "Dutch (Netherlands)", "nl_NL.UTF-8"),
        ("🇧🇪", "Dutch (Belgium)", "nl_BE.UTF-8"),
        ("🇸🇪", "Swedish (Sweden)", "sv_SE.UTF-8"),
        ("🇳🇴", "Norwegian (Norway)", "nb_NO.UTF-8"),
        ("🇩🇰", "Danish (Denmark)", "da_DK.UTF-8"),
        ("🇫🇮", "Finnish (Finland)", "fi_FI.UTF-8"),
        ("🇵🇱", "Polish (Poland)", "pl_PL.UTF-8"),
        ("🇨🇿", "Czech (Czech Republic)", "cs_CZ.UTF-8"),
        ("🇭🇺", "Hungarian (Hungary)", "hu_HU.UTF-8"),
        ("🇬🇷", "Greek (Greece)", "el_GR.UTF-8"),
        ("🇹🇷", "Turkish (Turkey)", "tr_TR.UTF-8"),
        ("🇮🇳", "Hindi (India)", "hi_IN.UTF-8"),
        ("🇮🇳", "English (India)", "en_IN.UTF-8"),
        ("🇹🇭", "Thai (Thailand)", "th_TH.UTF-8"),
        ("🇻🇳", "Vietnamese (Vietnam)", "vi_VN.UTF-8"),
    ]
    
    selected_locale = reactive("")
    search_query = reactive("")
    
    def compose(self) -> ComposeResult:
        """Compose the locale selection screen"""
        yield Header()
        
        with Container(classes="locale-container"):
            yield Static("🌍 Select System Language & Locale", classes="locale-header")
            yield Static("Choose your preferred language and regional settings", classes="info-text")
            
            with Container(classes="search-container"):
                yield Input(
                    placeholder="Search languages...",
                    id="locale_search"
                )
            
            yield DataTable(id="locale_table", classes="locale-table")
            
            with Horizontal(classes="button-container"):
                yield Button("← Back", id="back_button", variant="default")
                yield Button("Continue →", id="continue_button", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the locale table when screen mounts"""
        self.setup_locale_table()
        self.restore_previous_selection()
    
    def setup_locale_table(self) -> None:
        """Setup the locale selection table"""
        table = self.query_one("#locale_table", DataTable)
        table.add_columns("Flag", "Language", "Locale Code")
        table.cursor_type = "row"
        
        # Add all locales to table
        for flag, name, code in self.LOCALES:
            table.add_row(flag, name, code, key=code)
    
    def restore_previous_selection(self) -> None:
        """Restore previously selected locale"""
        config = self.app.get_config()
        if "locale" in config:
            selected_locale = config["locale"]
            table = self.query_one("#locale_table", DataTable)
            
            # Find and select the row
            for row_key in table.rows:
                if row_key.value == selected_locale:
                    table.cursor_row = table.get_row_index(row_key)
                    self.selected_locale = selected_locale
                    break
    
    def filter_locales(self, query: str) -> None:
        """Filter locales based on search query"""
        table = self.query_one("#locale_table", DataTable)
        table.clear()
        
        query_lower = query.lower()
        filtered_locales = [
            (flag, name, code) for flag, name, code in self.LOCALES
            if query_lower in name.lower() or query_lower in code.lower()
        ]
        
        for flag, name, code in filtered_locales:
            table.add_row(flag, name, code, key=code)
        
        # Restore selection if it's still visible
        if self.selected_locale:
            for row_key in table.rows:
                if row_key.value == self.selected_locale:
                    table.cursor_row = table.get_row_index(row_key)
                    break
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        if event.input.id == "locale_search":
            self.search_query = event.value
            self.filter_locales(event.value)
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle locale selection"""
        if event.data_table.id == "locale_table":
            row_key = event.row_key
            if row_key:
                self.selected_locale = row_key.value
                
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
        if not self.selected_locale:
            await self.app.show_message("Please select a locale", "error")
            return
        
        # Update configuration
        config = self.app.get_config()
        config["locale"] = self.selected_locale
        
        # Find the display name for the selected locale
        display_name = next(
            (name for flag, name, code in self.LOCALES if code == self.selected_locale),
            self.selected_locale
        )
        
        await self.app.show_message(f"Locale set to: {display_name}", "success")
        
        # Navigate to next screen (timezone)
        from ui.screens.timezone import TimezoneScreen
        await self.app.push_screen(TimezoneScreen())
    
    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "escape":
            await self.handle_back()
        elif event.key == "enter":
            if self.selected_locale:
                await self.handle_continue()
        elif event.key == "ctrl+f":
            # Focus search input
            search_input = self.query_one("#locale_search", Input)
            search_input.focus()
