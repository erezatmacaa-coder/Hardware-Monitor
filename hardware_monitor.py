import psutil
import time
import os
import sys
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from rich.table import Table
    from rich.panel import Panel
    from rich.console import Console
    from rich import box
    from rich.columns import Columns
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False


def color_for(pct):
    return "green" if pct < 50 else "yellow" if pct < 80 else "red"


def bar(pct, w=20):
    c = color_for(pct)
    fill = int(pct / 100 * w)
    return f"[{c}]{'#' * fill}{'-' * (w - fill)}[/{c}]"


def fmt_bytes(b):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} PB"


def fmt_uptime(s):
    d, r = divmod(int(s), 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def get_wmi_info():
    try:
        import subprocess, json
        r = subprocess.run(
            ["powershell", "-Command", """
                Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, MaxClockSpeed | ConvertTo-Json;
                Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json
            """],
            capture_output=True, text=True, timeout=5
        )
        parts = r.stdout.strip().split("}\n{")
        cpu_data, gpu_data = {}, {}
        if len(parts) >= 1:
            try:
                cpu_data = json.loads(parts[0])
            except:
                pass
        if len(parts) >= 2:
            try:
                gpu_data = json.loads("{" + parts[1] + "}")
            except:
                try:
                    gpu_data = json.loads(parts[1])
                except:
                    pass
        cpu_name = cpu_data.get("Name", "") if isinstance(cpu_data, dict) else (cpu_data[0]["Name"] if isinstance(cpu_data, list) and cpu_data else "")
        gpu_name = gpu_data.get("Name", "") if isinstance(gpu_data, dict) else (gpu_data[0]["Name"] if isinstance(gpu_data, list) and gpu_data else "")
        return cpu_name, gpu_name
    except:
        return "", ""


CPU_NAME, GPU_NAME = get_wmi_info()


def build_dashboard(prev):
    cpu_pct = psutil.cpu_percent(interval=None)
    cpu_cores = psutil.cpu_percent(interval=None, percpu=True)
    cpu_freq = psutil.cpu_freq()
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disks = psutil.disk_partitions()
    net_io = psutil.net_io_counters()
    net_per_nic = psutil.net_io_counters(pernic=True)
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime_s = time.time() - psutil.boot_time()
    host = os.environ.get("COMPUTERNAME", "?")

    sent, recv = (0, 0)
    if prev.get("net"):
        dt = time.time() - prev["time"]
        if dt > 0:
            sent = (net_io.bytes_sent - prev["net"].bytes_sent) / dt
            recv = (net_io.bytes_recv - prev["net"].bytes_recv) / dt

    disk_io = {}
    if prev.get("disk_io"):
        try:
            cur = psutil.disk_io_counters(perdisk=True)
            dt = time.time() - prev["time"]
            for d, c in cur.items():
                p = prev["disk_io"].get(d)
                if p and dt > 0:
                    disk_io[d] = {
                        "r": (c.read_bytes - p.read_bytes) / dt,
                        "w": (c.write_bytes - p.write_bytes) / dt,
                    }
        except:
            pass

    bat = psutil.sensors_battery()
    now = datetime.now()

    # CPU Panel
    cpu_t = Table.grid(padding=(0, 1))
    cpu_t.add_column(style="bold")
    cpu_t.add_column(no_wrap=True)
    cpu_t.add_row(f"[bold {color_for(cpu_pct)}]CPU[/]", f"{bar(cpu_pct, 20)}  [bold]{cpu_pct:.1f}%[/]")
    cores_line = " ".join(f"[{color_for(c)}]{c:>3.0f}[/]" for c in cpu_cores[:10])
    if len(cpu_cores) > 10:
        cores_line += f" [dim]+{len(cpu_cores)-10}[/]"
    cpu_t.add_row("Cores", cores_line)
    info_parts = []
    if CPU_NAME:
        short = CPU_NAME.replace("(R)", "").replace("(TM)", "").replace("  ", " ").strip()
        if len(short) > 50:
            short = short[:50] + "..."
        info_parts.append(f"[dim]{short}[/]")
    if cpu_freq:
        info_parts.append(f"[dim]{cpu_freq.current:.0f} MHz[/]")
    if info_parts:
        cpu_t.add_row("", "  ".join(info_parts))

    # Memory
    mem_t = Table.grid(padding=(0, 1))
    mem_t.add_column(style="bold")
    mem_t.add_column(no_wrap=True)
    used_gb = ram.used / 1e9
    total_gb = ram.total / 1e9
    mem_t.add_row(f"[bold {color_for(ram.percent)}]RAM[/]", f"{bar(ram.percent, 20)}  [bold]{ram.percent:.1f}%[/]  [dim]{used_gb:.1f}/{total_gb:.1f} GB[/]")
    avail_gb = ram.available / 1e9
    mem_t.add_row("", f"[dim]avail {avail_gb:.1f} GB[/]")

    swp_t = Table.grid(padding=(0, 1))
    swp_t.add_column(style="bold")
    swp_t.add_column(no_wrap=True)
    if swap.total:
        swp_t.add_row(f"[bold {color_for(swap.percent)}]SWP[/]", f"{bar(swap.percent, 20)}  [bold]{swap.percent:.1f}%[/]  [dim]{swap.used/1e9:.1f}/{swap.total/1e9:.1f} GB[/]")
    else:
        swp_t.add_row("[dim]SWP[/]", "[dim]no swap[/]")

    # Disks
    disk_t = Table.grid(padding=(0, 1))
    disk_t.add_column(style="bold")
    disk_t.add_column(no_wrap=True)
    for d in disks:
        try:
            u = psutil.disk_usage(d.mountpoint)
            label = d.device.replace("\\", "")
            io = disk_io.get(d.device.replace("\\", "").lower(), {})
            io_part = ""
            if io:
                io_part = f"  [dim]R:{fmt_bytes(io.get('r',0))}/s W:{fmt_bytes(io.get('w',0))}/s[/]"
            disk_t.add_row(f"[bold {color_for(u.percent)}]{label}[/]", f"{bar(u.percent, 20)}  {u.percent:.0f}%  [dim]{u.used/1e9:.0f}/{u.total/1e9:.0f} GB[/]{io_part}")
        except:
            continue

    # Network
    net_t = Table.grid(padding=(0, 2))
    net_t.add_column(style="bold")
    net_t.add_column(no_wrap=True)
    net_t.add_row("[bold cyan]DL[/]", f"[dim]{fmt_bytes(recv)}/s[/]")
    net_t.add_row("[bold cyan]UL[/]", f"[dim]{fmt_bytes(sent)}/s[/]")

    active_nics = {k: v for k, v in net_per_nic.items() if v.bytes_sent or v.bytes_recv}
    for name, nic in sorted(active_nics.items())[:3]:
        ns, nr = 0, 0
        pn = prev.get("nic", {}).get(name)
        if pn:
            dt = time.time() - prev["time"]
            if dt > 0:
                nr = (nic.bytes_recv - pn.bytes_recv) / dt
                ns = (nic.bytes_sent - pn.bytes_sent) / dt
        if nr or ns:
            net_t.add_row(f"[dim]{name[:12]}[/]", f"[dim]{fmt_bytes(nr)}/s / {fmt_bytes(ns)}/s[/]")

    # Processes
    procs = sorted(
        psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]),
        key=lambda p: p.info.get("cpu_percent", 0) or 0,
        reverse=True,
    )[:10]

    pt = Table.grid(padding=(0, 1))
    pt.add_column(style="dim", width=6)
    pt.add_column(style="white", width=22, no_wrap=True)
    pt.add_column(justify="right", width=6)
    pt.add_column(justify="right", width=6)
    pt.add_column(style="dim", width=4)
    pt.add_row("[bold]PID[/]", "[bold]Name[/]", "[bold]CPU%[/]", "[bold]MEM%[/]", "[bold]St[/]")
    for p in procs:
        try:
            st = (p.info.get("status") or "")[:4]
            pt.add_row(str(p.info["pid"]), (p.info["name"] or "")[:22], f"{p.info.get('cpu_percent', 0):.1f}", f"{p.info.get('memory_percent', 0):.1f}", st)
        except:
            continue

    # System info
    sys_t = Table.grid(padding=(0, 2))
    sys_t.add_column(no_wrap=True)
    line = f"[bold cyan]/// Hardware Monitor[/]    [white]{host}[/]"
    if bat:
        icon = "+" if bat.power_plugged else "-"
        line += f"    [yellow]BAT {icon} {bat.percent:.0f}%[/]"
    line += f"    [dim]up {fmt_uptime(uptime_s)}[/]    [dim]{now.strftime('%H:%M:%S')}[/]"
    if GPU_NAME:
        gpu_short = GPU_NAME.split(" (")[0][:40]
        line += f"    [dim]{gpu_short}[/]"
    sys_t.add_row(line)

    # Assemble
    cpu_panel = Panel(cpu_t, title="[bold]Processor[/]", border_style=color_for(cpu_pct))
    mem_grid = Table.grid()
    mem_grid.add_row(mem_t)
    mem_grid.add_row(swp_t)
    mem_panel = Panel(mem_grid, title="[bold]Memory[/]", border_style=color_for(ram.percent))
    disk_panel = Panel(disk_t, title="[bold]Disks[/] (usage + I/O)", border_style="cyan")
    net_panel = Panel(net_t, title="[bold]Network[/]", border_style="cyan")
    proc_panel = Panel(pt, title="[bold]Top Processes[/]", border_style="magenta")

    left = Table.grid(padding=(0, 1))
    left.add_column()
    left.add_row(cpu_panel)
    left.add_row(mem_panel)
    left.add_row(disk_panel)

    right = Table.grid(padding=(0, 1))
    right.add_column()
    right.add_row(net_panel)
    right.add_row(proc_panel)

    body = Table.grid(padding=(1, 2))
    body.add_column(no_wrap=True)
    body.add_column(no_wrap=True)
    body.add_row(left, right)

    outer = Table.grid()
    outer.add_column()
    outer.add_row(sys_t)
    outer.add_row(body)

    snap = {"net": net_io, "nic": net_per_nic, "disk_io": psutil.disk_io_counters(perdisk=True), "time": time.time()}
    return Panel(outer, border_style="cyan", padding=(0, 1)), snap


def main():
    if not RICH_AVAILABLE:
        print("Installing rich...")
        os.system("pip install rich")
        print("Done. Restart.")
        return
    prev = {"time": time.time()}
    try:
        while True:
            dash, prev = build_dashboard(prev)
            console.clear()
            console.print(dash)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
