```markdown
# 🚀 HNG Stage 2 — Blue/Green Deployment with Nginx (Auto-Failover + Manual Toggle)

## 🧭 Overview

This project implements a **Blue/Green Deployment** architecture using **Docker Compose** and **Nginx** as a reverse proxy.

Two identical Node.js services — **Blue (active)** and **Green (backup)** — are deployed behind Nginx.
Nginx handles **automatic failover** so that if Blue fails (via simulated chaos), all traffic switches to Green **with zero downtime**.

---

## 🧱 Architecture
```

```
      ┌────────────┐
      │   Client   │
      └─────┬──────┘
            │  (http://localhost:8080)
     ┌──────▼──────┐
     │    Nginx    │  ← reverse proxy + load balancer
     └──────┬──────┘
```

┌─────────────┴─────────────┐
│ │
┌──▼───┐ ┌────▼───┐
│ Blue │ 8081 │ Green │ 8082
└──────┘ └────────┘

````

---

## ⚙️ Features
- **Automatic failover:** Nginx retries to Green when Blue returns 5xx or times out.
- **Health-based detection:** Tight timeouts and fail thresholds trigger switch fast.
- **Header forwarding:** `X-App-Pool` and `X-Release-Id` headers preserved.
- **Chaos testing:** Use `/chaos/start` to simulate Blue failure.

---

## 🧩 Environment Variables
All configuration is parameterized in a `.env` file (used by Docker Compose).

```bash
# .env
BLUE_IMAGE=yimikaade/wonderful:devops-stage-two
GREEN_IMAGE=yimikaade/wonderful:devops-stage-two

ACTIVE_POOL=blue        # Controls which pool is primary by default (blue or green)

RELEASE_ID_BLUE=1.0.0
RELEASE_ID_GREEN=1.0.0

PORT=3000               # Internal app port (default: 3000)
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

You should see 3 running containers:

```
nginx
app_blue
app_green
```

### 3️⃣ Verify services

| Service            | URL                                            | Description                         |
| ------------------ | ---------------------------------------------- | ----------------------------------- |
| Nginx Public Entry | [http://localhost:8080](http://localhost:8080) | Routes requests (client entrypoint) |
| Blue Direct        | [http://localhost:8081](http://localhost:8081) | Blue service (primary)              |
| Green Direct       | [http://localhost:8082](http://localhost:8082) | Green service (backup)              |

Check version:

```bash
curl -i http://localhost:8080/version
```

Expected headers:

```
X-App-Pool: blue
X-Release-Id: <RELEASE_ID_BLUE>
```

---

## 💥 Testing Failover

Simulate a Blue failure and confirm Nginx automatically switches to Green.

```bash
# Start chaos on Blue
curl -X POST http://localhost:8081/chaos/start?mode=error

# Verify failover
./verify_failover.sh
```

Example successful output:

```
Baseline check (expect X-App-Pool: blue)
Starting chaos on Blue...
PASS: Failover succeeded and responses are from green
```

---

## 🧰 Project Structure

```
.
├── docker-compose.yml      # Orchestrates Nginx, Blue, and Green containers
├── nginx.conf.template     # Nginx config with dynamic upstreams
├── .env                    # Environment variables
├── verify_failover.sh      # Automated test script for failover
└── README.md               # Documentation
```

---

## 🧼 Cleanup

```bash
docker compose down
```

---

## 🧾 Notes

- Nginx automatically retries failed requests to the backup (Green) upstream.
- No client requests should ever fail during a Blue outage.
- You can switch the active pool manually by updating `ACTIVE_POOL` in `.env` and reloading Nginx:

  ```bash
  docker exec -it nginx nginx -s reload
  ```

---

## 🏁 Verification Criteria

✅ All traffic routed to Blue by default
✅ Nginx forwards `X-App-Pool` and `X-Release-Id` headers
✅ On Blue failure → traffic instantly switches to Green
✅ `verify_failover.sh` passes with 0 failed requests

---

## 👩‍💻 Author

**Busola Olowu**
DevOps Engineer Intern — HNG Internship Stage 2

```

```
