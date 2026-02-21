"""DNS Reconnaissance Plugin for Fluxion."""

from typing import Any
import asyncio
import typer

from fluxion.plugins.base import CommandPlugin
from fluxion.models import PluginMeta
from fluxion.hud.panels import QUANTUM_BLUE, _icon

class DNSCommandPlugin(CommandPlugin):
    """Adds `fluxion dns` for advanced record reconnaissance."""

    def metadata(self) -> PluginMeta:
        return PluginMeta(
            name="dns",
            version="0.1.0",
            description="Asynchronous DNS record reconnaissance",
            commands=["dns"],
        )

    def register_commands(self, root_app: typer.Typer) -> None:
        
        @root_app.command(name="dns")
        def run_dns_recon(
            domain: str = typer.Argument(..., help="Domain to analyze"),
        ) -> None:
            """Perform async DNS reconnaissance (A, AAAA, MX, TXT)."""
            asyncio.run(self._recon(domain))

    async def _recon(self, domain: str) -> None:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        import aiodns
        import socket
        
        console = Console()
        icon = _icon()
        console.print(f"\n[{QUANTUM_BLUE}]{icon} DNS INTELLIGENCE : {domain}[/{QUANTUM_BLUE}]\n")

        # Initialize resolver with specific nameservers
        resolver = aiodns.DNSResolver(nameservers=['1.1.1.1', '8.8.8.8'])
        record_types = ["A", "AAAA", "MX", "TXT", "CNAME"]
        results: list[tuple[str, str]] = []

        async def fetch_record(rectype: str) -> None:
            try:
                # Fallback to standard query to guarantee iterable results
                answers = await resolver.query(domain, rectype)
                for ans in answers:
                    if rectype in ("A", "AAAA"):
                        val = ans.host
                    elif rectype == "MX":
                        val = f"{ans.priority} {ans.host}"
                    elif rectype == "TXT":
                        val = getattr(ans, "text", str(ans))
                    elif rectype == "CNAME":
                        val = ans.cname
                    else:
                        val = str(ans)
                    results.append((rectype, val))
            except aiodns.error.DNSError:
                results.append((rectype, "No record found"))
            except Exception as e:
                results.append((rectype, f"Error: {e}"))

        await asyncio.gather(*(fetch_record(t) for t in record_types))

        # Render matrix UI
        table = Table(
            show_header=True, 
            header_style=f"bold {QUANTUM_BLUE}", 
            border_style=QUANTUM_BLUE, 
            box=box.HEAVY_EDGE
        )
        table.add_column("RECORD TYPE", style="bold cyan", width=12)
        table.add_column("COMPUTED VALUE")
        
        # Sort by record type
        results.sort(key=lambda x: x[0])
        for rt, val in results:
            table.add_row(rt, val)

        console.print(table)
        console.print()


def create_plugin() -> DNSCommandPlugin:
    """Factory called by Fluxion to initialize the DNS plugin."""
    return DNSCommandPlugin()
