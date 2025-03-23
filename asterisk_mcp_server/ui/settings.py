#!/usr/bin/env python3

"""Settings UI for Asterisk MCP Server.

This module provides a beautiful and minimal settings UI for Asterisk MCP Server.
"""

import os
import threading


class SettingsUI:
    """Beautiful and minimal settings UI for Asterisk MCP using Dear PyGui."""

    def __init__(self, config):
        """Initialize the settings UI."""
        self.config = config
        # Import Dear PyGui here to avoid dependency issues if it's not used
        try:
            import dearpygui.dearpygui as dpg
            self.dpg = dpg
            self.setup_ui()
        except ImportError:
            print("Error: dearpygui is required for the settings UI.")
            print("Please install it with: pip install dearpygui")
            raise

    def setup_ui(self):
        """Set up the UI components."""
        dpg = self.dpg

        # Initialize Dear PyGui context
        dpg.create_context()

        # Define theme colors
        PRIMARY_COLOR = [66, 150, 250]
        SECONDARY_COLOR = [45, 55, 75]
        ACCENT_COLOR = [255, 180, 0]
        BG_COLOR = [25, 30, 40]
        TEXT_COLOR = [220, 220, 220]
        SUCCESS_COLOR = [0, 200, 83]
        ERROR_COLOR = [255, 65, 65]
        VIOLET_COLOR = [128, 0, 255]

        # Set up themes
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG_COLOR)
                dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT_COLOR)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, PRIMARY_COLOR)
                dpg.add_theme_color(dpg.mvThemeCol_Button, PRIMARY_COLOR)
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered, [c + 30 for c in PRIMARY_COLOR]
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive, [c - 20 for c in PRIMARY_COLOR]
                )
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, SECONDARY_COLOR)
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgHovered, [c + 20 for c in SECONDARY_COLOR]
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgActive, [c + 30 for c in SECONDARY_COLOR]
                )
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, ACCENT_COLOR)
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, PRIMARY_COLOR)
                dpg.add_theme_color(
                    dpg.mvThemeCol_SliderGrabActive, [c + 20 for c in PRIMARY_COLOR]
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_HeaderHovered, [c + 20 for c in SECONDARY_COLOR]
                )
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, PRIMARY_COLOR)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)

        # Create button theme with violet color and white text
        with dpg.theme() as save_button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, VIOLET_COLOR)
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    [min(c + 30, 255) for c in VIOLET_COLOR],
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive, [max(c - 20, 0) for c in VIOLET_COLOR]
                )
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 5)

        # Create header theme
        with dpg.theme() as header_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, PRIMARY_COLOR)

        # Create viewport
        dpg.create_viewport(
            title="Asterisk MCP Settings", width=680, height=600, resizable=True
        )
        dpg.set_viewport_clear_color(BG_COLOR)

        # Add fonts
        with dpg.font_registry():
            default_font = (
                dpg.add_font("OpenSans-Regular.ttf", 18)
                if os.path.exists("OpenSans-Regular.ttf")
                else None
            )
            header_font = (
                dpg.add_font("OpenSans-Bold.ttf", 24)
                if os.path.exists("OpenSans-Bold.ttf")
                else None
            )
            button_font = (
                dpg.add_font("OpenSans-Bold.ttf", 18)
                if os.path.exists("OpenSans-Bold.ttf")
                else None
            )

            # Apply default font if available
            if default_font:
                dpg.bind_font(default_font)

        # Setup Dear PyGui
        dpg.setup_dearpygui()

        # Apply the global theme
        dpg.bind_theme(global_theme)

        # Helper function to create tooltips
        def add_tooltip(item, text):
            with dpg.tooltip(item):
                dpg.add_text(text, wrap=350)

        # Create main window
        with dpg.window(
            label="Asterisk MCP Settings",
            tag="main_window",
            no_close=True,
            width=660,
            height=580,
        ):
            # Add header
            dpg.add_text("Asterisk MCP Settings", tag="title_text")
            if header_font:
                dpg.bind_item_font("title_text", header_font)
            dpg.bind_item_theme("title_text", header_theme)

            dpg.add_separator()
            dpg.add_spacer(height=12)

            # Create collapsing sections for better organization
            # API Settings Section
            with dpg.collapsing_header(label="API Settings", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("API URL:")
                    dpg.add_input_text(
                        tag="api_url",
                        default_value=str(self.config.get("api_url")),
                        width=-1,
                        callback=lambda s, a, u: self.config.update(api_url=a),
                    )
                add_tooltip(
                    "api_url",
                    "The base URL of the Asterisk API server (e.g., https://api.mcp.asterisk.so)",
                )

                with dpg.group(horizontal=True):
                    dpg.add_text("API Key:")
                    dpg.add_input_text(
                        tag="api_key",
                        default_value=str(self.config.get("api_key")),
                        width=-1,
                        password=True,
                        callback=lambda s, a, u: self.config.update(api_key=a),
                    )
                add_tooltip(
                    "api_key", "Your personal API key from the Asterisk dashboard"
                )

            dpg.add_spacer(height=8)

            # Server Settings Section
            with dpg.collapsing_header(label="Server Settings", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("Server Name:")
                    dpg.add_input_text(
                        tag="server_name",
                        default_value=str(self.config.get("server_name")),
                        width=-1,
                        callback=lambda s, a, u: self.config.update(server_name=a),
                    )
                add_tooltip("server_name", "The name of your MCP server instance")

                with dpg.group(horizontal=True):
                    dpg.add_text("Transport:")
                    dpg.add_combo(
                        tag="transport",
                        items=["stdio", "sse"],
                        default_value=self.config.get("transport"),
                        width=-1,
                        callback=lambda s, a, u: self.config.update(transport=a),
                    )
                add_tooltip(
                    "transport",
                    "Communication protocol: stdio for standard I/O, sse for web server",
                )

                with dpg.group(horizontal=True):
                    dpg.add_text("Port:")
                    dpg.add_input_int(
                        tag="port",
                        default_value=int(self.config.get("port")),
                        width=-1,
                        step=10,
                        callback=lambda s, a, u: self.config.update(port=a),
                    )
                add_tooltip(
                    "port", "Port number when using SSE transport (default: 8080)"
                )

            dpg.add_spacer(height=8)

            # Logging Settings Section
            with dpg.collapsing_header(label="Logging Settings", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("Log Level:")
                    dpg.add_combo(
                        tag="log_level",
                        items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default_value=self.config.get("log_level"),
                        width=-1,
                        callback=lambda s, a, u: self.config.update(log_level=a),
                    )
                add_tooltip(
                    "log_level",
                    "Verbosity of logs: DEBUG (most verbose) to CRITICAL (least verbose)",
                )

                dpg.add_checkbox(
                    label="Disable Console Output",
                    tag="no_console",
                    default_value=self.config.get("no_console"),
                    callback=lambda s, a, u: self.config.update(no_console=a),
                )
                add_tooltip(
                    "no_console",
                    "When checked, output will only go to log file, not to console",
                )

            # Status text and button in a centered layout
            dpg.add_spacer(height=10)

            # Center the button properly
            with dpg.group(horizontal=True):
                # Status text centered
                status_text = dpg.add_text("", tag="status_text", color=SUCCESS_COLOR)

            dpg.add_spacer(height=5)

            # Use a separate group for the button with proper centering
            with dpg.group(horizontal=True):
                # Use dynamic width calculation to center
                window_width = 660  # Width of main window
                button_width = 200
                padding = (window_width - button_width) / 2

                # Left padding
                dpg.add_dummy(width=int(padding))

                # Save button with violet styling
                save_button = dpg.add_button(
                    label="Save & Close",
                    tag="save_button",
                    width=button_width,
                    height=35,
                    callback=self._on_save_close,
                )
                dpg.bind_item_theme(save_button, save_button_theme)
                if button_font:
                    dpg.bind_item_font(save_button, button_font)

                # Right padding (not strictly needed but added for symmetry)
                dpg.add_dummy(width=int(padding))

        # Show viewport
        dpg.show_viewport()

    def _on_save_close(self):
        """Handle save and close button."""
        # Save the configuration
        self.config.save()

        # Show success message
        self.dpg.set_value("status_text", "✅ Settings saved successfully!")
        self.dpg.configure_item("status_text", color=[0, 200, 83])

        # Schedule close after a short delay
        threading.Timer(1.0, self.dpg.stop_dearpygui).start()

    def run(self):
        """Run the settings UI."""
        # Start Dear PyGui
        while self.dpg.is_dearpygui_running():
            self.dpg.render_dearpygui_frame()

        # Clean up
        self.dpg.destroy_context()
