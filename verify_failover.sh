#!/bin/bash
set -euo pipefail

PUBLIC=http://localhost:8080/version
BLUE_CHAOS=http://localhost:8081/chaos/start?mode=error
BLUE_CHAOS_STOP=http://localhost:8081/chaos/stop
GREEN_CHAOS_STOP=http://localhost:8082/chaos/stop

# 1) Baseline check - ensure responses come from blue
echo "Baseline check (expect X-App-Pool: blue)"
for i in 1 2 3; do
  curl -s -D - -o /dev/null "$PUBLIC" | grep -i '^X-App-Pool:' || true
  sleep 0.2
done

# 2) Start chaos on Blue
echo "Starting chaos on Blue: $BLUE_CHAOS"
curl -s -X POST "$BLUE_CHAOS" || true

# 3) Poll for up to 10s and ensure responses are 200 and come from green
echo "Polling public endpoint for 10s to ensure green is serving..."
end=$((SECONDS+10))
total=0
non200=0
green_count=0
while [ $SECONDS -lt $end ]; do
  total=$((total+1))
  # single attempt with 6s timeout (curl -m ensures no client wait >10s overall)
  response=$(curl -s -w "\n%{http_code}" -m 6 "$PUBLIC" || echo -e "\n000")
  body=$(echo "$response" | sed -n '1p')
  code=$(echo "$response" | tail -n1)
  if [ "$code" != "200" ]; then
    non200=$((non200+1))
  else
    # extract header X-App-Pool via a direct HEAD like call
    pool=$(curl -s -I -m 3 "$PUBLIC" | grep -i '^X-App-Pool:' | awk '{print tolower($2)}' | tr -d '\r' || true)
    if [ "$pool" = "green" ]; then
      green_count=$((green_count+1))
    fi
  fi
  sleep 0.2
done

echo "Total requests: $total, non-200s: $non200, green responses: $green_count"
if [ $non200 -ne 0 ]; then
  echo "FAIL: some requests returned non-200"
  exit 1
fi

if [ $green_count -lt $((total * 95 / 100)) ]; then
  echo "FAIL: fewer than 95% responses came from green"
  exit 2
fi

echo "PASS: Failover succeeded and responses are from green"
# stop chaos for cleanup
curl -s -X POST "$BLUE_CHAOS_STOP" || true
curl -s -X POST "$GREEN_CHAOS_STOP" || true
