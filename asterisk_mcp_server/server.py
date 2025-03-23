#!/usr/bin/env python3

"""Main server implementation for Asterisk MCP Server.

This module defines the MCP server instance for vulnerability scanning of code snippets, codebases and verification of fixes.
Visit https://mcp.asterisk.so for documentation and API key.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

try:
    import httpx
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "Required packages not found. Please install with: pip install mcp[cli] httpx"
    )
    sys.exit(1)

# Configure logging - this will be updated based on config
logger = logging.getLogger("asterisk-mcp")


class Config:
    """Configuration manager for Asterisk MCP."""

    def __init__(self):
        """Initialize configuration with default values."""
        self.config_file = Path("asterisk-config.json")
        self.config = {
            "api_url": "https://api.mcp.asterisk.so",
            "api_key": "",
            "api_timeout": None,
            "server_name": "asterisk-mcp",
            "transport": "stdio",
            "port": 8080,
            "log_level": "INFO",
            "no_console": True,
        }
        self.load()

    def load(self) -> None:
        """Load configuration from file if it exists."""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")

    def update(self, **kwargs) -> None:
        """Update configuration with new values and save."""
        self.config.update(kwargs)
        self.save()

    def get(self, key: str, default: any = None) -> any:
        """Get configuration value by key."""
        return self.config.get(key, default)


def add_line_numbers(code: str) -> str:
    """
    Add line numbers to each line of code in the format "<line_number> | <code>".

    Args:
        code: The code to add line numbers to

    Returns:
        The code with line numbers added
    """
    lines = code.split("\n")
    max_line_num_width = len(str(len(lines)))

    numbered_lines = []
    for i, line in enumerate(lines, 1):
        line_num = str(i).rjust(max_line_num_width)
        numbered_lines.append(f"{line_num} | {line}")

    return "\n".join(numbered_lines)


class AsteriskMCPMiddleware:
    """MCP middleware server for Asterisk security tools."""

    def __init__(self, config: Config):
        """
        Initialize the MCP middleware server.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.mcp = FastMCP(config.get("server_name"))

        # Validate basic configuration initially
        if not self.config.get("api_url"):
            logger.warning("⚠️  No API base URL provided. API requests will fail.")
            logger.warning(
                "📝 Set the API URL with: python -m asterisk_mcp_server --api-url <URL>"
            )

        if not self.config.get("api_key"):
            logger.warning(
                "⚠️  No API key provided. Authentication will fail for API requests."
            )
            logger.warning(
                "📝 Get your API key from the dashboard at https://dashboard.asteriskmcp.com"
            )
            logger.warning(
                "🔑 Then run with: python -m asterisk_mcp_server --api-url <URL> --key <YOUR_API_KEY>"
            )

        self._register_tools()

        logger.info(
            f"Initialized AsteriskMCPMiddleware with name: {config.get('server_name')}"
        )

    def _get_current_config(self) -> Dict[str, any]:
        """
        Get the latest configuration values for every request.

        Returns:
            Dictionary with current configuration values
        """
        # Force config reload before returning values
        self.config.load()

        return {
            "api_base_url": self.config.get("api_url"),
            "api_key": self.config.get("api_key"),
            "api_timeout": self.config.get("api_timeout"),
        }

    def _register_tools(self) -> None:
        """Register all MCP tools with their handlers."""

        # Register the scan_snippet tool
        @self.mcp.tool()
        async def scan_snippet(code_snippet: str) -> str:
            """
            Scans individual code snippets for security vulnerabilities.

            This tool should be used when the user asks to scan or generate a specific snippet, implement a change,
            feature, etc. or specifically mentions to make sure that it's secure. 

            Args:
                code_snippet: The code snippet to analyze for security vulnerabilities

            Returns:
                Markdown-formatted security analysis report
            """
            return await self._handle_scan_snippet(code_snippet)

        # Register the scan_codebase tool
        @self.mcp.tool()
        async def scan_codebase(file_paths: List[str]) -> str:
            """
            Scans the entire codebase for security vulnerabilities.

            If the user asks to scan the entire codebase for security issues, this tool should be used.
            Provide absolute file paths to the files you want to scan. The MCP server will read the file
            contents from your local machine and send them to the API server for analysis.

            Args:
                file_paths: List of absolute paths to the files to analyze

            Returns:
                Markdown-formatted security analysis report with line numbers
            """
            return await self._handle_scan_codebase(file_paths)

        # Register the verify tool
        @self.mcp.tool()
        async def verify(changes: List[Dict[str, str]]) -> str:
            """
            Verifies if code changes made thus far introduce any security vulnerabilities.

            If the user asks to verify or check for security issues after a long chat or interaction,
            this tool should be used to pass in code changes made during the chat. Each change should
            include the absolute file path and the modified code snippet.

            Args:
                changes: List of dictionaries with 'file_path' (absolute) and 'code_snippet' (changed code)

            Returns:
                Markdown-formatted security verification report
            """
            return await self._handle_verify(changes)

        # Register the settings tool
        @self.mcp.tool()
        async def settings(command: str = "") -> str:
            """
            Opens the settings UI when the user enters "/asterisk".

            This tool should only be called when the user enters "/asterisk" in the chat.
            It opens a beautiful yet minimal settings UI that looks good in every operating system.
            The UI lets users configure Asterisk MCP without using CLI flags.

            Args:
                command: The command entered by the user (must be "/asterisk")

            Returns:
                A message indicating the settings UI was opened
            """
            if command == "/asterisk":
                # Import here to avoid circular imports
                from asterisk_mcp_server.ui.settings import SettingsUI
                
                # Create and run settings UI
                ui = SettingsUI(self.config)
                ui.run()
                return "Settings updated successfully!"
            return "Invalid command. Use /asterisk to open settings."

    async def _handle_scan_snippet(self, code_snippet: str) -> str:
        """
        Handle the scan_snippet tool request by forwarding to the API server.

        Args:
            code_snippet: The code snippet to analyze

        Returns:
            Markdown-formatted security analysis report
        """
        try:
            # Get fresh configuration before every request
            config = self._get_current_config()
            api_base_url = config["api_base_url"]
            api_key = config["api_key"]
            api_timeout = config["api_timeout"]

            logger.info("Forwarding scan_snippet request to API")

            # Prepare request payload
            payload = {"code_snippet": code_snippet}

            # Log snippet size
            logger.info(f"Snippet size: {len(code_snippet)} characters")

            # Prepare headers with API key if available
            headers = {"X-API-Key": api_key} if api_key else {}

            # Send request to API
            try:
                async with httpx.AsyncClient(timeout=api_timeout) as client:
                    logger.info(f"Sending request to {api_base_url}/scan/snippet")
                    response = await client.post(
                        f"{api_base_url}/scan/snippet", json=payload, headers=headers
                    )

                    # Check if request was successful
                    response.raise_for_status()

                    # Parse the response to get the markdown content
                    response_data = response.json()
                    markdown_content = response_data.get("markdown_content", "")

                    # Return the markdown content directly
                    return markdown_content
            except httpx.ConnectError as conn_err:
                logger.error(f"Connection error to API server: {conn_err}")
                return f"""# Security Analysis Error

## Error Details

Failed to connect to the API server: {str(conn_err)}

## Recommendations

Please check that the API server is running and accessible at {api_base_url}.
"""
            except httpx.TimeoutException as timeout_err:
                logger.error(f"Request to API server timed out: {timeout_err}")
                return f"""# Security Analysis Error

## Error Details

The request to the API server timed out: {str(timeout_err)}

## Recommendations

Please consider increasing the API timeout using the --api-timeout command-line option or setting it to 0 for no timeout.
"""
            except httpx.HTTPStatusError as http_err:
                logger.error(f"HTTP error from API server: {http_err}")
                status_code = (
                    http_err.response.status_code
                    if hasattr(http_err, "response")
                    else "unknown"
                )
                error_detail = (
                    http_err.response.text
                    if hasattr(http_err, "response")
                    else str(http_err)
                )

                # Check for authentication errors
                if status_code == 401:
                    return f"""# Security Analysis Error

## Authentication Error

Your API key is missing or invalid. Please provide a valid API key using the --key option when starting the MCP server.

Error details: {error_detail}
"""
                # Check for rate limiting
                elif status_code == 429:
                    return f"""# Security Analysis Error

## Rate Limit Exceeded

You have exceeded the rate limit for API requests. Please try again later.

Error details: {error_detail}
"""
                else:
                    return f"""# Security Analysis Error

## Error Details

The API server returned an HTTP error: {status_code}

Error details: {error_detail}

## Recommendations

Please try again or contact support if the issue persists.
"""

        except Exception as e:
            logger.error(f"Error in scan_snippet middleware: {str(e)}", exc_info=True)
            # Return a basic Markdown error message with the actual error message
            return f"""# Security Analysis Error

## Error Details

An error occurred during the security analysis: {str(e) or "Unknown error (no error message provided)"}

## Recommendations

Please try again or contact support if the issue persists.
"""

    async def _handle_scan_codebase(self, file_paths: List[str]) -> str:
        """
        Handle the scan_codebase tool request by reading files from the local machine and forwarding to the API server.

        Args:
            file_paths: List of absolute paths to the files to analyze

        Returns:
            Markdown-formatted security analysis report with line numbers
        """
        try:
            # Get fresh configuration before every request
            config = self._get_current_config()
            api_base_url = config["api_base_url"]
            api_key = config["api_key"]
            api_timeout = config["api_timeout"]

            logger.info(f"Processing scan_codebase request for {len(file_paths)} files")

            # Read file contents from the local machine
            files_data = []
            for file_path in file_paths:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()

                    # Add numbered content to files_data
                    numbered_content = add_line_numbers(file_content)
                    files_data.append(
                        {"file_path": file_path, "file_content": numbered_content}
                    )
                except Exception as file_err:
                    logger.error(f"Error reading file {file_path}: {str(file_err)}")
                    files_data.append(
                        {
                            "file_path": file_path,
                            "file_content": f"# Error reading file\n{str(file_err)}",
                        }
                    )

            if not files_data:
                return """# Security Analysis Error

## Error Details

No valid files were found to analyze.

## Recommendations

Please check that the provided file paths exist and are readable.
"""

            # Prepare request payload
            payload = {"files": files_data}

            # Log payload size for debugging
            payload_size = sum(
                len(file_data["file_content"]) for file_data in files_data
            )
            logger.info(
                f"Payload size: {payload_size} characters from {len(files_data)} files"
            )

            # Prepare headers with API key if available
            headers = {"X-API-Key": api_key} if api_key else {}

            # Send request to API
            try:
                async with httpx.AsyncClient(timeout=api_timeout) as client:
                    logger.info(f"Sending request to {api_base_url}/scan/codebase")
                    response = await client.post(
                        f"{api_base_url}/scan/codebase", json=payload, headers=headers
                    )

                    # Check if request was successful
                    response.raise_for_status()

                    # Parse the response to get the markdown content
                    response_data = response.json()
                    markdown_content = response_data.get("markdown_content", "")

                    # Return the markdown content directly
                    return markdown_content
            except httpx.ConnectError as conn_err:
                logger.error(f"Connection error to API server: {conn_err}")
                return f"""# Security Analysis Error

## Error Details

Failed to connect to the API server: {str(conn_err)}

## Recommendations

Please check that the API server is running and accessible at {api_base_url}.
"""
            except httpx.TimeoutException as timeout_err:
                logger.error(f"Request to API server timed out: {timeout_err}")
                return f"""# Security Analysis Error

## Error Details

The request to the API server timed out: {str(timeout_err)}

## Recommendations

Please consider increasing the API timeout using the --api-timeout command-line option or setting it to 0 for no timeout.
"""
            except httpx.HTTPStatusError as http_err:
                logger.error(f"HTTP error from API server: {http_err}")
                status_code = (
                    http_err.response.status_code
                    if hasattr(http_err, "response")
                    else "unknown"
                )
                error_detail = (
                    http_err.response.text
                    if hasattr(http_err, "response")
                    else str(http_err)
                )

                # Check for authentication errors
                if status_code == 401:
                    return f"""# Security Analysis Error

## Authentication Error

Your API key is missing or invalid. Please provide a valid API key using the --key option when starting the MCP server.

Error details: {error_detail}
"""
                # Check for rate limiting
                elif status_code == 429:
                    return f"""# Security Analysis Error

## Rate Limit Exceeded

You have exceeded the rate limit for API requests. Please try again later.

Error details: {error_detail}
"""
                else:
                    return f"""# Security Analysis Error

## Error Details

The API server returned an HTTP error: {status_code}

Error details: {error_detail}

## Recommendations

Please try again or contact support if the issue persists.
"""

        except Exception as e:
            logger.error(f"Error in scan_codebase middleware: {str(e)}", exc_info=True)
            # Return a basic Markdown error message with the actual error message
            return f"""# Security Analysis Error

## Error Details

An error occurred during the security analysis: {str(e) or "Unknown error (no error message provided)"}

## Recommendations

Please try again or contact support if the issue persists.
"""

    async def _handle_verify(self, changes: List[Dict[str, str]]) -> str:
        """
        Handle the verify tool request by forwarding to the API server.

        Args:
            changes: List of dictionaries with 'file_path' and 'code_snippet' keys

        Returns:
            Markdown-formatted security verification report
        """
        try:
            # Get fresh configuration before every request
            config = self._get_current_config()
            api_base_url = config["api_base_url"]
            api_key = config["api_key"]
            api_timeout = config["api_timeout"]

            logger.info(
                f"Forwarding verify request to API for {len(changes)} code changes"
            )

            # Validate the changes
            valid_changes = []
            for change in changes:
                if (
                    isinstance(change, dict)
                    and "file_path" in change
                    and "code_snippet" in change
                ):
                    valid_changes.append(change)
                else:
                    logger.warning(f"Invalid change format: {change}")

            if not valid_changes:
                return """# Code Verification Error

## Error Details

No valid code changes provided.

## Recommendations

Each change must include a 'file_path' and 'code_snippet'.
"""

            # Prepare request payload with the changes
            payload = {"changes": valid_changes}

            # Log payload size for debugging
            payload_size = sum(len(change["code_snippet"]) for change in valid_changes)
            logger.info(
                f"Payload size: {payload_size} characters from {len(valid_changes)} changes"
            )

            # Prepare headers with API key if available
            headers = {"X-API-Key": api_key} if api_key else {}

            # Send request to API
            try:
                async with httpx.AsyncClient(timeout=api_timeout) as client:
                    logger.info(f"Sending request to {api_base_url}/verify")
                    response = await client.post(
                        f"{api_base_url}/verify", json=payload, headers=headers
                    )

                    # Check if request was successful
                    response.raise_for_status()

                    # Parse the response to get the markdown content
                    response_data = response.json()
                    markdown_content = response_data.get("markdown_content", "")

                    # Return the markdown content directly
                    return markdown_content
            except httpx.ConnectError as conn_err:
                logger.error(f"Connection error to API server: {conn_err}")
                return f"""# Code Verification Error

## Error Details

Failed to connect to the API server: {str(conn_err)}

## Recommendations

Please check that the API server is running and accessible at {api_base_url}.
"""
            except httpx.TimeoutException as timeout_err:
                logger.error(f"Request to API server timed out: {timeout_err}")
                return f"""# Code Verification Error

## Error Details

The request to the API server timed out: {str(timeout_err)}

## Recommendations

Please consider increasing the API timeout using the --api-timeout command-line option or setting it to 0 for no timeout.
"""
            except httpx.HTTPStatusError as http_err:
                logger.error(f"HTTP error from API server: {http_err}")
                status_code = (
                    http_err.response.status_code
                    if hasattr(http_err, "response")
                    else "unknown"
                )
                error_detail = (
                    http_err.response.text
                    if hasattr(http_err, "response")
                    else str(http_err)
                )

                # Check for authentication errors
                if status_code == 401:
                    return f"""# Code Verification Error

## Authentication Error

Your API key is missing or invalid. Please provide a valid API key using the --key option when starting the MCP server.

Error details: {error_detail}
"""
                # Check for rate limiting
                elif status_code == 429:
                    return f"""# Code Verification Error

## Rate Limit Exceeded

You have exceeded the rate limit for API requests. Please try again later.

Error details: {error_detail}
"""
                else:
                    return f"""# Code Verification Error

## Error Details

The API server returned an HTTP error: {status_code}

Error details: {error_detail}

## Recommendations

Please try again or contact support if the issue persists.
"""

        except Exception as e:
            logger.error(f"Error in verify middleware: {str(e)}", exc_info=True)
            # Return a basic Markdown error message with the actual error message
            return f"""# Code Verification Error

## Error Details

An error occurred during the code verification: {str(e) or "Unknown error (no error message provided)"}

## Recommendations

Please try again or contact support if the issue persists.
"""

    def run(self, transport: str = "stdio", port: int = 8080) -> None:
        """
        Run the MCP middleware server.

        Args:
            transport: Transport mechanism (stdio or sse)
            port: Port number for HTTP transport
        """
        # Get fresh configuration
        config = self._get_current_config()
        server_name = self.config.get("server_name")

        # Log current configuration
        logger.info(f"Starting AsteriskMCPMiddleware with name: {server_name}")
        logger.info(f"API base URL: {config['api_base_url']}")
        logger.info(f"API key: {'[SET]' if config['api_key'] else '[NOT SET]'}")
        logger.info(
            f"API timeout: {config['api_timeout'] if config['api_timeout'] is not None else 'No timeout'}"
        )

        if transport == "sse":
            logger.info(
                f"Starting MCP middleware server with SSE transport on port {port}"
            )
            self.mcp.run(transport=transport, port=port)
        else:
            logger.info(f"Starting MCP middleware server with {transport} transport")
            self.mcp.run(transport=transport)


def configure_logging(log_level, no_console=False):
    """Configure logging with or without console output."""
    handlers = []

    # Only add StreamHandler if console output is enabled
    if not no_console:
        handlers.append(logging.StreamHandler(stream=sys.stdout))

    # Always add FileHandler
    handlers.append(
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp.log")
        )
    )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
