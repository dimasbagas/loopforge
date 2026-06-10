import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__

console = Console()


def _version_callback(value: bool):
    if value:
        console.print(f"LoopForge CLI v{__version__}")
        raise typer.Exit()


def _display_banner():
    banner = Panel.fit(
        "[bold cyan]LoopForge CLI[/bold cyan] [white]v1.0.0[/white]\n"
        "[dim]Ubah video pendek jadi video durasi panjang dengan looping otomatis[/dim]\n\n"
        "[bold]Perintah:[/bold]\n"
        "  [cyan]local[/cyan]    Loop video lokal\n"
        "  [cyan]youtube[/cyan]  Download YouTube lalu loop\n"
        "  [cyan]info[/cyan]     Info detail video\n"
        "  [cyan]batch[/cyan]    Batch process semua video di folder\n\n"
        "[bold]Contoh:[/bold]\n"
        "  loopforge local video.mp4 --duration 8h\n"
        "  loopforge youtube https://youtube.com/watch?v=xxx --duration 12h\n"
        "  loopforge info video.mp4\n"
        "  loopforge batch ./videos --duration 2h\n\n"
        "[dim]Gunakan [bold]loopforge --help[/bold] untuk bantuan lengkap[/dim]",
        border_style="cyan",
    )
    console.print(banner)


app = typer.Typer(
    name="loopforge",
    help="LoopForge CLI - Ubah video pendek menjadi video berdurasi panjang dengan looping otomatis",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v",
        help="Tampilkan versi",
        callback=_version_callback,
        is_eager=True,
    ),
):
    if ctx.invoked_subcommand is None:
        from .commands.interactive import interactive_wizard
        interactive_wizard()


from .commands.local import local_command
from .commands.youtube import youtube_command
from .commands.info import info_command
from .commands.batch import batch_command

app.command(name="local")(local_command)
app.command(name="youtube")(youtube_command)
app.command(name="info")(info_command)
app.command(name="batch")(batch_command)


def main_entry():
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Dibatalkan oleh pengguna[/yellow]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main_entry()
