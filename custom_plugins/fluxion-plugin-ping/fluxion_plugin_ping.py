"""Advanced TCP Ping / Measurement Plugin for Fluxion."""

from typing import Any
import asyncio
import time
import typer

from fluxion.plugins.base import CommandPlugin
from fluxion.models import PluginMeta
from fluxion.hud.panels import QUANTUM_BLUE, QUANTUM_GREEN, QUANTUM_YELLOW, QUANTUM_RED, QUANTUM_DIM, _icon

class PingCommandPlugin(CommandPlugin):
    """Provides a `fluxion ping` command for latency profiling."""

    def metadata(self) -> PluginMeta:
        return PluginMeta(
            name="ping",
            version="0.1.0",
            description="High-resolution TCP ping metrics",
            commands=["ping"],
        )

    def register_commands(self, root_app: typer.Typer) -> None:
        
        # Typer cannot easily overwrite root commands dynamically if they aren't sub-groups.
        # We will create a local Typer instance, add our command, and merge it if necessary,
        # or just decorate the function manually onto the root app's registered_commands list.
        
        @root_app.command(name="ping")
        def run_ping(
            host: str = typer.Argument(..., help="Host to ping (e.g., google.com)"),
            port: int = typer.Option(443, "-p", "--port", help="TCP port to probe"),
            count: int = typer.Option(4, "-c", "--count", help="Number of probes to send"),
            delay: float = typer.Option(1.0, "-i", "--interval", help="Seconds between probes"),
            timeout: float = typer.Option(5.0, "-t", "--timeout", help="TCP timeout in seconds"),
        ) -> None:
            """Perform continuous TCP latency profiling."""
            asyncio.run(self._tcp_ping(host, port, count, delay, timeout))

    async def _tcp_ping(self, host: str, port: int, count: int, delay: float, timeout: float) -> None:
        from rich.console import Console
        
        console = Console()
        icon = _icon()
        console.print(f"\n[{QUANTUM_BLUE}]{icon} TCP PROBE : {host}:{port}[/{QUANTUM_BLUE}]\n")

        sent = 0
        received = 0
        latencies: list[float] = []

        for seq in range(1, count + 1):
            sent += 1
            t0 = time.monotonic()
            try:
                # Use standard asyncio open_connection to simulate a TCP ping
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                
                t1 = time.monotonic()
                ms = (t1 - t0) * 1000.0
                latencies.append(ms)
                received += 1
                
                if ms < 50:
                    color = QUANTUM_GREEN
                elif ms < 150:
                    color = QUANTUM_YELLOW
                else:
                    color = QUANTUM_RED
                
                console.print(f"[{QUANTUM_DIM}]Seq={seq}[/{QUANTUM_DIM}] [{QUANTUM_BLUE}]Connected to {host}:{port}[/{QUANTUM_BLUE}] time=[{color}]{ms:.2f} ms[/{color}]")

            except (asyncio.TimeoutError, OSError) as exc:
                console.print(f"[{QUANTUM_DIM}]Seq={seq}[/{QUANTUM_DIM}] [{QUANTUM_RED}]Timeout or Error: {exc}[/{QUANTUM_RED}]")
            
            if seq < count:
                await asyncio.sleep(delay)

        # Output statistics
        console.print("\n" + "─" * 40)
        console.print(f"[{QUANTUM_BLUE}]TCP PING STATISTICS FOR {host}[/{QUANTUM_BLUE}]")
        loss = ((sent - received) / sent) * 100 if sent > 0 else 0
        console.print(f"    Packets: Sent = {sent}, Received = {received}, Lost = {sent - received} ({loss:.1f}% loss)")
        
        if latencies:
            min_ms = min(latencies)
            max_ms = max(latencies)
            avg_ms = sum(latencies) / len(latencies)
            console.print(f"    Round trip (ms): Min = {min_ms:.2f}, Max = {max_ms:.2f}, Avg = {avg_ms:.2f}")
        console.print()

def create_plugin() -> PingCommandPlugin:
    """Factory called by Fluxion to initialize the ping plugin."""
    return PingCommandPlugin()
