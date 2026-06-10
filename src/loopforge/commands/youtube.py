import signal
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn, Progress, TextColumn, TimeRemainingColumn,
    DownloadColumn, TransferSpeedColumn, SpinnerColumn, TaskID,
)
from rich.panel import Panel
from rich.table import Table

from ..utils.logger import get_logger, setup_logger
from ..utils.validator import (
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
from ..services.youtube_service import (
    download_video, get_video_duration, validate_youtube_url,
    YouTubeError,
)
from ..services.metadata_service import generate_metadata
from ..models import LoopResult
from ..config import OUTPUT_DIR, DOWNLOAD_DIR


console = Console()
cancel_requested = False


def _signal_handler(sig, frame):
    global cancel_requested
    cancel_requested = True
    console.print("\n[yellow]Membatalkan... Silakan tunggu[/yellow]")


def youtube_command(
    url: str = typer.Argument(..., help="URL video YouTube"),
    duration: str = typer.Option("1h", "--duration", "-d",
        help="Durasi target (1h, 2h, 8h, 12h, 24h, 90m, 01:30:00)"),
    output: Optional[str] = typer.Option(None, "--output", "-o",
        help="Nama file output (optional)"),
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

        if not validate_youtube_url(url):
            console.print("[red]Error: URL YouTube tidak valid[/red]")
            raise typer.Exit(code=1)

        target_seconds = parse_duration(duration)

        console.print()
        console.print(Panel.fit(
            "[bold cyan]LoopForge CLI[/bold cyan] - [white]Download & Loop YouTube[/white]",
            border_style="cyan",
        ))
        console.print()

        video_title = ""
        download_progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

        with download_progress:
            dl_task = download_progress.add_task(
                "[cyan]Mendownload video...", total=100.0
            )

            def on_dl_progress(progress_val, downloaded, total, speed):
                if cancel_requested:
                    return
                download_progress.update(
                    dl_task,
                    completed=progress_val * 100,
                )

            try:
                downloaded_file = download_video(
                    url, on_progress=on_dl_progress
                )
                download_progress.update(dl_task, completed=100)
            except YouTubeError as e:
                download_progress.update(dl_task, completed=0)
                console.print(f"\n[red]Error Download: {str(e)}[/red]")
                raise typer.Exit(code=1)

        if cancel_requested:
            console.print("[yellow]Download dibatalkan.[/yellow]")
            raise typer.Exit(code=1)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Membaca informasi video...", total=None)
            video_info = get_video_info(downloaded_file)
            progress.update(task, completed=True)

        source_duration = video_info["duration"]
        total_loops = calculate_loops(source_duration, target_seconds)

        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style="bold cyan", justify="right")
        info_table.add_column(style="white")
        info_table.add_row("Source:", url)
        info_table.add_row("Judul:", video_info["file_name"])
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
                seamless_score = analyze_seamless(downloaded_file)
                progress.update(task, completed=True)

            score_color = "green" if seamless_score >= 85 else "yellow" if seamless_score >= 60 else "red"
            console.print(f"Seamless Loop Score: [{score_color}]{seamless_score}%[/{score_color}]")
            if seamless_score < 60:
                console.print("[yellow]Warning: Visible Loop Transition Detected[/yellow]")
            console.print()

        # Extract video ID dari URL untuk naming yang lebih singkat
        import re
        video_id_match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)', url)
        video_id = video_id_match.group(1) if video_id_match else "video"
        duration_tag = duration.replace(":", "-")

        if output:
            out = Path(output)
            if out.suffix == ".mp4":
                # Path lengkap atau nama file .mp4
                output_dir = out.parent if out.parent != Path(".") else OUTPUT_DIR
                output_filename = out.name
            elif out.is_dir() or (not out.suffix):
                # Direktori yang diberikan dari wizard
                output_dir = out
                output_filename = f"{video_id}_{duration_tag}.mp4"
            else:
                output_dir = OUTPUT_DIR
                output_filename = f"{output}.mp4"
        else:
            output_dir = OUTPUT_DIR
            output_filename = f"{video_id}_{duration_tag}.mp4"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = str(output_dir / output_filename)


        if Path(output_path).exists():
            console.print(f"[yellow]File output sudah ada: {output_filename}[/yellow]")
            overwrite = typer.confirm("Timpa file?", default=True)
            if not overwrite:
                counter = 1
                while Path(output_path).exists():
                    output_filename = f"{Path(output_filename).stem}_{counter}.mp4"
                    output_path = str(output_dir / output_filename)
                    counter += 1

        encoder_flags = get_encoder_flags()

        render_progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        )

        console.print("[bold cyan]Render Progress:[/bold cyan]")

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
                    downloaded_file, output_path, target_seconds,
                    encoder_flags, on_progress=on_progress,
                    cancel_check=lambda: cancel_requested,
                )
                render_progress.update(render_task, completed=target_seconds)
            except FFmpegError as e:
                render_progress.update(render_task, completed=0)
                console.print(f"\n[red]Error Render: {str(e)}[/red]")
                raise typer.Exit(code=1)

        if cancel_requested:
            console.print("\n[yellow]Render dibatalkan.[/yellow]")
            if Path(output_path).exists():
                Path(output_path).unlink(missing_ok=True)
            raise typer.Exit(code=1)

        result = LoopResult(
            source_file=downloaded_file,
            source_duration=source_duration,
            target_duration=target_seconds,
            total_loops=total_loops,
            encoder=get_gpu_info()["encoder"],
            output_file=output_path,
            seamless_score=seamless_score,
            gpu_name=get_gpu_name(),
            estimated_size_mb=est_size if est_size > 0 else None,
            estimated_render_time=estimate_render_time(
                source_duration, target_seconds, gpu_info["available"]
            ),
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
            f"  [bold]URL:[/bold] {url}\n"
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
    except YouTubeError as e:
        console.print(f"[red]YouTube Error: {str(e)}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"[red]Error: {str(e)}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(code=1)
