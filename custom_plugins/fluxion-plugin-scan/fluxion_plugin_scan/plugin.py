"""Fluxion Port Scanning Plugin."""
import asyncio
import socket
from typing import Any, Dict

import typer
from rich.console import Console
from rich.table import Table

from fluxion.plugins.base import CommandPlugin
from fluxion.hud.panels import QUANTUM_BLUE, QUANTUM_YELLOW, QUANTUM_RED, QUANTUM_DIM

console = Console()

class PortScanPlugin(CommandPlugin):
    """Core plugin for asynchronous network port scanning."""

    name = "scan"
    version = "1.0.0"
    author = "ScorpioCodeX"

    def metadata(self) -> Any:
        from fluxion.models import PluginMeta
        return PluginMeta(name=self.name, version=self.version, author=self.author, description="Port Scanner", protocols=[], enabled=True)

    name = "scan"
    version = "1.0.0"
    author = "ScorpioCodeX"

    def register_commands(self, app: typer.Typer) -> None:
        """Register the scan command into the core Typer app."""

        @app.command(name=self.name, help="Deploy a rapid TCP port scanning matrix.")
        def scan_cmd(
            host: str = typer.Argument(..., help="The target IP or hostname to scan (e.g., 192.168.1.1, google.com)."),
            max_ports: int = typer.Option(1024, "--max", "-m", help="Highest port number to map (1 to max)."),
            timeout: float = typer.Option(0.5, "--timeout", "-t", help="Asynchronous socket connection timeout."),
        ) -> None:
            """Execute the concurrent TCP port scan."""
            asyncio.run(self.execute(target=host, max_ports=max_ports, timeout=timeout))

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        host: str = kwargs.get("target", "")
        max_ports: int = kwargs.get("max_ports", 1024)
        timeout: float = kwargs.get("timeout", 0.5)

        if not host:
            console.print(f"[{QUANTUM_RED}] Error: Grid Target missing.[/{QUANTUM_RED}]")
            return

        try:
            target_ip = socket.gethostbyname(host)
        except socket.gaierror:
            console.print(f"[{QUANTUM_RED}] Error: Unable to resolve node topology for target '{host}'.[/{QUANTUM_RED}]")
            return

        console.print(f"\\n[{QUANTUM_BLUE}]Initializing Asynchronous Port Matrix against {host} ({target_ip})...[/{QUANTUM_BLUE}]\\n")

        table = Table(title=f"Port Topology: {host}", style=QUANTUM_BLUE)
        table.add_column("PORT", style=f"bold {QUANTUM_BLUE}", justify="right")
        table.add_column("PROTOCOL", style=QUANTUM_DIM)
        table.add_column("STATUS", justify="center")

        # Gather Common Ports Mapping for identification
        COMMON_PORTS = {
            21: "FTP", 22: "SSH", 23: "TELNET", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
            445: "SMB", 3306: "MYSQL", 3389: "RDP", 8080: "HTTP-ALT"
        }

        async def _scan_port(port: int) -> tuple[int, bool]:
            conn = asyncio.open_connection(target_ip, port)
            try:
                reader, writer = await asyncio.wait_for(conn, timeout=timeout)
                writer.close()
                await writer.wait_closed()
                return port, True
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return port, False

        # Build execution matrix
        tasks = [_scan_port(port) for port in range(1, max_ports + 1)]
        results = await asyncio.gather(*tasks)

        open_ports = 0
        for port, is_open in results:
            if is_open:
                open_ports += 1
                proto = COMMON_PORTS.get(port, "UNKNOWN")
                table.add_row(
                    str(port), 
                    proto, 
                    f"[{QUANTUM_YELLOW}]OPEN[/{QUANTUM_YELLOW}]"
                )

        if open_ports == 0:
            console.print(f"[{QUANTUM_DIM}]No exposed logical ports detected up to {max_ports}.[/{QUANTUM_DIM}]")
        else:
            console.print(table)
            
        console.print(f"\\n[{QUANTUM_BLUE}]Scan Terminated.[/{QUANTUM_BLUE}]\\n")

def create_plugin() -> PortScanPlugin:
    """Factory function for the plugin manager to spawn the scanner."""
    return PortScanPlugin()
