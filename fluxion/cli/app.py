"""Main CLI application — all Fluxion commands."""

from __future__ import annotations

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from fluxion import __version__
from fluxion.core.engine import FluxionEngine
from fluxion.exceptions import FluxionError
from fluxion.hud.renderer import HUDRenderer
from fluxion.models import (
    FetchRequest,
    FluxionConfig,
    OutputMode,
    TransferStats,
)

app = typer.Typer(
    name="fluxion",
    help="Fluxion -- The Intelligent Network Command Engine",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


def _make_console() -> Console:
    """Create a Rich Console with safe encoding for the current terminal."""
    if sys.platform == "win32":
        import os

        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        vt_enabled = False
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetConsoleOutputCP(65001)
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                new_mode = mode.value | 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                vt_enabled = bool(kernel32.SetConsoleMode(handle, new_mode))
        except (AttributeError, OSError):
            pass

        from fluxion.hud.layout import supports_unicode

        modern = supports_unicode() or vt_enabled
        if modern:
            # Reconfigure stdout/stderr to UTF-8 for VT100 rendering
            try:
                if hasattr(sys.stdout, "reconfigure"):
                    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                if hasattr(sys.stderr, "reconfigure"):
                    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, AttributeError):
                pass
            return Console(highlight=False, force_terminal=True, legacy_windows=False)
        return Console(highlight=False)
    return Console(highlight=False)


console = _make_console()


# ── Shared helpers ────────────────────────────────────────────────────────


def _output_mode(
    minimal: bool = False,
    plain: bool = False,
    json_out: bool = False,
    quiet: bool = False,
) -> OutputMode:
    if json_out:
        return OutputMode.JSON
    if quiet:
        return OutputMode.QUIET
    if minimal:
        return OutputMode.MINIMAL
    if plain:
        return OutputMode.PLAIN
    return OutputMode.DEFAULT


def _run_async(coro: object) -> object:
    """Run an async coroutine from sync context."""
    return asyncio.run(coro)  # type: ignore[arg-type]


def _handle_error(
    hud: HUDRenderer,
    exc: Exception,
    trace: bool = False,
) -> None:
    """Unified error handler for CLI commands."""
    hud.stop_live()
    message = exc.message if isinstance(exc, FluxionError) else str(exc)
    suggestion = exc.suggestion if isinstance(exc, FluxionError) else None
    hud.print_error(
        message,
        suggestion=suggestion,
        show_trace=trace,
        traceback_str=traceback.format_exc() if trace else None,
    )
    raise typer.Exit(1)


def _load_config() -> FluxionConfig:
    """Load user config with graceful fallback."""
    from fluxion.installer.config import load_config

    return load_config()


def _parse_header_option(raw: str) -> tuple[str, str]:
    """Parse a ``"Name: Value"`` header string. Raises typer.BadParameter on invalid."""
    if ":" not in raw:
        raise typer.BadParameter(
            f"Invalid header format: {raw!r} — expected 'Name: Value'"
        )
    name, _, value = raw.partition(":")
    return name.strip(), value.strip()


# ── Commands ──────────────────────────────────────────────────────────────


@app.command()
def fetch(
    url: str = typer.Argument(..., help="URL to download"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output file path"),
    connections: int = typer.Option(8, "-c", "--connections", help="Max parallel connections"),
    no_resume: bool = typer.Option(False, "--no-resume", help="Disable resume"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip TLS verification"),
    timeout: float = typer.Option(30.0, "--timeout", help="Request timeout in seconds"),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="Proxy URL"),
    sha256: Optional[str] = typer.Option(None, "--sha256", help="Expected SHA-256 checksum"),
    header: Optional[list[str]] = typer.Option(None, "-H", "--header", help="Custom header (Name: Value)"),
    cookie: Optional[list[str]] = typer.Option(None, "--cookie", help="Cookie (name=value)"),
    cookie_file: Optional[str] = typer.Option(None, "--cookie-file", help="Netscape/JSON cookie file path"),
    browser_cookies: Optional[str] = typer.Option(None, "--browser-cookies", help="Import cookies from browser (chrome/firefox/edge/safari)"),
    browser_profile: Optional[str] = typer.Option(None, "--browser-profile", help="Browser impersonation profile (chrome/firefox/edge/safari)"),
    referer: Optional[str] = typer.Option(None, "--referer", help="Referer URL"),
    minimal: bool = typer.Option(False, "--minimal", help="Single-line progress"),
    plain: bool = typer.Option(False, "--plain", help="No styling"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    quiet: bool = typer.Option(False, "--quiet", help="Quiet mode"),
    trace: bool = typer.Option(False, "--trace", help="Show tracebacks on error"),
) -> None:
    """Download a file with intelligent parallel transport."""
    mode = _output_mode(minimal, plain, json_out, quiet)
    hud = HUDRenderer(console=console, output_mode=mode)
    hud.print_header()

    cfg = _load_config()

    # Parse custom headers
    custom_headers: dict[str, str] = {}
    if header:
        for h in header:
            try:
                name, value = _parse_header_option(h)
                custom_headers[name] = value
            except typer.BadParameter as exc:
                hud.print_error(str(exc))
                raise typer.Exit(1)

    # Build cookie jar
    cookies: dict[str, str] = {}
    if cookie:
        from fluxion.stealth.cookies import CookieJar

        jar = CookieJar()
        for c in cookie:
            jar.add_raw(c)
        cookies = jar.as_dict()

    if cookie_file:
        from fluxion.stealth.cookies import CookieJar

        jar = CookieJar()
        cookie_path = Path(cookie_file)
        if not cookie_path.exists():
            hud.print_error(
                f"Cookie file not found: {cookie_file}",
                suggestion="Check the path and try again.",
            )
            raise typer.Exit(1)
        try:
            jar.load_file(cookie_path)
            cookies.update(jar.as_dict())
        except FluxionError as exc:
            _handle_error(hud, exc, trace)

    if browser_cookies:
        from fluxion.stealth.cookies import CookieJar

        jar = CookieJar()
        try:
            jar.load_browser(browser_cookies)
            cookies.update(jar.as_dict())
        except FluxionError as exc:
            _handle_error(hud, exc, trace)

    engine = FluxionEngine(
        max_connections=connections,
        timeout=timeout,
        verify_tls=not no_verify,
        proxy=proxy or cfg.proxy,
        user_agent=cfg.user_agent,
    )

    request = FetchRequest(
        url=url,
        output=Path(output) if output else None,
        headers=custom_headers,
        max_connections=connections,
        resume=not no_resume,
        verify_tls=not no_verify,
        timeout=timeout,
        proxy=proxy or cfg.proxy,
        browser_profile=browser_profile or cfg.default_browser_profile,
        cookies=cookies,
        referer=referer,
    )

    def on_progress(stats: TransferStats) -> None:
        hud.update_transfer(stats, url)

    try:
        hud.start_live()
        result = _run_async(engine.fetch(request, on_progress=on_progress))
        hud.stop_live()

        if sha256 and hasattr(result, "sha256"):
            if result.sha256.lower() != sha256.lower():  # type: ignore[union-attr]
                hud.print_error(
                    f"SHA-256 mismatch: expected {sha256}, got {result.sha256}",  # type: ignore[union-attr]
                    suggestion="File may be corrupted. Re-download.",
                )
                raise typer.Exit(1)

        hud.print_result(result)

    except FluxionError as exc:
        _handle_error(hud, exc, trace)
    except typer.Exit:
        raise
    except Exception as exc:
        _handle_error(hud, exc, trace)


@app.command()
def stream(
    url: str = typer.Argument(..., help="URL to stream"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip TLS verification"),
    header: Optional[list[str]] = typer.Option(None, "-H", "--header", help="Custom header (Name: Value)"),
    cookie: Optional[list[str]] = typer.Option(None, "--cookie", help="Cookie (name=value)"),
    browser_profile: Optional[str] = typer.Option(None, "--browser-profile", help="Browser impersonation profile"),
    referer: Optional[str] = typer.Option(None, "--referer", help="Referer URL"),
    trace: bool = typer.Option(False, "--trace", help="Show tracebacks on error"),
) -> None:
    """Stream a URL's content to stdout."""
    # Build stealth headers for stream
    from fluxion.stealth.context import StealthContext
    from fluxion.stealth.cookies import CookieJar
    from fluxion.stealth.profiles import get_profile

    custom_headers: dict[str, str] = {}
    if header:
        for h in header:
            try:
                name, value = _parse_header_option(h)
                custom_headers[name] = value
            except typer.BadParameter as exc:
                hud = HUDRenderer(console=console)
                hud.print_error(str(exc))
                raise typer.Exit(1)

    jar = CookieJar()
    if cookie:
        for c in cookie:
            jar.add_raw(c)

    profile = None
    if browser_profile:
        profile = get_profile(browser_profile)

    ctx = StealthContext(
        profile=profile,
        cookie_jar=jar,
        custom_headers=custom_headers,
        referer=referer,
    )
    stream_headers = ctx.build_headers() or None

    engine = FluxionEngine(verify_tls=not no_verify)

    async def _stream() -> None:
        async for chunk in engine.stream(url, headers=stream_headers):
            sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()

    try:
        _run_async(_stream())
    except FluxionError as exc:
        hud = HUDRenderer(console=console)
        hud.print_error(exc.message, suggestion=exc.suggestion)
        raise typer.Exit(1)


@app.command()
def probe(
    url: str = typer.Argument(..., help="URL to probe"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip TLS verification"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    quiet: bool = typer.Option(False, "--quiet", help="Quiet mode"),
    trace: bool = typer.Option(False, "--trace", help="Show tracebacks on error"),
) -> None:
    """Probe a URL for network intelligence."""
    mode = _output_mode(json_out=json_out, quiet=quiet)
    hud = HUDRenderer(console=console, output_mode=mode)
    hud.print_header()

    engine = FluxionEngine(verify_tls=not no_verify)

    try:
        result = _run_async(engine.probe(url))
        hud.print_probe(result)
    except FluxionError as exc:
        _handle_error(hud, exc, trace)


@app.command()
def bench(
    url: str = typer.Argument(..., help="URL to benchmark"),
    iterations: int = typer.Option(10, "-n", "--iterations", help="Number of requests"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip TLS verification"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    quiet: bool = typer.Option(False, "--quiet", help="Quiet mode"),
    trace: bool = typer.Option(False, "--trace", help="Show tracebacks on error"),
) -> None:
    """Benchmark network performance to a URL."""
    mode = _output_mode(json_out=json_out, quiet=quiet)
    hud = HUDRenderer(console=console, output_mode=mode)
    hud.print_header()

    engine = FluxionEngine(verify_tls=not no_verify)

    try:
        result = _run_async(engine.bench(url, iterations=iterations))
        hud.print_bench(result)
    except FluxionError as exc:
        _handle_error(hud, exc, trace)


@app.command()
def mirror(
    urls: list[str] = typer.Argument(..., help="Mirror URLs (space-separated)"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output file path"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    quiet: bool = typer.Option(False, "--quiet", help="Quiet mode"),
    trace: bool = typer.Option(False, "--trace", help="Show tracebacks on error"),
) -> None:
    """Download from the fastest available mirror."""
    mode = _output_mode(json_out=json_out, quiet=quiet)
    hud = HUDRenderer(console=console, output_mode=mode)
    hud.print_header()

    engine = FluxionEngine()

    def on_progress(stats: TransferStats) -> None:
        hud.update_transfer(stats)

    try:
        hud.start_live()
        result = _run_async(
            engine.mirror(urls, output=Path(output) if output else None, on_progress=on_progress)
        )
        hud.stop_live()
        hud.print_result(result)
    except FluxionError as exc:
        _handle_error(hud, exc, trace)


@app.command()
def secure(
    url: str = typer.Argument(..., help="URL to inspect"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    trace: bool = typer.Option(False, "--trace", help="Show tracebacks on error"),
) -> None:
    """Inspect TLS security for a URL."""
    from fluxion.security.tls import TLSInspector

    mode = _output_mode(json_out=json_out)
    hud = HUDRenderer(console=console, output_mode=mode)
    hud.print_header()

    inspector = TLSInspector()
    try:
        cert = inspector.inspect(url)
        from fluxion.hud.panels import render_tls_panel

        cert_data: dict[str, str] = {
            "SUBJECT CN": cert.subject.get("commonName", "\u2014"),
            "ISSUER": cert.issuer.get("organizationName", "\u2014"),
            "TLS VERSION": cert.tls_version,
            "CIPHER": cert.cipher,
            "SERIAL": cert.serial_number,
            "VALID FROM": cert.not_before,
            "VALID UNTIL": cert.not_after,
            "SHA-256": cert.fingerprint_sha256,
        }
        if cert.san:
            cert_data["SAN"] = ", ".join(cert.san[:5])

        expiry_warn = inspector.check_expiry(cert)
        if expiry_warn:
            cert_data["WARNING"] = expiry_warn

        if json_out:
            import dataclasses
            console.print_json(json.dumps(dataclasses.asdict(cert), default=str))
        else:
            panel = render_tls_panel(cert_data)
            console.print(panel)

    except FluxionError as exc:
        _handle_error(hud, exc, trace)


@app.command()
def init(
    trace: bool = typer.Option(False, "--trace", help="Show tracebacks on error"),
) -> None:
    """Initialize Fluxion - detect system and install dependencies."""
    from fluxion.installer.setup import run_init

    hud = HUDRenderer(console=console)
    hud.print_header()

    try:
        _run_async(run_init(console))
    except FluxionError as exc:
        _handle_error(hud, exc, trace)


@app.command()
def doctor(
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Diagnose Fluxion installation and environment."""
    from fluxion.installer.doctor import run_doctor

    mode = _output_mode(json_out=json_out)
    hud = HUDRenderer(console=console, output_mode=mode)
    hud.print_header()
    run_doctor(console, json_output=json_out)


@app.command()
def config(
    show: bool = typer.Option(True, "--show/--no-show", help="Show current config"),
    key: Optional[str] = typer.Option(None, "--set", help="Config key to set (key=value)"),
) -> None:
    """View or modify Fluxion configuration."""
    from fluxion.installer.config import load_config, save_config, show_config

    hud = HUDRenderer(console=console)

    if key:
        if "=" not in key:
            hud.print_error(
                f"Invalid format: {key}",
                suggestion="Use --set key=value (e.g. --set max_connections=16)",
            )
            raise typer.Exit(1)
        k, _, v = key.partition("=")
        cfg = load_config()
        data = cfg.model_dump()
        if k not in data:
            hud.print_error(
                f"Unknown config key: {k}",
                suggestion=f"Valid keys: {', '.join(data.keys())}",
            )
            raise typer.Exit(1)
        # Coerce type
        existing = data[k]
        if isinstance(existing, bool):
            data[k] = v.lower() in ("true", "1", "yes")
        elif isinstance(existing, int):
            data[k] = int(v)
        elif isinstance(existing, float):
            data[k] = float(v)
        else:
            data[k] = v
        new_cfg = FluxionConfig.model_validate(data)
        save_config(new_cfg)
        console.print(f"  [bright_green]+[/bright_green] {k} = {v}")
        return

    hud.print_header()
    show_config(console)


@app.command()
def plugin(
    action: str = typer.Argument(..., help="Action: install, remove, list"),
    name: Optional[str] = typer.Argument(None, help="Plugin name"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Manage Fluxion plugins."""
    from fluxion.plugins.manager import PluginManager

    mode = _output_mode(json_out=json_out)
    hud = HUDRenderer(console=console, output_mode=mode)
    hud.print_header()

    manager = PluginManager()

    if action == "list":
        plugins = manager.list_plugins()
        if json_out:
            console.print_json(json.dumps([p.model_dump() for p in plugins], default=str))
        else:
            from rich.table import Table

            table = Table(title="Installed Plugins", border_style="bright_cyan")
            table.add_column("Name", style="bold")
            table.add_column("Version")
            table.add_column("Protocols")
            table.add_column("Status")
            for p in plugins:
                table.add_row(
                    p.name,
                    p.version,
                    ", ".join(p.protocols) or "\u2014",
                    "enabled" if p.enabled else "disabled",
                )
            console.print(table)

    elif action == "install":
        if not name:
            hud.print_error("Plugin name required.", suggestion="Usage: fluxion plugin install <name>")
            raise typer.Exit(1)
        manager.install(name)
        console.print(f"  [bright_green]+[/bright_green] Plugin '{name}' installed.")

    elif action == "remove":
        if not name:
            hud.print_error("Plugin name required.", suggestion="Usage: fluxion plugin remove <name>")
            raise typer.Exit(1)
        manager.remove(name)
        console.print(f"  [bright_yellow]-[/bright_yellow] Plugin '{name}' removed.")

    else:
        hud.print_error(
            f"Unknown action: {action}",
            suggestion="Use: install, remove, or list",
        )
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show Fluxion version and system info."""
    from fluxion import __codename__
    from fluxion.hud.panels import QUANTUM_BLUE, QUANTUM_DIM, _icon

    icon = _icon()
    console.print(f"[{QUANTUM_BLUE}]{icon} Fluxion v{__version__}[/{QUANTUM_BLUE}] [{QUANTUM_DIM}][{__codename__}][/{QUANTUM_DIM}]")


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
