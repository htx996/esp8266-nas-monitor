import os
import time
import glob
from flask import Flask, request, jsonify, abort
import psutil

app = Flask(__name__)

TOKEN = os.environ.get("TOKEN", "abc123456")
DISK_PATH = os.environ.get("DISK_PATH", "/")
_last_net = None
_last_net_time = None


def percent(value):
    try:
        return int(round(float(value)))
    except Exception:
        return 0


def format_speed(bytes_per_sec):
    try:
        b = float(bytes_per_sec)
    except Exception:
        return "0KB/s"
    if b >= 1024 * 1024:
        return f"{b / 1024 / 1024:.1f}MB/s"
    if b >= 1024:
        return f"{b / 1024:.0f}KB/s"
    return f"{b:.0f}B/s"


def read_text(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return ""


def read_temp_value(path):
    try:
        raw = read_text(path)
        if not raw:
            return None
        value = float(raw)
        if value > 1000:
            value = value / 1000.0
        if 0 < value < 120:
            return value
    except Exception:
        pass
    return None


def get_temp():
    all_temps = []
    cpu_temps = []
    package_temps = []

    for base in ["/host/sys/class/hwmon", "/sys/class/hwmon"]:
        for temp_path in glob.glob(base + "/hwmon*/temp*_input"):
            label_path = temp_path.replace("_input", "_label")
            name_path = os.path.join(os.path.dirname(temp_path), "name")

            label = read_text(label_path).lower()
            name = read_text(name_path).lower()
            full_label = label + " " + name

            temp = read_temp_value(temp_path)
            if temp is None:
                continue

            all_temps.append(temp)

            if "package id 0" in full_label or "package" in full_label:
                package_temps.append(temp)
                continue

            if (
                "core" in full_label
                or "coretemp" in full_label
                or "cpu" in full_label
                or "x86_pkg_temp" in full_label
            ):
                cpu_temps.append(temp)

    if package_temps:
        return int(max(package_temps))
    if cpu_temps:
        return int(max(cpu_temps))
    if all_temps:
        return int(max(all_temps))
    return 0


def get_net_speed():
    global _last_net, _last_net_time
    now_net = psutil.net_io_counters()
    now_time = time.time()

    if _last_net is None or _last_net_time is None:
        _last_net = now_net
        _last_net_time = now_time
        return "0KB/s", "0KB/s"

    elapsed = max(now_time - _last_net_time, 0.001)
    down = (now_net.bytes_recv - _last_net.bytes_recv) / elapsed
    up = (now_net.bytes_sent - _last_net.bytes_sent) / elapsed

    _last_net = now_net
    _last_net_time = now_time

    return format_speed(down), format_speed(up)


@app.route("/status")
def status():
    token = request.args.get("token", "")
    if token != TOKEN:
        abort(401)

    cpu = percent(psutil.cpu_percent(interval=0.1))
    mem = percent(psutil.virtual_memory().percent)

    try:
        disk = percent(psutil.disk_usage(DISK_PATH).percent)
    except Exception:
        disk = 0

    temp = get_temp()
    down, up = get_net_speed()
    uptime = int(time.time() - psutil.boot_time())

    return jsonify({
        "cpu": cpu,
        "disk": disk,
        "down": down,
        "mem": mem,
        "temp": temp,
        "up": up,
        "uptime": uptime,
    })


@app.route("/")
def index():
    return "ESP8266 NAS status server is running. Use /status?token=YOUR_TOKEN"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)
