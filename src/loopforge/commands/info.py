import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils.logger import setup_logger
from ..utils.validator import validate_file_exists, validate_ffprobe_available
from ..services.ffmpeg_service import get_video_info, FFprobeError
from ..services.duration_service import format_duration


console = Console()


def info_command(
    input_file: str = typer.Argument(..., help="Path ke file video"),
    debug: bool = typer.Option(False, "--debug", help="Mode debug"),
):
    setup_logger(debug=debug)

    try:
        validate_ffprobe_available()
        file_path = validate_file_exists(input_file)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Membaca informasi video...", total=None)
            info = get_video_info(str(file_path))
            progress.update(task, completed=True)

        console.print()
        console.print(Panel.fit(
            "[bold cyan]LoopForge CLI[/bold cyan] - [white]Info Video[/white]",
            border_style="cyan",
        ))
        console.print()

        table = Table(show_header=False, border_style="cyan", padding=(0, 2))
        table.add_column(style="bold cyan", justify="right")
        table.add_column(style="white")

        table.add_row("File Name", info["file_name"])
        table.add_row("Resolution", info["resolution"])
        table.add_row("FPS", f'{info["fps"]:.2f}')
        table.add_row("Codec", info["codec"])
        table.add_row("Duration", format_duration(info["duration"]))
        table.add_row("Bitrate", info["bitrate"])
        table.add_row("File Size", info["file_size"])

        console.print(table)
        console.print()

    except FFprobeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(code=1)
