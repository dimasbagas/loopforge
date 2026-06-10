import signal
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn, Progress, TextColumn, TimeRemainingColumn, SpinnerColumn,
)
from rich.panel import Panel
from rich.table import Table

from ..utils.logger import get_logger, setup_logger
from ..utils.validator import (
    validate_file_exists, validate_video_extension, validate_ffmpeg_available,
    validate_ffprobe_available,
)
from ..services.duration_service import (
    parse_duration, calculate_loops, format_duration, DurationParseError,
)
from ..services.ffmpeg_service import (
    get_video_info, render_loop, FFmpegError,
    estimate_output_size, estimate_render_time,
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
    console.print("\n[yellow]Membatalkan batch... Silakan tunggu[/yellow]")


def batch_command(
    input_dir: str = typer.Argument(..., help="Direktori berisi file video"),
    duration: str = typer.Option("1h", "--duration", "-d",
        help="Durasi target (1h, 2h, 8h, 12h, 24h, 90m, 01:30:00)"),
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

        target_seconds = parse_duration(duration)
        input_path = Path(input_dir).resolve()

        if not input_path.exists():
            console.print(f"[red]Error: Direktori tidak ditemukan: {input_dir}[/red]")
            raise typer.Exit(code=1)
        if not input_path.is_dir():
            console.print(f"[red]Error: Path bukan direktori: {input_dir}[/red]")
            raise typer.Exit(code=1)

        video_files = []
        for ext in SUPPORTED_VIDEO_EXTENSIONS:
            video_files.extend(input_path.glob(f"*{ext}"))
            video_files.extend(input_path.glob(f"*{ext.upper()}"))

        video_files = sorted(set(video_files))

        if not video_files:
            exts = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
            console.print(f"[yellow]Tidak ada file video ditemukan di: {input_dir}[/yellow]")
            console.print(f"Format yang didukung: {exts}")
            raise typer.Exit(code=1)

        console.print()
        console.print(Panel.fit(
            "[bold cyan]LoopForge CLI[/bold cyan] - [white]Batch Process[/white]",
            border_style="cyan",
        ))
        console.print()

        gpu_info = get_gpu_info()
        encoder_flags = get_encoder_flags()

        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style="bold cyan", justify="right")
        info_table.add_column(style="white")
        info_table.add_row("Direktori:", str(input_path))
        info_table.add_row("Total File:", str(len(video_files)))
        info_table.add_row("Durasi Target:", format_duration(target_seconds))
        if gpu_info["available"]:
            info_table.add_row("GPU:", f'[green]{gpu_info["name"]}[/green]')
        info_table.add_row("Encoder:", gpu_info["encoder"])
        console.print(info_table)
        console.print()

        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        successful = 0
        failed = 0

        for i, video_file in enumerate(video_files, 1):
            if cancel_requested:
                console.print("[yellow]Batch dibatalkan oleh pengguna.[/yellow]")
                break

            console.print(f"\n[bold cyan][{i}/{len(video_files)}][/bold cyan] Memproses: {video_file.name}")

            try:
                validate_video_extension(video_file)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("[cyan]Membaca informasi video...", total=None)
                    video_info = get_video_info(str(video_file))
                    progress.update(task, completed=True)

                source_duration = video_info["duration"]
                total_loops = calculate_loops(source_duration, target_seconds)

                duration_tag = duration.replace(":", "-")
                output_filename = f"{video_file.stem}_{duration_tag}.mp4"
                output_path = str(output_dir / output_filename)

                counter = 1
                while Path(output_path).exists():
                    output_filename = f"{video_file.stem}_{duration_tag}_{counter}.mp4"
                    output_path = str(output_dir / output_filename)
                    counter += 1

                render_progress = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeRemainingColumn(),
                    console=console,
                )

                with render_progress:
                    render_task = render_progress.add_task(
                        f"[cyan]Render: ", total=target_seconds
                    )

                    def make_progress(task_id):
                        def on_progress(progress_val, current_time):
                            if cancel_requested:
                                return
                            render_progress.update(
                                task_id,
                                completed=min(current_time, target_seconds),
                            )
                        return on_progress

                    render_loop(
                        str(video_file), output_path, target_seconds,
                        encoder_flags,
                        on_progress=make_progress(render_task),
                        cancel_check=lambda: cancel_requested,
                    )
                    render_progress.update(render_task, completed=target_seconds)

                est_size = estimate_output_size(video_info, target_seconds)

                result = LoopResult(
                    source_file=str(video_file),
                    source_duration=source_duration,
                    target_duration=target_seconds,
                    total_loops=total_loops,
                    encoder=gpu_info["encoder"],
                    output_file=output_path,
                    gpu_name=get_gpu_name(),
                    estimated_size_mb=est_size if est_size > 0 else None,
                )

                generate_metadata(result, output_dir)
                results.append(result)
                successful += 1

                console.print(f"  [green]✓ Selesai: {output_filename}[/green]")

            except Exception as e:
                failed += 1
                logger.exception(f"Gagal memproses {video_file.name}")
                console.print(f"  [red]✗ Gagal: {str(e)[:100]}[/red]")

        console.print()
        console.print(Panel(
            f"[bold]Batch Result[/bold]\n\n"
            f"  Total Files: {len(video_files)}\n"
            f"  [green]Successful: {successful}[/green]\n"
            f"  [red]Failed: {failed}[/red]\n"
            f"  Output: {output_dir}",
            border_style="green" if failed == 0 else "yellow",
        ))

    except DurationParseError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Batch error")
        console.print(f"[red]Error: {str(e)}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(code=1)
