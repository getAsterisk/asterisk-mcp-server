#!/usr/bin/env python3

"""Command-line interface for Asterisk MCP Server.

This module provides the command-line interface for the Asterisk MCP Server.
"""

import argparse
import logging
import sys

from asterisk_mcp_server import __version__
from asterisk_mcp_server.server import AsteriskMCPMiddleware, Config, configure_logging
from asterisk_mcp_server.ui.settings import SettingsUI


def parse_args():
    """
    Parse command-line arguments for the MCP server.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Asterisk MCP: Standalone Middleware MCP Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # API server settings
    api_group = parser.add_argument_group("API Server Settings")
    api_group.add_argument(
        "--api-url", type=str, default=None, help="Base URL for the API server"
    )
    api_group.add_argument(
        "--key",
        type=str,
        default=None,
        help="API key for authentication (REQUIRED for API access)",
    )
    api_group.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout for API requests in seconds (0 for no timeout)",
    )

    # Server settings
    server_group = parser.add_argument_group("MCP Server Settings")
    server_group.add_argument(
        "--server-name", type=str, default=None, help="Name of the MCP server"
    )
    server_group.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default=None,
        help="Transport protocol for the MCP server",
    )
    server_group.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for the SSE server (used with --transport sse)",
    )

    # Logging settings
    logging_group = parser.add_argument_group("Logging Settings")
    logging_group.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Logging level",
    )
    logging_group.add_argument(
        "--no-console",
        action="store_true",
        help="Disable console output (only log to file)",
    )

    # Version
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # Examples
    examples = parser.add_argument_group("Examples")
    examples.add_argument("--example", action="store_true", help=argparse.SUPPRESS)
    # Add example usage
    examples = """
Examples:
  # Start with API key (recommended)
  asterisk-mcp --api-url https://api.asteriskmcp.com --key YOUR_API_KEY

  # Use sse transport instead of stdio 
  asterisk-mcp --api-url https://api.asteriskmcp.com --key YOUR_API_KEY --transport sse --port 8080

  # Increase logging verbosity
  asterisk-mcp --api-url https://api.asteriskmcp.com --key YOUR_API_KEY --log-level DEBUG

  # Use saved configuration
  asterisk-mcp

  # Open settings UI
  asterisk-mcp --settings
"""
    parser.epilog = examples

    # Add settings flag
    parser.add_argument("--settings", action="store_true", help="Open settings UI")

    args = parser.parse_args()

    # Convert timeout of 0 to None (no timeout)
    if args.timeout == 0:
        args.timeout = None

    return args


def main():
    """Main entry point for the MCP server."""
    args = parse_args()

    # Load configuration
    config = Config()

    # Update config with CLI arguments if provided
    updates = {}
    if args.api_url is not None:
        updates["api_url"] = args.api_url
    if args.key is not None:
        updates["api_key"] = args.key
    if args.timeout is not None:
        updates["api_timeout"] = args.timeout
    if args.server_name is not None:
        updates["server_name"] = args.server_name
    if args.transport is not None:
        updates["transport"] = args.transport
    if args.port is not None:
        updates["port"] = args.port
    if args.log_level is not None:
        updates["log_level"] = args.log_level
    if args.no_console:
        updates["no_console"] = True

    if updates:
        config.update(**updates)

    # Open settings UI if requested
    if args.settings:
        ui = SettingsUI(config)
        ui.run()
        return

    # Configure logging
    configure_logging(config.get("log_level"), config.get("no_console"))

    # Validate required parameters
    if not config.get("api_url"):
        logging.error(
            "API URL is required. Use --api-url to specify the API server URL or configure it in settings."
        )
        sys.exit(1)

    if not config.get("api_key"):
        logging.warning(
            "⚠️  No API key provided. Authentication will fail for API requests."
        )
        logging.warning(
            "📝 Get your API key from the dashboard at https://dashboard.asteriskmcp.com"
        )
        logging.warning(
            "🔑 Then run with: asterisk-mcp --api-url <URL> --key <YOUR_API_KEY>"
        )

    # Create and run the MCP server
    try:
        mcp_server = AsteriskMCPMiddleware(config=config)

        logging.info(
            f"Starting MCP server on port {config.get('port')} with {config.get('transport')} transport"
        )
        mcp_server.run(transport=config.get("transport"), port=config.get("port"))
    except Exception as e:
        logging.error(f"Error starting MCP server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
