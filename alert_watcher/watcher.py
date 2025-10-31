import os
import time
import re
import requests
from collections import deque

# Environment variables
LOG_FILE = "/var/log/nginx/bluegreen-access.log"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
ERROR_RATE_THRESHOLD = float(os.environ.get("ERROR_RATE_THRESHOLD", 2))
WINDOW_SIZE = int(os.environ.get("WINDOW_SIZE", 200))
ALERT_COOLDOWN_SEC = int(os.environ.get("ALERT_COOLDOWN_SEC", 300))

# Regex to extract fields from Nginx logs
POOL_REGEX = re.compile(r'pool=(\w+)')
STATUS_REGEX = re.compile(r'upstream_status=(\d+)')

# State tracking
last_pool = None
error_window = deque(maxlen=WINDOW_SIZE)
last_failover_alert = 0
last_error_alert = 0

def send_failover(message: str):
    global last_failover_alert
    now = time.time()
    if now - last_failover_alert < ALERT_COOLDOWN_SEC:
        print(f"[DEBUG] Failover alert skipped due to cooldown: {message}", flush=True)
        return
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=3)
        print(f"[DEBUG] Failover Slack response: {resp.status_code} {resp.text}", flush=True)
        last_failover_alert = now
        print(f"[ALERT] {message}", flush=True)
    except Exception as e:
        print(f"[ERROR] Failover Slack alert failed: {e}", flush=True)

def send_error(message: str):
    global last_error_alert
    now = time.time()
    if now - last_error_alert < ALERT_COOLDOWN_SEC:
        print(f"[DEBUG] Error alert skipped due to cooldown: {message}", flush=True)
        return
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=3)
        print(f"[DEBUG] Error Slack response: {resp.status_code} {resp.text}", flush=True)
        last_error_alert = now
        print(f"[ALERT] {message}", flush=True)
    except Exception as e:
        print(f"[ERROR] Error Slack alert failed: {e}", flush=True)

def parse_line(line: str):
    pool_match = POOL_REGEX.search(line)
    status_match = STATUS_REGEX.search(line)
    pool = pool_match.group(1) if pool_match else None
    status = int(status_match.group(1)) if status_match else 0
    return pool, status

def tail_f(file_path):
    """Follow the log file like tail -f."""
    with open(file_path, "r") as f:
        try:
            f.seek(0, 2)  # Move to EOF
        except io.UnsupportedOperation:
            pass
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

def main():
    global last_pool
    for line in tail_f(LOG_FILE):
        line = line.strip()
        if not line:
            continue
        print(f"Log line: {line}", flush=True)

        pool, status = parse_line(line)
        if pool is None:
            continue

        # Detect failover
        if last_pool and pool != last_pool:
            send_failover(f":warning: Failover detected: {last_pool} → {pool}")
        last_pool = pool

        # Track error rate
        error_window.append(1 if 500 <= status < 600 else 0)
        if len(error_window) == 0:
            continue
        error_rate = sum(error_window) / len(error_window) * 100
        if error_rate > ERROR_RATE_THRESHOLD:
            send_error(f":rotating_light: High upstream error rate: {error_rate:.1f}% over last {len(error_window)} requests")

if __name__ == "__main__":
    print("Starting Nginx log watcher...", flush=True)
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL environment variable is required")
    main()
