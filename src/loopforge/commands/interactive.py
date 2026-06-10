import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from .local import local_command
from .youtube import youtube_command
from .info import info_command

console = Console()


def _ask_save_directory(default_dir: Path) -> Path:
    """Tanya user direktori penyimpanan output."""
    console.print()
    console.print(f"[dim]Direktori default: {default_dir}[/dim]")
    raw = Prompt.ask(
        "[cyan]Simpan output ke direktori[/cyan]",
        default=str(default_dir),
    )
    chosen = Path(raw.strip()).expanduser().resolve()
    try:
        chosen.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓ Output akan disimpan ke: {chosen}[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Tidak dapat membuat direktori ({e}). Menggunakan default.[/yellow]")
        chosen = default_dir
        chosen.mkdir(parents=True, exist_ok=True)
    console.print()
    return chosen


def interactive_wizard():
    # Import di sini agar tidak circular
    from ..config import OUTPUT_DIR

    console.print()
    console.print("[bold cyan]============================================================[/bold cyan]")
    console.print("[bold cyan]                 LoopForge Interactive Wizard               [/bold cyan]")
    console.print("[bold cyan]============================================================[/bold cyan]")
    console.print()

    while True:
        console.print("[bold]Pilih Opsi:[/bold]")
        console.print("  [cyan]1.[/cyan] Loop Video Lokal")
        console.print("  [cyan]2.[/cyan] Download & Loop YouTube Video")
        console.print("  [cyan]3.[/cyan] Tampilkan Info Video")
        console.print("  [cyan]4.[/cyan] Keluar")
        console.print()

        choice = Prompt.ask("[bold]Pilihan Anda[/bold]", choices=["1", "2", "3", "4"], default="1")

        if choice == "1":
            input_file = Prompt.ask("[cyan]Masukkan path video lokal (contoh: video.mp4)[/cyan]")
            # Validasi file
            file_path = Path(input_file.strip()).expanduser().resolve()
            if not file_path.exists():
                console.print(f"[red]Error: File '{input_file}' tidak ditemukan.[/red]\n")
                continue

            duration = Prompt.ask(
                "[cyan]Masukkan durasi target (contoh: 1h, 2h, 8h, 90m, atau detik)[/cyan]",
                default="1h"
            )
            fast = Confirm.ask("[cyan]Gunakan Fast Mode (copy stream tanpa re-encode)?[/cyan]", default=False)
            seamless = Confirm.ask("[cyan]Analisis seamless loop?[/cyan]", default=False)

            # Tanya direktori simpan
            save_dir = _ask_save_directory(OUTPUT_DIR)

            # Buat nama output dengan path lengkap
            stem = file_path.stem
            duration_tag = duration.replace(":", "-")
            output_path = str(save_dir / f"{stem}_{duration_tag}.mp4")

            try:
                local_command(
                    input_file=str(file_path),
                    duration=duration,
                    output=output_path,
                    fast=fast,
                    seamless=seamless,
                    debug=False
                )
            except typer.Exit:
                pass
            except Exception as e:
                console.print(f"[red]Error saat menjalankan perintah: {str(e)}[/red]")
            break

        elif choice == "2":
            url = Prompt.ask("[cyan]Masukkan URL video YouTube[/cyan]")
            # Validasi url
            import re
            patterns = [
                r"^https?://(?:www\.)?youtube\.com/watch\?v=.+",
                r"^https?://(?:www\.)?youtu\.be/.+",
                r"^https?://(?:www\.)?youtube\.com/embed/.+",
                r"^https?://(?:www\.)?youtube\.com/shorts/.+",
            ]
            if not any(re.match(p, url) for p in patterns):
                console.print("[red]Error: URL YouTube tidak valid.[/red]\n")
                continue

            duration = Prompt.ask(
                "[cyan]Masukkan durasi target (contoh: 1h, 2h, 8h, 90m, atau detik)[/cyan]",
                default="1h"
            )
            seamless = Confirm.ask("[cyan]Analisis seamless loop?[/cyan]", default=False)

            # Tanya direktori simpan
            save_dir = _ask_save_directory(OUTPUT_DIR)

            try:
                youtube_command(
                    url=url,
                    duration=duration,
                    output=str(save_dir),   # pass direktori sebagai output hint
                    seamless=seamless,
                    debug=False
                )
            except typer.Exit:
                pass
            except Exception as e:
                console.print(f"[red]Error saat menjalankan perintah: {str(e)}[/red]")
            break

        elif choice == "3":
            input_file = Prompt.ask("[cyan]Masukkan path video lokal[/cyan]")
            file_path = Path(input_file.strip()).expanduser().resolve()
            if not file_path.exists():
                console.print(f"[red]Error: File '{input_file}' tidak ditemukan.[/red]\n")
                continue

            try:
                info_command(input_file=str(file_path))
            except typer.Exit:
                pass
            except Exception as e:
                console.print(f"[red]Error saat menjalankan perintah: {str(e)}[/red]")
            console.print()

        elif choice == "4":
            console.print("[yellow]Keluar dari LoopForge.[/yellow]")
            break
