# performance_monitor.py
import time
import psutil
import csv
import os
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.process = psutil.Process()

    def profile(self, func, args=None, kwargs=None):
        """
        Run a function and collect:
        - runtime
        - CPU usage avg/peak
        - RAM usage avg/peak
        - disk I/O (MB)
        """
        if args is None: args = []
        if kwargs is None: kwargs = {}

        cpu_readings = []
        mem_readings = []

        # Starting measurements
        io_start = psutil.disk_io_counters()
        t0 = time.time()

        # Monitor while function runs
        result = func(*args, **kwargs)

        t1 = time.time()
        io_end = psutil.disk_io_counters()

        runtime = t1 - t0

        # Collect CPU & Memory snapshots *after function returns*
        for _ in range(5):
            cpu_readings.append(self.process.cpu_percent(interval=0.05))
            mem_readings.append(self.process.memory_percent())

        cpu_avg = sum(cpu_readings) / len(cpu_readings)
        cpu_peak = max(cpu_readings)

        mem_avg = sum(mem_readings) / len(mem_readings)
        mem_peak = max(mem_readings)

        disk_read = (io_end.read_bytes - io_start.read_bytes) / (1024 * 1024)
        disk_write = (io_end.write_bytes - io_start.write_bytes) / (1024 * 1024)

        return {
            "runtime": runtime,
            "cpu_avg": cpu_avg,
            "cpu_peak": cpu_peak,
            "mem_avg": mem_avg,
            "mem_peak": mem_peak,
            "disk_read": disk_read,
            "disk_write": disk_write,
            "result": result
        }

    def print_stats(self, label, stats):
        print(
            f"[{label}] time={stats['runtime']:.4f}s | "
            f"cpu_avg={stats['cpu_avg']:.1f}% | cpu_peak={stats['cpu_peak']:.1f}% | "
            f"mem_peak={stats['mem_peak']:.1f}% | "
            f"disk_r={stats['disk_read']:.2f}MB | disk_w={stats['disk_write']:.2f}MB"
        )

    def export_to_csv(self, filename, stats_dict_list):
        os.makedirs("logs", exist_ok=True)

        filepath = os.path.join("logs", filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "algorithm", "runtime_sec", "cpu_avg", "cpu_peak",
                "mem_peak", "disk_read_MB", "disk_write_MB"
            ])

            for row in stats_dict_list:
                writer.writerow([
                    row["algorithm"],
                    row["runtime"],
                    row["cpu_avg"],
                    row["cpu_peak"],
                    row["mem_peak"],
                    row["disk_read"],
                    row["disk_write"]
                ])

        print(f"\nPerformance CSV exported → {filepath}\n")