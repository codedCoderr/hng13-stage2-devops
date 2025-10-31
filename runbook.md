````markdown
# 🚨 HNG Stage 2 Runbook — Blue/Green Deployment with Nginx

This runbook guides operators through **failover alerts, high error-rate alerts, verification, and maintenance procedures** for Stage 2.

---

## Alerts

### 1️⃣ Failover Detected

- **Meaning:** The active pool serving traffic has changed (Blue → Green or Green → Blue), as seen in Nginx access logs.
- **Trigger:** Detected by the Python log watcher reading `X-App-Pool` headers.
- **Action:**
  1. Check Nginx logs (`/var/log/nginx/access.log`) for `pool` and `upstream_status`.
  2. Inspect the primary container logs (`app_blue` or `app_green`) for errors.
  3. Determine the root cause of failover (e.g., app crash, timeout, high 5xx rate).
- **Suppression:**
  - Enable maintenance mode (`MAINTENANCE_MODE=1`) in watcher environment, or
  - Temporarily stop the watcher container:
    ```bash
    docker stop alert_watcher
    ```

---

### 2️⃣ High Upstream Error Rate

- **Meaning:** More than the configured threshold of recent requests returned 5xx errors.
  - Default threshold: `ERROR_RATE_THRESHOLD=2%`
  - Rolling window size: `WINDOW_SIZE=200` requests
- **Trigger:** Python watcher calculates error rate from Nginx logs.
- **Action:**
  1. Inspect upstream app logs for 5xx errors.
  2. Check container health, resource usage, and network connectivity.
  3. Consider toggling the active pool if errors persist.
- **Suppression:** Enable maintenance mode during planned upgrades or chaos testing.

---

### 3️⃣ Recovery

- **Meaning:** The primary container is serving traffic again.
- **Verification:**
  - Check `/version` endpoint:
    ```bash
    curl -i http://localhost:8080/version
    ```
  - Ensure `X-App-Pool` corresponds to the intended active pool.
- **Optional:** Slack may post recovery notifications if configured.

---

## Verification Procedures

- **Nginx Logs:** Tail the access log to confirm structured fields are present for each request:
  ```bash
  docker-compose exec nginx tail -f /var/log/nginx/access.log
  ```
````

Required fields:

- `pool` (active pool serving request)

- `release` (app release ID)

- `upstream_status` (status code from upstream)

- `request_time` (total request time)

- `upstream_response_time` (response time from upstream)

- `upstream_addr` (upstream IP:port)

- **Slack Alerts:** Confirm failover and high error-rate alerts are posted.

- **Chaos Drills:** Run:

  ```bash
  curl -X POST http://localhost:8081/chaos/start?mode=error
  ./verify_failover.sh
  ```

  Expected outcomes:

  - Failover to backup pool triggers Slack alert.
  - High 5xx rate triggers Slack alert.

---

## Maintenance

- **Suppress alerts temporarily:**

  - Stop watcher container:

    ```bash
    docker stop alert_watcher
    ```

  - Or increase cooldown interval in `.env`:

    ```bash
    ALERT_COOLDOWN_SEC=3600
    ```

- **Planned pool switch:**

  1. Update `ACTIVE_POOL` in `.env`
  2. Reload Nginx:

     ```bash
     docker exec -it nginx nginx -s reload
     ```

  3. Re-enable watcher if it was stopped for maintenance.

---

## Notes

- Alerts are **rate-limited** via `ALERT_COOLDOWN_SEC` to avoid spam.
- Watcher only reads logs — no direct coupling to request paths.
- All configuration is environment-variable driven via `.env`.

---

## Reference

| Alert Type               | Indicator                                                   | Recommended Action                          |
| ------------------------ | ----------------------------------------------------------- | ------------------------------------------- |
| Failover Detected        | Pool change in Nginx logs (`pool` field)                    | Investigate primary container, check logs   |
| High Upstream Error Rate | > `ERROR_RATE_THRESHOLD` 5xx in last `WINDOW_SIZE` requests | Inspect upstream logs, consider pool toggle |
| Recovery                 | Primary pool serving traffic again                          | Confirm via `/version` endpoint             |

```

```
