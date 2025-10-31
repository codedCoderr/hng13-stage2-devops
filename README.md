```markdown
# 🚀 HNG Stage 2 — Blue/Green Deployment with Nginx (Auto-Failover + Observability)

## 🧭 Overview

This project implements a **Blue/Green Deployment** architecture using **Docker Compose** and **Nginx** as a reverse proxy with **automatic failover** and **operational visibility**.

Two identical Node.js services — **Blue (active)** and **Green (backup)** — are deployed behind Nginx.  
Nginx handles automatic failover, and a **Python log watcher** monitors Nginx logs to post **Slack alerts** for:

- Pool failovers (Blue → Green, Green → Blue)
- Elevated upstream 5xx error rates (> configured threshold)

---

## 🧱 Architecture

```

```
  ┌────────────┐
  │   Client   │
  └─────┬──────┘
        │  (http://localhost:8080)
 ┌──────▼──────┐
 │    Nginx    │  ← reverse proxy + load balancer + structured logs
 └──────┬──────┘
```

┌─────────────┴─────────────┐
│                             │
┌──▼───┐                   ┌──▼───┐
│ Blue │ 8081              │ Green│ 8082
└──────┘                   └──────┘

````

---

## ⚙️ Features

- **Automatic failover:** Nginx retries to Green if Blue returns 5xx or times out.
- **Structured Nginx logs:** Capture `pool`, `release`, `upstream_status`, `request_time`, `upstream_response_time`, `upstream_addr`.
- **Operational visibility:** Python watcher tails logs and posts alerts to Slack.
- **Failover & error-rate detection:** Rolling window monitors upstream 5xx rates and pool flips.
- **Rate-limited Slack alerts:** Prevents alert spam via cooldown configuration.
- **Chaos testing:** Use `/chaos/start` to simulate failure scenarios.

---

## 🧩 Environment Variables

All configuration is parameterized in `.env`:

```bash
# .env
BLUE_IMAGE=yimikaade/wonderful:devops-stage-two
GREEN_IMAGE=yimikaade/wonderful:devops-stage-two

ACTIVE_POOL=blue         # Default primary pool (blue or green)

RELEASE_ID_BLUE=blue-v1.0.0
RELEASE_ID_GREEN=green-v1.0.0

PORT=3000                # Internal app port

# Operational visibility
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
ERROR_RATE_THRESHOLD=2    # % 5xx rate to trigger alert
WINDOW_SIZE=200           # Number of recent requests in rolling window
ALERT_COOLDOWN_SEC=300    # Seconds between repeated alerts
````

---

## 🐳 Running the Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/codedcoderr/hng13-stage2-devops.git
cd hng13-stage2-devops
```

### 2️⃣ Start the containers

```bash
docker compose down
docker compose up -d
```

Containers running:

```
nginx
app_blue
app_green
alert_watcher
```

### 3️⃣ Verify services

| Service            | URL                                            | Description                         |
| ------------------ | ---------------------------------------------- | ----------------------------------- |
| Nginx Public Entry | [http://localhost:8080](http://localhost:8080) | Routes requests (client entrypoint) |
| Blue Direct        | [http://localhost:8081](http://localhost:8081) | Blue service (primary)              |
| Green Direct       | [http://localhost:8082](http://localhost:8082) | Green service (backup)              |

Check version and headers:

```bash
curl -i http://localhost:8080/version
```

Expected headers:

```
X-App-Pool: blue
X-Release-Id: blue-v1.0.0
```

---

## 💥 Testing Failover & Alerts

### Simulate Blue failure

```bash
curl -X POST http://localhost:8081/chaos/start?mode=error
```

### Verify failover & watcher alerts

```bash
./verify_failover.sh
```

* Failover to Green triggers a Slack alert.
* Elevated upstream 5xx error rate triggers a Slack alert.
* Example Slack alert:

```
:warning: Failover detected: blue → green
:rotating_light: High upstream error rate: 5.2% over last 200 requests
```

---

## 🧰 Project Structure

```
.
├── docker-compose.yml      # Orchestrates Nginx, Blue, Green, and watcher
├── nginx/
│   ├── nginx.conf.template # Nginx config with dynamic upstreams
│   └── render_and_run.sh   # Entrypoint script to render upstreams
├── alert_watcher/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── watcher.py          # Python log watcher with Slack alerts
├── .env                    # Environment variables (not committed)
├── .env.example            # Template for env
├── verify_failover.sh      # Automated failover test
├── runbook.md              # Operator instructions and alert meanings
└── README.md               # Documentation
```

---

## 🧼 Cleanup

```bash
docker compose down
```

---

## 🧾 Notes

* Nginx automatically retries failed requests to the backup upstream.
* Python watcher reads Nginx logs in real-time to detect failovers and high error rates.
* Operator-friendly runbook is provided (`runbook.md`).
* Manual pool switching:

```bash
# Change ACTIVE_POOL in .env and reload Nginx
docker exec -it nginx nginx -s reload
```

---

## 🏁 Verification Criteria

✅ Traffic routes to Blue by default
✅ Nginx logs show `pool`, `release`, `upstream_status`, `request_time`, `upstream_response_time`, `upstream_addr`
✅ Failover triggers Slack alert
✅ High error-rate triggers Slack alert
✅ Alerts respect cooldowns
✅ `verify_failover.sh` passes with 0 failed requests

---

## 👩‍💻 Author

**Busola Olowu**
DevOps Engineer Intern — HNG Internship Stage 2

```
