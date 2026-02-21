from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

with open("rich_out.txt", "w", encoding="utf-8") as f:
    console = Console(file=f, force_terminal=False)

    QUANTUM_DIM = "#888888"
    QUANTUM_WHITE = "#ffffff"
    QUANTUM_GREEN = "#00ff88"
    QUANTUM_BLUE = "#00d2ff"

    table = Table.grid(padding=(0, 2))
    table.add_column(style=QUANTUM_DIM, min_width=14)
    table.add_column()

    table.add_row("FILE", Text("test_ipfs.txt", style=QUANTUM_WHITE))
    table.add_row("URL", Text("ipfs://test", style="white"))
    table.add_row("SIZE", Text("123 KB", style=QUANTUM_GREEN))
    table.add_row("SPEED", Text("800 KB/s", style=QUANTUM_GREEN))
    table.add_row("TIME", Text("1.5s", style="white"))
    table.add_row("PROTOCOL", Text("HTTP1", style=QUANTUM_BLUE))

    panel = Panel(table, title="TEST GRID TO FILE")
    console.print(panel)
