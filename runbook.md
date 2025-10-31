# CredCars Stage 2 Runbook

## Alerts

### Failover Detected

- **Meaning:** Active pool changed (Blue→Green or Green→Blue)
- **Action:** Check primary container logs, investigate why failover occurred
- **Suppression:** Maintenance mode flag or temporarily stop watcher

### High Upstream Error Rate

- **Meaning:** >2% of last 200 requests returned 5xx
- **Action:** Inspect upstream logs, check resource usage, consider toggling pools
- **Suppression:** Maintenance mode during upgrades

### Recovery

- Primary container is serving again
- Confirm via `/version` endpoint

## Verification

- Tail `/var/log/nginx/access.log` for pool and status fields
- Check Slack channel for alerts
- Chaos drills should trigger failover alerts

## Maintenance

- To temporarily disable alerts, stop the watcher container or set `ALERT_COOLDOWN_SEC` to a high value
