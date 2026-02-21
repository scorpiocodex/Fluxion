"""Fluxion Certificate Inspector Plugin."""
import ssl
import socket
from datetime import datetime
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fluxion.plugins.base import CommandPlugin
from fluxion.hud.panels import QUANTUM_BLUE, QUANTUM_RED, QUANTUM_YELLOW, QUANTUM_DIM

console = Console()

class CertInspectorPlugin(CommandPlugin):
    """Core plugin for extracting and verifying remote SSL/TLS certs."""

    name = "cert"
    version = "1.0.0"
    author = "ScorpioCodeX"

    def metadata(self) -> Any:
        from fluxion.models import PluginMeta
        return PluginMeta(name=self.name, version=self.version, author=self.author, description="SSL/TLS Inspector", protocols=[], enabled=True)

    name = "cert"
    version = "1.0.0"
    author = "ScorpioCodeX"

    def register_commands(self, app: typer.Typer) -> None:
        """Register the cert command into the core Typer app."""

        @app.command(name=self.name, help="Deploy an SSL/TLS certificate diagnostic extraction hook.")
        def cert_cmd(
            host: str = typer.Argument(..., help="The target domain to inspect (e.g., example.com)."),
            port: int = typer.Option(443, "--port", "-p", help="The HTTPS port to extract from."),
            timeout: float = typer.Option(5.0, "--timeout", "-t", help="Socket connection timeout."),
        ) -> None:
            """Execute the certificate evaluation."""
            self.execute(target=host, port=port, timeout=timeout)

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        host: str = kwargs.get("target", "")
        port: int = kwargs.get("port", 443)
        timeout: float = kwargs.get("timeout", 5.0)

        if not host:
            console.print(f"[{QUANTUM_RED}] Error: Grid Target missing.[/{QUANTUM_RED}]")
            return

        console.print(f"\\n[{QUANTUM_BLUE}]Initiating SSL Handshake with {host}:{port}...[/{QUANTUM_BLUE}]\\n")

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Extract regardless of trust limits

        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    from cryptography import x509
                    from cryptography.hazmat.backends import default_backend
                    import os
                    
                    try:
                        parsed_cert = x509.load_der_x509_certificate(cert, default_backend())
                    except Exception as e:
                        console.print(f"[{QUANTUM_RED}] Parse Exception: {e}[/{QUANTUM_RED}]")
                        return

                    issuer = parsed_cert.issuer.rfc4514_string()
                    subject = parsed_cert.subject.rfc4514_string()
                    serial = parsed_cert.serial_number
                    not_before = parsed_cert.not_valid_before_utc
                    not_after = parsed_cert.not_valid_after_utc
                    
                    table = Table(show_header=False, show_edge=False, box=None)
                    table.add_column("Key", style=f"bold {QUANTUM_BLUE}")
                    table.add_column("Value", style="white")

                    table.add_row("Subject", subject)
                    table.add_row("Issuer", issuer)
                    table.add_row("Serial", str(serial))
                    table.add_row("Valid From", str(not_before))
                    table.add_row("Valid Until", f"[{QUANTUM_YELLOW}]{not_after}[/{QUANTUM_YELLOW}]")
                    table.add_row("Signature Algo", parsed_cert.signature_algorithm_oid._name)

                    panel = Panel(
                        table,
                        title=f"SSL/TLS Certificate Tracker: {host}",
                        border_style=QUANTUM_BLUE,
                        expand=False
                    )
                    console.print(panel)
                    console.print(f"\\n[{QUANTUM_BLUE}]Inspection Terminated.[/{QUANTUM_BLUE}]\\n")

        except (socket.gaierror, socket.timeout, ConnectionRefusedError) as e:
            console.print(f"[{QUANTUM_RED}] Connectivity Error linking to '{host}': {e}[/{QUANTUM_RED}]")
        except ssl.SSLError as e:
            console.print(f"[{QUANTUM_RED}] Handshake Protocol Violation: {e}[/{QUANTUM_RED}]")
        except ImportError:
             console.print(f"[{QUANTUM_RED}] Missing dependency: pip install cryptography[/{QUANTUM_RED}]")

def create_plugin() -> CertInspectorPlugin:
    """Factory function for the plugin manager to spawn the cert inspector."""
    return CertInspectorPlugin()
