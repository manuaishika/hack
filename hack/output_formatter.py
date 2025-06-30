from rich.console import Console
from rich.table import Table
from rich import box
from typing import List, Dict

def print_dead_code_table(results: List[Dict]):
    console = Console()
    table = Table(title="Dead/Unused Functions", box=box.ROUNDED, show_lines=True)
    table.add_column("Function", style="bold magenta")
    table.add_column("Line", style="cyan", justify="right")
    table.add_column("Reason", style="yellow")
    table.add_column("Lines Saved", style="green", justify="right")
    table.add_column("Energy Impact", style="dim", justify="right")
    for func in results:
        table.add_row(
            f"🪦 {func['name']}",
            str(func['line']),
            func['reason'],
            str(func['lines']),
            func.get('energy_impact') or "-"
        )
    console.print(table) 