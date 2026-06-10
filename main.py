import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from loopforge.cli import app

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        from rich.console import Console
        console = Console()
        console.print("\n[yellow]Dibatalkan oleh pengguna[/yellow]")
        sys.exit(1)
