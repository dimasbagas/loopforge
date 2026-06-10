import signal
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn, Progress, TextColumn, TimeRemainingColumn,
    DownloadColumn, TransferSpeedColumn, SpinnerColumn,
)
from rich.panel import Panel
from rich.table import Table

from ..utils.logger import get_logger, setup_logger
from ..utils.validator import (
    validate_file_exists, validate_video_extension, validate_file_size,
    validate_ffmpeg_available, validate_ffprobe_available,
)
from ..services.duration_service import (
    parse_duration, calculate_loops, format_duration, DurationParseError,
)
from ..services.ffmpeg_service import (
    get_video_info, render_loop, analyze_seamless,
    estimate_output_size, estimate_render_time, FFmpegError,
)
from ..services.gpu_service import (
    get_gpu_info, get_encoder_flags, is_gpu_available, get_gpu_name,
)
from ..services.metadata_service import generate_metadata
from ..models import LoopResult
from ..config import OUTPUT_DIR, SUPPORTED_VIDEO_EXTENSIONS


console = Console()
cancel_requested = False


def _signal_handler(sig, frame):
    global cancel_requested
    cancel_requested = True
    console.print("\n[yellow]Membatalkan render... Silakan tunggu[/yellow]")


def local_command(
    input_file: str = typer.Argument(..., help="Path ke file video lokal"),
    duration: str = typer.Option("1h", "--duration", "-d",
        help="Durasi target (1h, 2h, 8h, 12h, 24h, 90m, 01:30:00)"),
    output: Optional[str] = typer.Option(None, "--output", "-o",
        help="Nama file output (optional)"),
    fast: bool = typer.Option(False, "--fast", "-f",
        help="Fast mode tanpa re-encode (copy stream)"),
    seamless: bool = typer.Option(False, "--seamless", "-s",
        help="Analisis seamless loop"),
    debug: bool = typer.Option(False, "--debug", help="Mode debug"),
):
    setup_logger(debug=debug)
    logger = get_logger()

    global cancel_requested
    cancel_requested = False
    signal.signal(signal.SIGINT, _signal_handler)

    try:
        validate_ffmpeg_available()
        validate_ffprobe_available()

        file_path = validate_file_exists(input_file)
        validate_video_extension(file_path)
        validate_file_size(file_path)

        target_seconds = parse_duration(duration)

        console.print()
        console.print(Panel.fit(
            "[bold cyan]LoopForge CLI[/bold cyan] - [white]Loop Video Lokal[/white]",
            border_style="cyan",
        ))
        console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Membaca informasi video...", total=None)
            video_info = get_video_info(str(file_path))
            progress.update(task, completed=True)

        source_duration = video_info["duration"]
        target_seconds = parse_duration(duration)
        total_loops = calculate_loops(source_duration, target_seconds)

        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style="bold cyan", justify="right")
        info_table.add_column(style="white")
        info_table.add_row("Input:", video_info["file_name"])
        info_table.add_row("Resolusi:", video_info["resolution"])
        info_table.add_row("FPS:", f'{video_info["fps"]:.2f}')
        info_table.add_row("Codec:", video_info["codec"])
        info_table.add_row("Durasi Source:", format_duration(source_duration))
        info_table.add_row("Durasi Target:", format_duration(target_seconds))
        info_table.add_row("Total Loops:", str(total_loops))

        gpu_info = get_gpu_info()
        if gpu_info["available"]:
            info_table.add_row("GPU:", f'[green]{gpu_info["name"]}[/green]')
            info_table.add_row("Encoder:", f'[green]{gpu_info["encoder"]}[/green]')
        else:
            info_table.add_row("GPU:", "[yellow]Not Found[/yellow]")
            info_table.add_row("Encoder:", f'[yellow]{gpu_info["encoder"]}[/yellow]')

        est_size = estimate_output_size(video_info, target_seconds)
        if est_size > 0:
            if est_size > 1024:
                size_str = f"{est_size / 1024:.1f} GB"
            else:
                size_str = f"{est_size:.0f} MB"
            info_table.add_row("Estimasi Ukuran:", size_str)

        est_time = estimate_render_time(source_duration, target_seconds, gpu_info["available"])
        info_table.add_row("Estimasi Waktu:", est_time)

        console.print(info_table)
        console.print()

        seamless_score = None
        if seamless:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Menganalisis seamless loop...", total=None)
                seamless_score = analyze_seamless(str(file_path))
                progress.update(task, completed=True)

            score_color = "green" if seamless_score >= 85 else "yellow" if seamless_score >= 60 else "red"
            console.print(f"Seamless Loop Score: [{score_color}]{seamless_score}%[/{score_color}]")
            if seamless_score < 60:
                console.print("[yellow]Warning: Visible Loop Transition Detected[/yellow]")
            console.print()

        # Deteksi apakah output adalah path lengkap, direktori, atau nama file
        if output:
            out = Path(output)
            if out.suffix == ".mp4":
                # Path lengkap atau nama file .mp4
                output_dir = out.parent if out.parent != Path(".") else OUTPUT_DIR
                output_filename = out.name
            elif out.is_dir() or (not out.suffix and not out.exists()):
                # Direktori (ada atau belum ada)
                output_dir = out
                stem = file_path.stem
                duration_tag = duration.replace(":", "-")
                output_filename = f"{stem}_{duration_tag}.mp4"
            else:
                output_dir = OUTPUT_DIR
                output_filename = f"{output}.mp4"
        else:
            output_dir = OUTPUT_DIR
            stem = file_path.stem
            duration_tag = duration.replace(":", "-")
            output_filename = f"{stem}_{duration_tag}.mp4"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = str(output_dir / output_filename)

        if Path(output_path).exists():
            console.print(f"[yellow]File output sudah ada: {output_filename}[/yellow]")
            overwrite = typer.confirm("Timpa file?", default=True)
            if not overwrite:
                base = output_dir / Path(output_filename).stem
                counter = 1
                while Path(output_path).exists():
                    output_filename = f"{Path(output_filename).stem}_{counter}.mp4"
                    output_path = str(output_dir / output_filename)
                    counter += 1

        console.print("[bold cyan]Render Progress:[/bold cyan]")

        if fast:
            from ..services.ffmpeg_service import copy_stream_loop
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Fast Copy: ", total=target_seconds)
                try:
                    copy_stream_loop(str(file_path), output_path, target_seconds)
                    progress.update(task, completed=target_seconds)
                except FFmpegError as e:
                    progress.update(task, completed=0)
                    console.print(f"\n[red]Error: {str(e)}[/red]")
                    console.print("[yellow]Mencoba render mode sebagai fallback...[/yellow]")
                    fast = False

        if not fast:
            encoder_flags = get_encoder_flags()

            render_progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            )

            with render_progress:
                render_task = render_progress.add_task(
                    "[cyan]Render: ", total=target_seconds
                )

                def on_progress(progress_val, current_time):
                    if cancel_requested:
                        return
                    render_progress.update(
                        render_task,
                        completed=min(current_time, target_seconds),
                    )

                try:
                    render_loop(
                        str(file_path), output_path, target_seconds,
                        encoder_flags, on_progress=on_progress,
                        cancel_check=lambda: cancel_requested,
                    )
                    render_progress.update(render_task, completed=target_seconds)
                except FFmpegError as e:
                    render_progress.update(render_task, completed=0)
                    console.print(f"\n[red]Error: {str(e)}[/red]")
                    raise typer.Exit(code=1)

        if cancel_requested:
            console.print("\n[yellow]Render dibatalkan.[/yellow]")
            if Path(output_path).exists():
                Path(output_path).unlink(missing_ok=True)
            raise typer.Exit(code=1)

        result = LoopResult(
            source_file=str(file_path),
            source_duration=source_duration,
            target_duration=target_seconds,
            total_loops=total_loops,
            encoder=get_gpu_info()["encoder"],
            output_file=output_path,
            seamless_score=seamless_score,
            gpu_name=get_gpu_name(),
            estimated_size_mb=est_size if est_size > 0 else None,
            estimated_render_time=est_time,
        )

        metadata_file = generate_metadata(result, output_dir)
        logger.info(f"Metadata saved: {metadata_file}")

        output_size = Path(output_path).stat().st_size
        output_size_mb = output_size / (1024 * 1024)
        if output_size_mb > 1024:
            output_size_str = f"{output_size_mb / 1024:.2f} GB"
        else:
            output_size_str = f"{output_size_mb:.2f} MB"

        console.print()
        console.print(Panel(
            f"[bold green]✓ Selesai![/bold green]\n\n"
            f"  [bold]Output:[/bold] {output_filename}\n"
            f"  [bold]Lokasi:[/bold] {output_dir}\n"
            f"  [bold]Ukuran:[/bold] {output_size_str}",
            border_style="green",
        ))

    except DurationParseError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1)
    except FFmpegError as e:
        console.print(f"[red]FFmpeg Error: {str(e)}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"[red]Error: {str(e)}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(code=1)
