import psutil
import time
import os
import sys
from datetime import datetime
from collections import deque

try:
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.progress_bar import ProgressBar
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def color_for_percent(pct):
    if pct < 50:
        return "green"
    elif pct < 80:
        return "yellow"
    return "red"


def make_progress(percent, width=30):
    filled = int(percent / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    color = color_for_percent(percent)
    return f"[{color}]{bar}[/{color}]"


def net_speed(io_before, io_after, interval):
    sent = (io_after.bytes_sent - io_before.bytes_sent) / interval
    recv = (io_after.bytes_recv - io_before.bytes_recv) / interval
    return sent, recv


def format_bytes(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def format_uptime(seconds):
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def build_dashboard(prev_io, interval):
    cpu_pct = psutil.cpu_percent(interval=None)
    cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disks = psutil.disk_partitions()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_sec = time.time() - psutil.boot_time()
    net_io = psutil.net_io_counters()
    hostname = os.environ.get("COMPUTERNAME", "Unknown")

    sent, recv = net_speed(prev_io, net_io, interval) if prev_io else (0, 0)

    layout = Layout()

    header = Table.grid(padding=(0, 1))
    header.add_column()
    header.add_row(
        f"[bold cyan]  Hardware Monitor[/bold cyan]    "
        f"[white]{hostname}[/white]    "
        f"[dim]up {format_uptime(uptime_sec)}[/dim]    "
        f"[dim]{boot_time.strftime('%H:%M:%S')}[/dim]"
    )

    cpu_table = Table.grid(padding=(0, 1))
    cpu_table.add_column(style="bold")
    cpu_table.add_column(no_wrap=True)
    cpu_bar = make_progress(cpu_pct)
    cpu_table.add_row(
        f"[bold {color_for_percent(cpu_pct)}]CPU[/]",
        f"{cpu_bar}  [bold]{cpu_pct:.1f}%[/]"
    )
    cores_text = "  ".join(
        f"[{color_for_percent(c)}]{c}%[/]"
        for i, c in enumerate(cpu_per_core)
    )
    cpu_table.add_row("Cores", cores_text)

    ram_table = Table.grid(padding=(0, 1))
    ram_table.add_column(style="bold")
    ram_table.add_column(no_wrap=True)
    ram_bar = make_progress(ram.percent)
    used_gb = ram.used / (1024**3)
    total_gb = ram.total / (1024**3)
    ram_table.add_row(
        f"[bold {color_for_percent(ram.percent)}]RAM[/]",
        f"{ram_bar}  [bold]{ram.percent:.1f}%[/]  "
        f"[dim]{used_gb:.1f}/{total_gb:.1f} GB[/dim]"
    )

    swap_table = Table.grid(padding=(0, 1))
    swap_table.add_column(style="bold")
    swap_table.add_column(no_wrap=True)
    swap_bar = make_progress(swap.percent)
    swap_used = swap.used / (1024**3)
    swap_total = swap.total / (1024**3) if swap.total else 0
    swap_table.add_row(
        f"[bold {color_for_percent(swap.percent)}]SWP[/]",
        f"{swap_bar}  [bold]{swap.percent:.1f}%[/]  "
        f"[dim]{swap_used:.1f}/{swap_total:.1f} GB[/dim]"
    )

    disk_table = Table.grid(padding=(0, 1))
    disk_table.add_column(style="bold")
    disk_table.add_column(no_wrap=True)
    for disk in disks:
        try:
            usage = psutil.disk_usage(disk.mountpoint)
            bar = make_progress(usage.percent)
            used = usage.used / (1024**3)
            total = usage.total / (1024**3)
            disk_table.add_row(
                f"[bold {color_for_percent(usage.percent)}]{disk.device.replace('\\\\', '')}[/]",
                f"{bar}  {usage.percent:.0f}%  "
                f"[dim]{used:.1f}/{total:.1f} GB[/dim]"
            )
        except PermissionError:
            continue

    net_table = Table.grid(padding=(0, 1))
    net_table.add_column(style="bold")
    net_table.add_column(no_wrap=True)
    net_table.add_row(
        "[bold cyan]↓[/] DL", f"[dim]{format_bytes(recv)}/s[/dim]"
    )
    net_table.add_row(
        "[bold cyan]↑[/] UL", f"[dim]{format_bytes(sent)}/s[/dim]"
    )

    procs = sorted(
        psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
        key=lambda p: p.info.get("cpu_percent", 0) or 0,
        reverse=True,
    )[:8]

    proc_table = Table(
        box=box.SIMPLE,
        show_edge=False,
        padding=(0, 1),
    )
    proc_table.add_column("PID", style="dim", width=6)
    proc_table.add_column("Name", style="white", no_wrap=True)
    proc_table.add_column("CPU%", justify="right", width=6)
    proc_table.add_column("MEM%", justify="right", width=6)
    for p in procs:
        try:
            proc_table.add_row(
                str(p.info["pid"]),
                p.info["name"][:20],
                f"{p.info.get('cpu_percent', 0):.1f}",
                f"{p.info.get('memory_percent', 0):.1f}",
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    cpu_panel = Panel(cpu_table, title="[bold]Processor[/]", border_style=color_for_percent(cpu_pct))
    mem_panel = Panel(
        Table.grid().add_row(ram_table, swap_table),
        title="[bold]Memory[/]",
        border_style=color_for_percent(ram.percent),
    )
    disk_panel = Panel(disk_table, title="[bold]Disks[/]", border_style="cyan")
    net_panel = Panel(net_table, title="[bold]Network[/]", border_style="cyan")
    proc_panel = Panel(proc_table, title="[bold]Top Processes[/]", border_style="magenta")

    main = Table.grid(padding=(0, 1))
    main.add_column()
    main.add_row(cpu_panel)
    main.add_row(mem_panel)
    main.add_row(disk_panel)

    side = Table.grid(padding=(0, 1))
    side.add_column()
    side.add_row(net_panel)
    side.add_row(proc_panel)

    body = Table.grid(padding=(1, 2))
    body.add_column(no_wrap=True)
    body.add_column(no_wrap=True)
    body.add_row(main, side)

    return Panel(
        Table.grid().add_row(header, body),
        border_style="cyan",
        padding=(0, 1),
    ), net_io


def monitor_simple():
    print(" Hardware Monitor ")
    print("=" * 40)
    try:
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            bar_len = 20
            cpu_bar = "█" * int(cpu / 100 * bar_len) + "░" * (bar_len - int(cpu / 100 * bar_len))
            ram_bar = "█" * int(ram / 100 * bar_len) + "░" * (bar_len - int(ram / 100 * bar_len))
            sys.stdout.write(f"\rCPU: {cpu_bar} %{cpu:5.1f}  RAM: {ram_bar} %{ram:5.1f}")
            sys.stdout.flush()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nDone.")


def monitor_rich():
    prev_io = psutil.net_io_counters()
    interval = 2

    with Live(refresh_per_second=4, screen=True) as live:
        try:
            while True:
                dashboard, prev_io = build_dashboard(prev_io, interval)
                live.update(dashboard)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("")


def main():
    if not RICH_AVAILABLE:
        print("rich library not found. Installing...")
        os.system("pip install rich")
        print("\nRestart the script.")
        return

    try:
        monitor_rich()
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
